#!/usr/bin/env python3
"""
goalworld omniroute — local management CLI for the OmniRoute LLM router.

Gives Nico/agent a clean, local interface to:
  - list providers + their connection health (and which are unreachable)
  - list the 7 combos and their model tiers
  - show / rewrite a combo's model tiers (e.g. force 100% free)
  - live-test any combo or model through the router
  - test an individual provider connection

All reads/writes go to the local OmniRoute SQLite (via sudo) + the local REST API.
No SSH, no manual SQLite editing.

Usage:
  goalworld omniroute providers [--dead-only]
  goalworld omniroute combos
  goalworld omniroute combo show <name>
  goalworld omniroute combo set-free <name> [--dry-run]
  goalworld omniroute test <combo|model> [--prompt "..."] [--img] [--timeout SEC]
  goalworld omniroute key test <provider> [--connection-id ID]
"""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import urllib.request

# ── paths / creds ────────────────────────────────────────────────────────
DB = "/data/docker/volumes/omniroute-data/_data/storage.sqlite"
OR_BASE = "http://127.0.0.1:20128"
CONFIG_YAML = "/data/hermes-home/config.yaml"
REGISTRY = ["coding", "context-1m", "writing", "parameters", "small", "infalible", "tooling"]
# Combos that often cold-start >30s (large / multi-hop routing)
HEAVY_COMBOS = frozenset({"context-1m", "parameters"})
DEFAULT_TEST_TIMEOUT = 120
HEAVY_TEST_TIMEOUT = 300

# Providers with ZERO active connections → listed as unreachable
# (discovered live; this is just a fallback if DB query fails)
UNREACHABLE_PROVIDERS = {"kilocode", "mimocode", "opencode", "xiaomi-mimo",
                         "zenmux", "openai-compatible-chat-ee6f3065-8993-4e38-87d2-842e74869e6a"}

# Models known to be paid / not free-tier (used by combo set-free)
PAID_HINT = ("deepseek-v4-pro", "nemotron-3-ultra-550b", "nemotron-3-ultra",
             "claude-opus-4.7", "claude-opus-4.8", "gemini-3-pro",
             "mistral-large-3-675b", "mistral-medium-3-instruct", "mistral-medium-3.1",
             "kimi-k2.6:", "gpt-5", "grok-4")


def get_or_key():
    import yaml
    return yaml.safe_load(open(CONFIG_YAML))["providers"]["omniroute"]["api_key"]


def sudo_db():
    """Open the SQLite read/write via sudo python helper."""
    return DB


def db_rows(query, args=()):
    out = subprocess.run(
        ["sudo", "python3", "-c",
         "import sqlite3,sys,json\n"
         "db=sqlite3.connect(sys.argv[1]); db.row_factory=sqlite3.Row\n"
         "cur=db.cursor(); cur.execute(sys.argv[2], sys.argv[3:] if len(sys.argv)>3 else [])\n"
         "print(json.dumps([dict(r) for r in cur.fetchall()]))\n",
         DB, query, *[str(a) for a in args]],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"DB error: {out.stderr}")
    return json.loads(out.stdout)


def db_exec(query, args=()):
    out = subprocess.run(
        ["sudo", "python3", "-c",
         "import sqlite3,sys\n"
         "db=sqlite3.connect(sys.argv[1]); db.execute(sys.argv[2], sys.argv[3:] if len(sys.argv)>3 else [])\n"
         "db.commit(); print('OK')\n",
         DB, query, *[str(a) for a in args]],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"DB exec error: {out.stderr}")
    return out.stdout.strip()


def api_get(path):
    req = urllib.request.Request(f"{OR_BASE}{path}",
                                 headers={"Authorization": f"Bearer {get_or_key()}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def api_post(path, body):
    req = urllib.request.Request(f"{OR_BASE}{path}",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {get_or_key()}",
                                          "Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# ── commands ───────────────────────────────────────────────────────────────
def cmd_providers(args):
    rows = db_rows("""SELECT provider, COUNT(*) t,
                      SUM(CASE WHEN test_status='active' THEN 1 ELSE 0 END) a
                      FROM provider_connections GROUP BY provider ORDER BY t DESC""")
    print(f"{'PROVIDER':16s} {'active/total':12s} STATUS")
    print("-" * 50)
    for r in rows:
        dead = r["a"] == 0
        if args.dead_only and not dead:
            continue
        flag = "DEAD" if dead else "ok"
        print(f"{r['provider']:16s} {r['a']:>2}/{r['t']:<3}        {flag}")


def cmd_combos(args):
    rows = db_rows("SELECT name, data FROM combos ORDER BY sort_order")
    print(f"{'COMBO':14s} {'models':6s} strategy  tier1 (highest weight)")
    print("-" * 70)
    for r in rows:
        d = json.loads(r["data"]) if isinstance(r["data"], str) else r["data"]
        models = sorted(d.get("models", []), key=lambda m: -m.get("weight", 0))
        t1 = models[0] if models else {}
        print(f"{r['name']:14s} {len(models):<6} {d.get('strategy',''):9s} "
              f"{t1.get('providerId',''):12s} {t1.get('model','')}")


def cmd_combo_show(args):
    row = db_rows("SELECT data FROM combos WHERE name=?", (args.name,))
    if not row:
        print(f"combo '{args.name}' not found. Registry: {REGISTRY}")
        return 1
    d = json.loads(row[0]["data"]) if isinstance(row[0]["data"], str) else row[0]["data"]
    print(f"=== {args.name} (strategy={d.get('strategy')}, {len(d.get('models',[]))} models) ===")
    for m in sorted(d.get("models", []), key=lambda m: -m.get("weight", 0)):
        cfg = m.get("config", {})
        paid = not is_free(m.get("model", ""), m.get("providerId", ""))
        tag = " [PAID?]" if paid else ""
        print(f"  w={m.get('weight'):3} {m.get('providerId'):14s} {m.get('model'):45s} "
              f"ctx={cfg.get('contextLimit')}{tag}")


def is_free(model_str, provider_id):
    """Heuristic: free if ends with :free or -free (checked FIRST), else reject known paid hints."""
    if model_str.endswith(":free") or model_str.endswith("-free"):
        return True
    if any(h in model_str for h in PAID_HINT):
        return False
    # optimistic: any remaining model is treated as free (review PAID? tags manually)
    return True


def cmd_combo_set_free(args):
    row = db_rows("SELECT id, data FROM combos WHERE name=?", (args.name,))
    if not row:
        print(f"combo '{args.name}' not found. Registry: {REGISTRY}")
        return 1
    combo_id, raw = row[0]["id"], row[0]["data"]
    d = json.loads(raw) if isinstance(raw, str) else raw
    models = d.get("models", [])
    removed, kept = [], []
    for m in models:
        if is_free(m.get("model", ""), m.get("providerId", "")):
            kept.append(m)
        else:
            removed.append(f"{m.get('providerId')}/{m.get('model')}")
    if not removed:
        print(f"[set-free] {args.name}: already all-free. Nothing to do.")
        return 0
    d["models"] = kept
    d["version"] = d.get("version", 1) + 1
    new_raw = json.dumps(d)
    if args.dry_run:
        print(f"[DRY-RUN] would remove {len(removed)} paid tiers from {args.name}:")
        for x in removed:
            print(f"   - {x}")
        print(f"   keeps {len(kept)} free tiers.")
        return 0
    db_exec("UPDATE combos SET data=? WHERE id=?", (new_raw, combo_id))
    print(f"[set-free] {args.name}: removed {len(removed)} paid tiers, kept {len(kept)} free.")
    for x in removed:
        print(f"   - {x}")


def _probe(model, prompt, with_image, timeout):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300, "stream": False}
    if with_image:
        png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGNgYGAAAAAEAAH2FzhVAAAAAElFTkSuQmCC"
        body["messages"][0]["content"] = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png}"}},
            {"type": "text", "content": prompt}]
    req = urllib.request.Request(f"{OR_BASE}/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {get_or_key()}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            or_prov = r.headers.get("x-omniroute-provider") or ""
            or_model = r.headers.get("x-omniroute-model") or ""
            d = json.load(r)
        if "choices" not in d:
            return f"ERR: {str(d)[:120]}"
        ch = d["choices"][0]
        route = f" [{or_prov}/{or_model}]" if or_prov else ""
        return f"OK -> {d.get('model')}{route} | {(ch['message'].get('content') or '')[:50]}"
    except urllib.error.HTTPError as e:
        return f"HTTP{e.code}: {e.read().decode()[:120]}"
    except Exception as e:
        return f"ERR: {str(e)[:120]}"


def cmd_test(args):
    model = args.combo
    prompt = args.prompt or "Reply with exactly the word OK"
    if args.timeout is not None:
        timeout = args.timeout
    elif model in HEAVY_COMBOS:
        timeout = HEAVY_TEST_TIMEOUT
    else:
        timeout = DEFAULT_TEST_TIMEOUT
    print(f"[test] {model} (timeout={timeout}s): {_probe(model, prompt, args.img, timeout)}")


def cmd_key_test(args):
    # find a connection for provider
    rows = db_rows("SELECT id, name, provider FROM provider_connections WHERE provider=? LIMIT 1",
                   (args.provider,))
    if not rows:
        print(f"no connection for provider {args.provider}")
        return 1
    conn = rows[0]
    cid = args.connection_id or conn["id"]
    body = {"model": args.model or "ping", "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 10, "stream": False}
    req = urllib.request.Request(f"{OR_BASE}/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {get_or_key()}",
                                          "Content-Type": "application/json",
                                          "X-OmniRoute-Connection": cid})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
        print(f"[{args.provider}/{cid[:8]}] OK -> {d.get('model')}")
    except Exception as e:
        print(f"[{args.provider}/{cid[:8]}] FAIL: {str(e)[:150]}")


def main():
    p = argparse.ArgumentParser(prog="goalworld omniroute")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("providers"); sp.add_argument("--dead-only", action="store_true")
    sp.set_defaults(func=cmd_providers)

    sp = sub.add_parser("combos"); sp.set_defaults(func=cmd_combos)

    sp = sub.add_parser("combo"); sc = sp.add_subparsers(dest="sub")
    sshow = sc.add_parser("show"); sshow.add_argument("name"); sshow.set_defaults(func=cmd_combo_show)
    sfree = sc.add_parser("set-free"); sfree.add_argument("name")
    sfree.add_argument("--dry-run", action="store_true"); sfree.set_defaults(func=cmd_combo_set_free)

    st = sub.add_parser("test"); st.add_argument("combo"); st.add_argument("--prompt")
    st.add_argument("--img", action="store_true")
    st.add_argument("--timeout", type=int, default=None,
                    help=f"HTTP timeout seconds (default {HEAVY_TEST_TIMEOUT} for context-1m/parameters, else {DEFAULT_TEST_TIMEOUT})")
    st.set_defaults(func=cmd_test)

    sk = sub.add_parser("key"); skc = sk.add_subparsers(dest="sub")
    skt = skc.add_parser("test"); skt.add_argument("provider"); skt.add_argument("--connection-id")
    skt.add_argument("--model"); skt.set_defaults(func=cmd_key_test)

    args = p.parse_args()
    if not args.cmd:
        p.print_help(); return 1
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
