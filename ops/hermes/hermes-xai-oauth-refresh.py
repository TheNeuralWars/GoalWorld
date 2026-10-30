#!/usr/bin/env python3
"""Proactive xAI Grok OAuth refresh — SINGLETON root only.

xAI rotates refresh_token on every refresh. Refreshing N profile copies of
the same grant revokes the login (invalid_grant). Only refresh the fleet
root auth.json; profiles inherit via Hermes write-through (#43589).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _refresh_one(hermes_home: Path, agent_root: Path, label: str) -> int:
    if not agent_root.is_dir():
        print(f"ERROR: hermes-agent not found under {agent_root}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(agent_root))
    os.environ["HERMES_HOME"] = str(hermes_home)

    try:
        from hermes_cli.auth import AuthError, resolve_xai_oauth_runtime_credentials
    except ImportError as exc:
        print(f"ERROR [{label}]: cannot import hermes_cli.auth: {exc}", file=sys.stderr)
        return 2

    auth_path = hermes_home / "auth.json"
    if not auth_path.is_file():
        print(f"SKIP [{label}]: no auth.json at {auth_path}")
        return 0

    try:
        creds = resolve_xai_oauth_runtime_credentials(
            force_refresh=False,
            refresh_if_expiring=True,
        )
        token = str(creds.get("api_key", "") or "")
        preview = f"{token[:8]}…" if len(token) > 8 else "(empty)"
        print(f"OK [{label}] xai-oauth refreshed or still valid (token preview {preview})")
        return 0
    except AuthError as exc:
        print(f"FAIL [{label}] xai-oauth: [{exc.code}] {exc}", file=sys.stderr)
        if getattr(exc, "relogin_required", False):
            print(
                "Re-login: hermes auth add xai-oauth --no-browser "
                "(with ssh -L 56121:127.0.0.1:56121 on Mac if remote)",
                file=sys.stderr,
            )
        return 1
    except Exception as exc:
        print(f"FAIL [{label}] xai-oauth: {exc}", file=sys.stderr)
        return 1


def _fleet_root() -> Path:
    env = os.environ.get("HERMES_HOME", "").strip()
    if env:
        p = Path(env)
        if p.name and p.parent.name == "profiles":
            return p.parent.parent
        return p
    return Path.home() / ".hermes"


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh xAI OAuth in Hermes auth.json")
    parser.add_argument(
        "--all-agent-profiles",
        action="store_true",
        help="Refresh the SINGLETON fleet root only (profiles inherit; do not loop).",
    )
    args = parser.parse_args()

    agent_root = Path("/data/ubuntu/.hermes/hermes-agent")
    if not agent_root.is_dir():
        agent_root = Path.home() / ".hermes" / "hermes-agent"

    # Always refresh the fleet root. --all-agent-profiles used to loop every
    # profile and burn the rotating refresh_token. That flag is now an alias
    # for "refresh the shared grant once".
    if args.all_agent_profiles:
        root = Path(os.environ.get("HERMES_HOME_ROOT", "/data/hermes-home"))
        if not (root / "auth.json").is_file():
            root = _fleet_root()
        print(f"SINGLETON refresh at {root} (profiles inherit; not looped)")
        return _refresh_one(root, agent_root, "fleet-root")

    profile = os.environ.get("HERMES_PROFILE", "").strip()
    hermes_home = _fleet_root()
    if profile and profile not in ("default", ""):
        # Explicit single-profile request: still redirect to fleet root so a
        # cron that sets HERMES_PROFILE cannot rotate a shadow copy.
        print(f"NOTE: ignoring HERMES_PROFILE={profile}; xai-oauth is a root singleton")
    return _refresh_one(hermes_home, agent_root, profile or "fleet-root")


if __name__ == "__main__":
    raise SystemExit(main())
