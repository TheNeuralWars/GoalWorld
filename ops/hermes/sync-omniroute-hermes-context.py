#!/usr/bin/env python3
"""Align OmniRoute combo context windows + MoA presets across all Hermes profiles."""
from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

import yaml

HERMES_ROOT = Path(os.environ.get("HERMES_HOME", "/data/hermes-home"))
OR_BASE = "http://127.0.0.1:20128/v1"

# Hermes compaction / get_model_context_length for omniroute combo model IDs
COMBO_CONTEXT: dict[str, int] = {
    "context-1m": 1_048_576,
    "parameters": 1_048_576,
    "coding": 256_000,
    "writing": 400_000,
    "tooling": 409_600,
    "small": 131_072,
    "infalible": 131_072,
    "moa-fast": 131_072,
    "bomba": 1_048_576,
}

MOA_PRESET_PATCHES: dict[str, dict] = {
    "MAX": {
        "fanout": "user_turn",
        "reference_max_tokens": 600,
    },
    "PRO": {
        "fanout": "user_turn",
        "reference_max_tokens": 600,
    },
}


def _homes() -> list[Path]:
    homes = [HERMES_ROOT]
    prof = HERMES_ROOT / "profiles"
    if prof.is_dir():
        for d in sorted(prof.iterdir()):
            if d.is_dir() and (d / "config.yaml").is_file():
                homes.append(d)
    return homes


def _write_context_cache(home: Path) -> None:
    cache_path = home / "context_length_cache.yaml"
    existing: dict = {}
    if cache_path.is_file():
        try:
            existing = yaml.safe_load(cache_path.read_text()) or {}
        except Exception:
            existing = {}
    lengths = dict(existing.get("context_lengths") or {})
    for combo, ctx in COMBO_CONTEXT.items():
        key = f"{combo}@{OR_BASE.rstrip('/')}"
        lengths[key] = ctx
    cache_path.write_text(
        yaml.dump({"context_lengths": lengths}, default_flow_style=False, sort_keys=True),
        encoding="utf-8",
    )


def _patch_config(path: Path) -> list[str]:
    cfg = yaml.safe_load(path.read_text()) or {}
    notes: list[str] = []

    prov = cfg.setdefault("providers", {}).setdefault("omniroute", {})
    if not isinstance(prov, dict):
        return notes
    models = prov.setdefault("models", {})
    if not isinstance(models, dict):
        models = {}
        prov["models"] = models
    for combo, ctx in COMBO_CONTEXT.items():
        slot = models.setdefault(combo, {})
        if not isinstance(slot, dict):
            slot = {}
            models[combo] = slot
        slot["context_length"] = ctx
    notes.append("omniroute.models context_length")

    moa = cfg.get("moa") or {}
    presets = moa.get("presets") or {}
    if isinstance(presets, dict):
        for pname, patch in MOA_PRESET_PATCHES.items():
            if pname not in presets or not isinstance(presets[pname], dict):
                continue
            presets[pname].update(patch)
            if presets[pname].pop("max_tokens", None) == 4096:
                notes.append(f"moa.{pname} dropped max_tokens cap")
            notes.append(f"moa.{pname} fanout/reference_max_tokens")

    model = cfg.get("model") or {}
    if (
        isinstance(model, dict)
        and str(model.get("provider") or "").lower() == "moa"
        and str(model.get("default") or "") in ("MAX", "PRO")
    ):
        model["context_length"] = COMBO_CONTEXT["context-1m"]
        notes.append("model.context_length=1M (moa MAX/PRO)")

    # Delegation / auxiliary often hit context-1m directly
    for key in ("delegation",):
        block = cfg.get(key)
        if isinstance(block, dict) and block.get("model") == "context-1m":
            block["context_length"] = COMBO_CONTEXT["context-1m"]
            notes.append(f"{key}.context_length=1M")

    path.write_text(yaml.dump(cfg, default_flow_style=False, sort_keys=False), encoding="utf-8")
    return notes


def main() -> int:
    for home in _homes():
        label = home.name if home != HERMES_ROOT else "root"
        _write_context_cache(home)
        cfg_path = home / "config.yaml"
        if cfg_path.is_file():
            notes = _patch_config(cfg_path)
            print(f"[{label}] context_length_cache.yaml + {', '.join(notes) or 'cache only'}")
        else:
            print(f"[{label}] context_length_cache.yaml only")
    print("Done. Restart gateway or /new sessions to pick up compaction limits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())