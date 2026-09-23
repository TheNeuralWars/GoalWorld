#!/usr/bin/env python3
"""Apply GoalWorld-balanced OmniRoute compression + stability settings."""
from __future__ import annotations

import json
import sqlite3
import urllib.request
from pathlib import Path

import yaml

HERMES_CONFIG = Path("/data/hermes-home/config.yaml")
OR_BASE = "http://127.0.0.1:20128"
DB = "/data/docker/volumes/omniroute-data/_data/storage.sqlite"

COMBO_OVERRIDES = {
    "tooling": "stacked",
    "coding": "stacked",
    "small": "lite",
    "moa-fast": "lite",
    "infalible": "lite",
    "context-1m": "off",
    "parameters": "off",
    "writing": "off",
}


def _key() -> str:
    return yaml.safe_load(HERMES_CONFIG.read_text())["providers"]["omniroute"]["api_key"]


def _get_json(path: str) -> dict:
    req = urllib.request.Request(
        f"{OR_BASE}{path}",
        headers={"Authorization": f"Bearer {_key()}"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def _put_json(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{OR_BASE}{path}",
        data=data,
        method="PUT",
        headers={
            "Authorization": f"Bearer {_key()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def apply_compression() -> dict:
    cfg = _get_json("/api/settings/compression")
    cfg["enabled"] = True
    cfg["defaultMode"] = "off"
    cfg["autoTriggerMode"] = "lite"
    cfg["autoTriggerTokens"] = 56_000
    cfg["preserveSystemPrompt"] = True
    cfg["comboOverrides"] = dict(COMBO_OVERRIDES)
    cfg["stackedPipeline"] = [{"engine": "rtk", "intensity": "standard"}]
    cfg["cavemanOutputMode"] = {
        "enabled": False,
        "intensity": "lite",
        "autoClarity": True,
    }
    cave = cfg.get("cavemanConfig") or {}
    cave.update({"enabled": True, "intensity": "lite", "compressRoles": ["user"]})
    cfg["cavemanConfig"] = cave
    cfg["rtkConfig"] = {
        "enabled": True,
        "intensity": "standard",
        "applyToToolResults": True,
        "applyToCodeBlocks": False,
        "applyToAssistantMessages": False,
        "maxLinesPerResult": 120,
        "maxCharsPerResult": 12_000,
    }
    engines = cfg.get("engines") or {}
    engines.setdefault("rtk", {})["enabled"] = True
    engines["rtk"]["level"] = "standard"
    engines.setdefault("caveman", {})["enabled"] = True
    engines["caveman"]["level"] = "lite"
    engines.setdefault("lite", {})["enabled"] = True
    cfg["engines"] = engines
    return _put_json("/api/settings/compression", cfg)


def apply_debug_off() -> bool:
    s = _get_json("/api/settings")
    s["debugMode"] = False
    out = _put_json("/api/settings", s)
    return out.get("debugMode") is False


def widen_hermes_allowlist() -> None:
    conn = sqlite3.connect(DB)
    conn.execute(
        "UPDATE api_keys SET allowed_models = ? WHERE name = 'hermes'",
        (json.dumps([]),),
    )
    conn.commit()
    conn.close()


def main() -> int:
    comp = apply_compression()
    print("compression defaultMode", comp.get("defaultMode"), "auto", comp.get("autoTriggerTokens"))
    print("comboOverrides", comp.get("comboOverrides"))
    print("cavemanOutputMode", comp.get("cavemanOutputMode"))
    print("debugMode off", apply_debug_off())
    widen_hermes_allowlist()
    print("hermes allowed_models -> []")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())