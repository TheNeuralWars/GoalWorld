#!/usr/bin/env python3
"""Seed Super Grok picker caches + Nous auth on every Hermes profile.

xAI OAuth refresh tokens rotate on every refresh (invalid_grant if reused).
The live Super Grok grant is therefore a SINGLETON on root auth.json
(/data/hermes-home/auth.json, hardlinked to ~/.hermes/auth.json).

Specialist profiles must NOT carry providers.xai-oauth or
credential_pool.xai-oauth — Hermes already falls back to root and
write-throughs rotated tokens there (#43589 / #74339). Copying the
refresh_token into 9 files is what revoked Nico's login.

Nous grants are still merged into each profile (separate IdP).
"""
from __future__ import annotations

import fcntl
import json
import os
import shutil
import sys
from datetime import datetime, timezone

HERMES_ROOT = os.environ.get("HERMES_HOME_ROOT", "/data/hermes-home")
AGENT_ROOT = "/data/ubuntu/.hermes/hermes-agent"
FAR_FUTURE_AT = 2098485230.0  # ~2036 — resist cache eviction
LOCK_PATH = os.path.join(HERMES_ROOT, "logs", "sync-xai-oauth-fleet.lock")
PROFILES = [
    "creative",
    "dev",
    "hermes-ceo",
    "money",
    "product",
    "qa",
    "research",
    "social",
    "trader",
    "default",
]


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    os.replace(tmp, path)


def refresh_root_xai_cache() -> list[str]:
    os.chdir(AGENT_ROOT)
    if AGENT_ROOT not in sys.path:
        sys.path.insert(0, AGENT_ROOT)
    os.environ["HERMES_HOME"] = HERMES_ROOT
    from hermes_cli.config import load_config
    from hermes_cli.model_switch import list_authenticated_providers

    cfg = load_config()
    rows = list_authenticated_providers(
        current_provider="xai-oauth",
        current_model="grok-composer-2.5-fast",
        user_providers=cfg.get("providers") or {},
        custom_providers=cfg.get("custom_providers") or [],
        refresh=True,
    )
    for r in rows:
        if r.get("slug") == "xai-oauth":
            return list(r.get("models") or [])
    return []


def _oauth_tokens(auth: dict) -> dict:
    px = (auth.get("providers") or {}).get("xai-oauth") or {}
    toks = px.get("tokens") or {}
    return toks if isinstance(toks, dict) else {}


def _oauth_healthy(auth: dict) -> bool:
    toks = _oauth_tokens(auth)
    if not (toks.get("access_token") and toks.get("refresh_token")):
        return False
    if (auth.get("providers") or {}).get("xai-oauth", {}).get("last_auth_error"):
        # stale error with live tokens is still usable; only reject if tokens gone
        pass
    pool = (auth.get("credential_pool") or {}).get("xai-oauth") or []
    if not isinstance(pool, list):
        return bool(toks.get("access_token") and toks.get("refresh_token"))
    for cred in pool:
        if not isinstance(cred, dict):
            continue
        kind = cred.get("auth_type") or cred.get("type")
        if kind and kind != "oauth":
            continue
        if cred.get("last_status") == "exhausted":
            continue
        if cred.get("access_token") and cred.get("refresh_token"):
            return True
    # providers.tokens alone is enough (pool may be empty after singleton restore)
    return bool(toks.get("access_token") and toks.get("refresh_token"))


def _last_refresh_ts(auth: dict) -> str:
    px = (auth.get("providers") or {}).get("xai-oauth") or {}
    return str(px.get("last_refresh") or "")


def _pick_newest_healthy_auth(root: str) -> tuple[str, dict]:
    """Newest last_refresh wins. Never prefer a hardcoded profile."""
    candidates = [os.path.join(root, "auth.json")] + [
        os.path.join(root, "profiles", p, "auth.json") for p in PROFILES
    ]
    best: tuple[str, dict, str] | None = None
    for path in candidates:
        if not os.path.isfile(path):
            continue
        data = _load_json(path)
        if not _oauth_healthy(data):
            continue
        stamp = _last_refresh_ts(data)
        if best is None or stamp > best[2]:
            best = (path, data, stamp)
    if not best:
        raise SystemExit("no healthy xai-oauth auth.json found (root or any profile)")
    return best[0], best[1]


def install_xai_oauth_on_root(root_auth_path: str, src_auth: dict, src_path: str) -> bool:
    """Write the live grant to root only. Never touch specialist files here."""
    if os.path.abspath(root_auth_path) == os.path.abspath(src_path):
        # already on root — just clear stale last_auth_error if tokens live
        dst = _load_json(root_auth_path)
        px = (dst.get("providers") or {}).get("xai-oauth")
        if isinstance(px, dict) and px.get("last_auth_error"):
            toks = px.get("tokens") or {}
            if toks.get("access_token") and toks.get("refresh_token"):
                px.pop("last_auth_error", None)
                dst["providers"]["xai-oauth"] = px
                _save_json(root_auth_path, dst)
                return True
        return False
    dst = _load_json(root_auth_path) if os.path.isfile(root_auth_path) else {}
    src_prov = (src_auth.get("providers") or {}).get("xai-oauth")
    if not src_prov:
        return False
    dst.setdefault("providers", {})
    new_prov = json.loads(json.dumps(src_prov))
    if isinstance(new_prov, dict):
        new_prov.pop("last_auth_error", None)
    dst["providers"]["xai-oauth"] = new_prov
    dst.setdefault("credential_pool", {})
    src_pool = (src_auth.get("credential_pool") or {}).get("xai-oauth") or []
    healthy = []
    if isinstance(src_pool, list):
        for cred in src_pool:
            if not isinstance(cred, dict):
                continue
            if cred.get("last_status") == "exhausted":
                continue
            if cred.get("access_token") and cred.get("refresh_token"):
                healthy.append(json.loads(json.dumps(cred)))
    if healthy:
        dst["credential_pool"]["xai-oauth"] = healthy
    _save_json(root_auth_path, dst)
    return True


def strip_profile_xai_oauth_shadow(auth_path: str) -> bool:
    """Remove shadowing xai-oauth so the profile inherits + write-throughs root."""
    if not os.path.isfile(auth_path):
        return False
    dst = _load_json(auth_path)
    changed = False
    providers = dst.get("providers")
    if isinstance(providers, dict) and "xai-oauth" in providers:
        providers.pop("xai-oauth", None)
        changed = True
    if "xai-oauth" in dst:
        dst.pop("xai-oauth", None)
        changed = True
    pool = dst.get("credential_pool")
    if isinstance(pool, dict) and "xai-oauth" in pool:
        pool.pop("xai-oauth", None)
        changed = True
    if changed:
        _save_json(auth_path, dst)
    return changed


def _nous_healthy(auth: dict) -> bool:
    px = (auth.get("providers") or {}).get("nous") or {}
    if not (px.get("access_token") and px.get("refresh_token")):
        return False
    pool = (auth.get("credential_pool") or {}).get("nous") or []
    if not isinstance(pool, list):
        return False
    for cred in pool:
        kind = cred.get("auth_type") or cred.get("type")
        if kind == "oauth" and cred.get("last_status") != "exhausted" and cred.get("access_token"):
            return True
    return False


def _pick_healthy_nous_auth(root: str) -> tuple[str, dict]:
    candidates = [
        os.path.join(root, "auth.json"),
        os.path.join(root, "profiles", "hermes-ceo", "auth.json"),
        os.path.join(root, "profiles", "research", "auth.json"),
    ]
    for path in candidates:
        if not os.path.isfile(path):
            continue
        data = _load_json(path)
        if _nous_healthy(data):
            return path, data
    raise SystemExit("no healthy nous auth.json found (root/ceo/research)")


def merge_nous_auth(dst_auth_path: str, src_auth: dict) -> bool:
    if not os.path.isfile(dst_auth_path):
        return False
    dst = _load_json(dst_auth_path)
    src_prov = (src_auth.get("providers") or {}).get("nous")
    if not src_prov:
        return False
    dst.setdefault("providers", {})
    new_prov = json.loads(json.dumps(src_prov))
    if isinstance(new_prov, dict):
        new_prov.pop("last_auth_error", None)
    dst["providers"]["nous"] = new_prov
    if isinstance(src_auth.get("nous"), dict):
        top = json.loads(json.dumps(src_auth["nous"]))
        top.pop("last_auth_error", None)
        dst["nous"] = top
    dst.setdefault("credential_pool", {})
    src_pool = (src_auth.get("credential_pool") or {}).get("nous")
    if isinstance(src_pool, list):
        dst["credential_pool"]["nous"] = json.loads(json.dumps(src_pool))
    _save_json(dst_auth_path, dst)
    return True


def patch_nous_cache(cache_path: str, src_nous_entry: dict) -> None:
    cache: dict = {}
    if os.path.isfile(cache_path):
        cache = _load_json(cache_path)
    entry = json.loads(json.dumps(src_nous_entry))
    entry["at"] = FAR_FUTURE_AT
    cache["nous"] = entry
    _save_json(cache_path, cache)


def patch_provider_cache(cache_path: str, models: list[str], also_omniroute_from: str | None) -> None:
    cache: dict = {}
    if os.path.isfile(cache_path):
        cache = _load_json(cache_path)
    if also_omniroute_from and os.path.isfile(also_omniroute_from):
        root_cache = _load_json(also_omniroute_from)
        if "omniroute" in root_cache:
            cache["omniroute"] = root_cache["omniroute"]
        if "custom:omniroute" in root_cache:
            cache["custom:omniroute"] = root_cache["custom:omniroute"]
    fp = "|".join(sorted(models))
    cache["xai-oauth"] = {
        "fp": fp[:64],
        "at": FAR_FUTURE_AT,
        "models": models,
    }
    _save_json(cache_path, cache)


def main() -> None:
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    lock_f = open(LOCK_PATH, "w")
    try:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("another sync-xai-oauth-fleet.py is running")

    root = HERMES_ROOT
    models = refresh_root_xai_cache()
    if not models:
        raise SystemExit("xai-oauth refresh returned 0 models — check root auth.json")
    if "grok-composer-2.5-fast" not in models:
        models = ["grok-composer-2.5-fast"] + [m for m in models if m != "grok-composer-2.5-fast"]
    print(f"ROOT xai-oauth models ({len(models)}):", ", ".join(models))

    src_path, src_auth = _pick_newest_healthy_auth(root)
    print(f"XAI AUTH SOURCE (singleton): {src_path} last_refresh={_last_refresh_ts(src_auth)}")
    root_auth = os.path.join(root, "auth.json")
    if install_xai_oauth_on_root(root_auth, src_auth, src_path):
        print(f"ROOT xai-oauth installed from {src_path}")
    else:
        print("ROOT xai-oauth already canonical")

    nous_src_path, nous_src_auth = _pick_healthy_nous_auth(root)
    print(f"NOUS AUTH SOURCE: {nous_src_path}")
    root_pmc = os.path.join(root, "provider_models_cache.json")
    root_mdc = os.path.join(root, "models_dev_cache.json")
    nous_entry = None
    for cand in [root_pmc] + [
        os.path.join(root, "profiles", p, "provider_models_cache.json") for p in PROFILES
    ]:
        if not os.path.isfile(cand):
            continue
        cache = _load_json(cand)
        entry = cache.get("nous") if isinstance(cache, dict) else None
        if isinstance(entry, dict) and entry.get("models"):
            nous_entry = entry
            print(f"NOUS CATALOG SOURCE: {cand} ({len(entry['models'])} models)")
            break
    if not nous_entry:
        raise SystemExit("no nous catalog in root or profile provider_models_cache.json")

    patch_provider_cache(root_pmc, models, also_omniroute_from=None)
    patch_nous_cache(root_pmc, nous_entry)

    targets = [os.path.join(root, "profiles", p) for p in PROFILES]
    for home in targets:
        if not os.path.isdir(home):
            continue
        name = os.path.basename(home)
        pmc = os.path.join(home, "provider_models_cache.json")
        mdc = os.path.join(home, "models_dev_cache.json")
        patch_provider_cache(pmc, models, also_omniroute_from=root_pmc)
        patch_nous_cache(pmc, nous_entry)
        if os.path.isfile(root_mdc) and os.path.abspath(root_mdc) != os.path.abspath(mdc):
            shutil.copy2(root_mdc, mdc)
        auth_path = os.path.join(home, "auth.json")
        bits = []
        if strip_profile_xai_oauth_shadow(auth_path):
            bits.append("xai-oauth-unshadowed")
        if os.path.isfile(auth_path) and os.path.abspath(auth_path) != os.path.abspath(nous_src_path):
            if merge_nous_auth(auth_path, nous_src_auth):
                bits.append("nous")
        print(
            f"OK {name}: caches"
            + (f" + {','.join(bits)}" if bits else "")
        )

    print(
        "Done. Super Grok grant lives ONLY on root auth.json; "
        "profiles inherit it. Re-open /model in each profile (or new chat)."
    )
    print(f"sync_at={datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
