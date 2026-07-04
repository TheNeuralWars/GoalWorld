"""
omniroute_smart_cooldown.py
===========================
Smart cooldown watcher + OpenRouter free-tier quota manager for OmniRoute.

Logic per provider:
  - OpenRouter free:   50 req/day, resets at 00:00 UTC daily
                       → cooldown until next 00:00 UTC when daily usage >= 48 (safety margin 2)
  - OpenRouter paid:   error_code 402 → cooldown 24h
  - Kilocode:          error_code 402 → cooldown 24h (monthly quota, manual action needed)
  - Nvidia NIM:        429 → backoff 1h, 402 → 24h
  - Kimi-coding:       429 → backoff 1h, credits_exhausted → 24h

Runs every minute via cron. Parses docker logs for 402/429/credits signals,
then updates rate_limited_until in SQLite so OmniRoute skips exhausted keys.
"""

import sqlite3
import json
import subprocess
import datetime
import re
import sys
from omniroute_auto_recovery import main as run_auto_recovery

DB = "/data/docker/volumes/omniroute-data/_data/storage.sqlite"
LOG_WINDOW = "2m"   # scan last 2 min of docker logs each run

# ─── helpers ───────────────────────────────────────────────────────────────

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

def next_utc_midnight():
    """Returns the next 00:00:00 UTC timestamp (ISO string)."""
    now = utcnow()
    tomorrow = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return tomorrow.isoformat().replace("+00:00", "Z")

def cooldown_ts(hours):
    ts = utcnow() + datetime.timedelta(hours=hours)
    return ts.isoformat().replace("+00:00", "Z")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def set_cooldown(conn_id, until_ts, status="rate_limited", name="?"):
    c = db()
    cursor = c.cursor()
    cursor.execute(
        "UPDATE provider_connections SET test_status=?, rate_limited_until=? WHERE id=?",
        (status, until_ts, conn_id)
    )
    c.commit()
    c.close()
    log(f"COOLDOWN [{name}] → {status} until {until_ts}")

def log(msg):
    ts = utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)

# ─── 1. OpenRouter free-tier quota management ──────────────────────────────

def manage_openrouter_free_quota():
    """
    For each free-tier OR key: if usage_daily >= 48 (2 reqs safety margin
    before the 50 req/day hard cap), set cooldown until next 00:00 UTC.
    Requires the OR API key stored in provider_connections.api_key.
    """
    import urllib.request

    c = db()
    cursor = c.cursor()
    cursor.execute("""
        SELECT id, name, api_key, test_status, rate_limited_until
        FROM provider_connections
        WHERE provider='openrouter' AND is_active=1
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    c.close()

    midnight = next_utc_midnight()
    now_iso = utcnow().isoformat().replace("+00:00", "Z")

    for row in rows:
        key = row.get("api_key") or ""
        if not key:
            continue

        # If already cooling down, skip
        rl = row.get("rate_limited_until") or ""
        if rl and rl > now_iso:
            continue

        # Query OR API for current key usage
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/auth/key")
            req.add_header("Authorization", f"Bearer {key}")
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.load(r).get("data", {})

            is_free = data.get("is_free_tier", False)
            usage_daily = data.get("usage_daily", 0) or 0
            limit = data.get("limit")      # None = no paid limit set
            limit_remaining = data.get("limit_remaining")

            name = row.get("name") or row["id"][:8]

            if is_free:
                # Free tier: 50 req/day hard cap → cooldown at 48
                if usage_daily >= 48:
                    set_cooldown(row["id"], midnight, "rate_limited", f"{name}(free)")
                    log(f"  Free key {name}: usage_daily={usage_daily}/50 → cooldown until midnight UTC")
                else:
                    log(f"  Free key {name}: usage_daily={usage_daily}/50 — OK")
            else:
                # Paid tier: check credit balance via limit_remaining
                if limit_remaining is not None and limit_remaining < 500:
                    # Under $0.50 remaining → 24h cooldown
                    set_cooldown(row["id"], cooldown_ts(24), "credits_exhausted", f"{name}(paid)")
                    log(f"  Paid key {name}: limit_remaining={limit_remaining} < 500 → 24h cooldown")
                elif row.get("error_code") in ("402.0", "402") or row.get("test_status") == "credits_exhausted":
                    set_cooldown(row["id"], cooldown_ts(24), "credits_exhausted", f"{name}(paid-402)")

        except Exception as e:
            log(f"  OR API check failed for {row['id'][:8]}: {e}")

# ─── 2. Docker logs scan → 402/429 → cooldown ─────────────────────────────

def scan_logs_and_cooldown():
    """
    Parse OmniRoute docker logs for 402/429 errors tied to connection IDs.
    Apply appropriate cooldowns.
    """
    try:
        res = subprocess.run(
            ["docker", "logs", "--since", LOG_WINDOW, "omniroute"],
            capture_output=True, text=True, timeout=10
        )
        logs = res.stdout + res.stderr
    except Exception as e:
        log(f"docker logs error: {e}")
        return

    if not logs.strip():
        return

    c = db()
    cursor = c.cursor()
    cursor.execute("SELECT id, name, provider, test_status, rate_limited_until, error_code FROM provider_connections WHERE is_active=1")
    all_conns = [dict(r) for r in cursor.fetchall()]
    c.close()

    now_iso = utcnow().isoformat().replace("+00:00", "Z")

    for conn in all_conns:
        short = conn["id"][:8]
        name = conn.get("name") or short
        provider = conn["provider"]

        # Skip if already cooling down
        rl = conn.get("rate_limited_until") or ""
        if rl and rl > now_iso:
            continue

        # Only scan logs for providers that return HTTP errors we care about
        if provider not in ("openrouter", "nvidia", "kilocode", "kimi-coding"):
            continue

        # Check if this connection appears in logs near a 402/429
        # Use tight window: error must appear on the SAME log line as the connection ID
        if short not in logs and conn["id"] not in logs:
            continue

        # Split into lines for per-line matching (avoids cross-line false positives)
        for line in logs.splitlines():
            if short not in line and conn["id"] not in line:
                continue
            # 402 = credit exhaustion — only on error-tagged lines
            if ("402" in line or "credits_exhausted" in line or "insufficient credits" in line.lower() or
                    "requires more credits" in line.lower()):
                set_cooldown(conn["id"], cooldown_ts(24), "credits_exhausted", f"{provider}/{name}")
                break
            # 429 = temporary rate limit
            if "429" in line or "rate_limit" in line.lower() or "too many requests" in line.lower():
                set_cooldown(conn["id"], cooldown_ts(1), "rate_limited", f"{provider}/{name}")
                break

# ─── 3. Kilocode: check 402 in DB state ───────────────────────────────────

def manage_kilocode():
    c = db()
    cursor = c.cursor()
    cursor.execute("""
        SELECT id, name, test_status, error_code, rate_limited_until
        FROM provider_connections WHERE provider='kilocode' AND is_active=1
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    c.close()
    now_iso = utcnow().isoformat().replace("+00:00", "Z")
    for r in rows:
        rl = r.get("rate_limited_until") or ""
        if rl and rl > now_iso:
            continue
        if r.get("error_code") in ("402.0", "402") or r.get("test_status") == "credits_exhausted":
            # KC monthly quota — cooldown 24h, needs manual re-check
            set_cooldown(r["id"], cooldown_ts(24), "credits_exhausted", f"kilocode/{r.get('name','?')}")

# ─── 4. Auto-clear expired cooldowns ──────────────────────────────────────

def clear_expired_cooldowns():
    """Re-activate connections whose rate_limited_until has passed."""
    c = db()
    cursor = c.cursor()
    now_iso = utcnow().isoformat().replace("+00:00", "Z")
    cursor.execute("""
        UPDATE provider_connections
        SET test_status='active', rate_limited_until=NULL, error_code=NULL
        WHERE rate_limited_until IS NOT NULL
          AND rate_limited_until < ?
          AND test_status IN ('rate_limited')
    """, (now_iso,))
    cleared = cursor.rowcount
    c.commit()
    c.close()
    if cleared > 0:
        log(f"Auto-cleared {cleared} expired rate_limited cooldowns → status=active")

# ─── main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log("=== OmniRoute Smart Cooldown Watcher ===")
    clear_expired_cooldowns()
    manage_openrouter_free_quota()
    manage_kilocode()
    scan_logs_and_cooldown()
    run_auto_recovery()
    log("Done.")
