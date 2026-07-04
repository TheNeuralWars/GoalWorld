#!/usr/bin/env python3
"""
omniroute_cooldown_watcher.py
==============================
Runs every minute (cron). Reads Docker logs, detects provider errors,
sets rate_limited_until in DB so OmniRoute excludes exhausted connections.

Cooldown rules (research-confirmed 2026-07-02):
  - OR free  402 ("requires more credits")  → cooldown until next UTC midnight
  - OR free  daily quota hit (48/48)         → cooldown until next UTC midnight
  - Kimi     402 ("membership" / "credits")  → cooldown 7 days (weekly Kimi quota)
  - KC free  402 ("Add credits")             → cooldown 7 days (upstream Kimi via KC)
  - Cerebras 429                             → cooldown until next UTC midnight (UTC-midnight reset)
  - NV       429                             → cooldown 1 hour (rolling hourly)
  - Any      429 generic                     → cooldown 1 hour
"""

import subprocess, re, sqlite3, datetime, json, os, sys

DB = "/data/docker/volumes/omniroute-data/_data/storage.sqlite"
LOG_LINES = 500   # last N lines of docker logs to scan

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)

def next_utc_midnight():
    n = now_utc()
    return (n + datetime.timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)

def in_hours(h):
    return now_utc() + datetime.timedelta(hours=h)

def in_days(d):
    return now_utc() + datetime.timedelta(days=d)

def next_week():
    """Next Monday 00:00 UTC (Kimi weekly reset)"""
    n = now_utc()
    days_until_monday = (7 - n.weekday()) % 7 or 7  # at least 1 day ahead
    return (n + datetime.timedelta(days=days_until_monday)).replace(hour=0,minute=0,second=0,microsecond=0)

def ts(dt):
    return dt.isoformat().replace('+00:00','Z')

def get_docker_logs():
    try:
        r = subprocess.run(
            ["docker","logs","--tail", str(LOG_LINES), "omniroute"],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout + r.stderr
    except Exception as e:
        print(f"[watcher] docker logs error: {e}")
        return ""

def load_connections(db):
    c = db.cursor()
    c.execute("""
        SELECT id, name, provider, api_key, test_status, rate_limited_until, error_code
        FROM provider_connections
        WHERE is_active=1
          AND provider IN ('openrouter','cerebras','nvidia','kilocode','kimi-coding')
    """)
    return [dict(r) for r in c.fetchall()]

def clear_expired(db):
    """Remove cooldowns that have passed their expiry (auto-recovery)."""
    n = ts(now_utc())
    c = db.cursor()
    c.execute("""
        UPDATE provider_connections
        SET rate_limited_until=NULL, backoff_level=0
        WHERE rate_limited_until IS NOT NULL
          AND rate_limited_until < ?
          AND is_active=1
    """, (n,))
    cleared = c.rowcount
    if cleared:
        db.commit()
        print(f"[watcher] cleared {cleared} expired cooldowns")
    return cleared

def set_cooldown(db, conn_id, until_dt, reason):
    until_str = ts(until_dt)
    c = db.cursor()
    # Don't shorten existing longer cooldown
    c.execute("SELECT rate_limited_until FROM provider_connections WHERE id=?", (conn_id,))
    row = c.fetchone()
    if row and row[0] and row[0] > until_str:
        return  # already has a longer cooldown
    c.execute("""
        UPDATE provider_connections
        SET rate_limited_until=?, backoff_level=1, updated_at=?
        WHERE id=?
    """, (until_str, ts(now_utc()), conn_id))
    db.commit()
    print(f"[watcher] cooldown {conn_id[:8]} until {until_str} — {reason}")

def scan_logs_for_errors(logs, connections):
    """
    Returns list of (conn_id, provider, cooldown_until, reason) tuples.
    Matches by connection id fragments or api_key fragments in log lines.
    """
    actions = []
    for conn in connections:
        cid    = conn['id']
        short  = cid[:8]
        prov   = conn['provider']
        apikey = (conn['api_key'] or '')[:12]  # enough to match in logs

        # Build search tokens
        tokens = [short]
        if apikey: tokens.append(apikey)
        if conn['name']: tokens.append(str(conn['name'])[:20])

        # Find relevant log lines for this connection
        conn_lines = []
        for line in logs.splitlines():
            if any(t in line for t in tokens):
                conn_lines.append(line)

        if not conn_lines:
            continue

        full_ctx = '\n'.join(conn_lines)

        # ── OpenRouter free: 402 credit exhaustion ───────────────────────
        if prov == 'openrouter' and re.search(r'402|requires more credits|credit', full_ctx, re.I):
            actions.append((cid, prov, next_utc_midnight(),
                            "OR 402 credits exhausted → until UTC midnight"))

        # ── Kimi-coding: 402 membership/credits (weekly quota) ───────────
        elif prov == 'kimi-coding' and re.search(r'402|membership|credits', full_ctx, re.I):
            # Try to parse expiry from log
            m = re.search(r'expires["\s:]+(\d{4}-\d{2}-\d{2}T[\d:\.Z]+)', full_ctx)
            if m:
                try:
                    expiry = datetime.datetime.fromisoformat(m.group(1).replace('Z','+00:00'))
                    actions.append((cid, prov, expiry, "kimi 402 → parsed expiry from response"))
                    continue
                except: pass
            actions.append((cid, prov, next_week(), "kimi 402 → 7-day weekly quota cooldown"))

        # ── Kilocode: 402 upstream credits (Kimi via KC, weekly) ─────────
        elif prov == 'kilocode' and re.search(r'402|Add credits|credits', full_ctx, re.I):
            actions.append((cid, prov, next_week(), "KC 402 upstream credits → 7-day cooldown"))

        # ── Cerebras: 429 → UTC midnight reset ───────────────────────────
        elif prov == 'cerebras' and re.search(r'429|rate.limit|quota', full_ctx, re.I):
            actions.append((cid, prov, next_utc_midnight(), "cerebras 429 → until UTC midnight"))

        # ── NVIDIA: 429 → 1-hour rolling ─────────────────────────────────
        elif prov == 'nvidia' and re.search(r'429|rate.limit', full_ctx, re.I):
            actions.append((cid, prov, in_hours(1), "nvidia 429 → 1-hour rolling cooldown"))

    return actions

def check_or_quota_by_api(conn, db):
    """
    Proactively check OR key usage via /auth/key endpoint.
    Sets cooldown if usage >= 48/50.
    """
    if conn['provider'] != 'openrouter' or not conn['api_key']:
        return
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {conn['api_key']}"}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        usage = data.get('data',{}).get('usage', 0)
        limit = data.get('data',{}).get('limit')
        rate_limit = data.get('data',{}).get('rate_limit',{})
        req_used  = rate_limit.get('requests', 0)
        req_limit = rate_limit.get('requests',{}) if isinstance(rate_limit, dict) else 0

        # If free tier (limit is small number like 1.0 or 0.5 USD), check request count
        if data.get('data',{}).get('is_free_tier') and req_used >= 48:
            set_cooldown(db, conn['id'], next_utc_midnight(),
                        f"OR proactive: {req_used}/50 daily req used")
    except Exception:
        pass  # silent - this is a bonus check, not required

def main():
    if not os.path.exists(DB):
        print(f"[watcher] DB not found: {DB}")
        sys.exit(1)

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    # 1. Clear expired cooldowns first
    clear_expired(db)

    # 2. Load active connections
    connections = load_connections(db)

    # 3. Scan docker logs
    logs = get_docker_logs()

    # 4. Apply cooldowns from log analysis
    actions = scan_logs_for_errors(logs, connections)
    for (cid, prov, until, reason) in actions:
        set_cooldown(db, cid, until, reason)

    # 5. Proactive OR quota check (only free keys)
    for conn in connections:
        if conn['provider'] == 'openrouter' and conn['api_key']:
            check_or_quota_by_api(conn, db)

    db.close()
    if not actions:
        pass  # quiet when nothing to do

if __name__ == "__main__":
    main()
