# OmniRoute combo live-verified rebuild — 2026-08-10

## Problem
7/8 combos had collapsed to `github/gpt-4o` (stale). `context-1m` was not frontier. Catalog still listed EOL NVIDIA DeepSeek V4 flash/pro (410 Gone since 2026-08-07).

## Actions
1. Backup: `/tmp/storage_combo_backup_20260810_191749.sqlite`
2. Live inventory of providers + `/v1/models` + HTTP probes
3. Full rebuild of 8 combos with **live-verified** models only
4. `docker restart omniroute`
5. Hermes fleet sync: `ops/hermes/sync-omniroute-hermes-context.py` (parameters→1M, coding→256k, writing→400k, tooling→409k)
6. Purge provider/models caches across Hermes homes

## Live smoke (stream=false) — PASS 8/8
| Combo | Winner (actual) |
|-------|-----------------|
| coding | codestral/codestral-latest |
| parameters | codex/gpt-5.5 |
| context-1m | morph/morph-dsv4flash (fallback; nvidia ultra also top-weight) |
| writing | morph/morph-qwen35-397b |
| tooling | morph/morph-dsv4flash |
| small | morph/morph-qwen36-27b |
| infalible | morph/morph-dsv4flash |
| moa-fast | codestral/codestral-latest |

## Tier-1 design (unique models, multi-key expanded)
- **parameters**: nemotron-3-ultra → gpt-5.5 → agy gemini-3.1-pro-high → gemini-3.1-pro → grok-4.20 → claude-opus-4.7 → morph-qwen35-397b → mistral-large → minimax-m3 …
- **coding**: codestral → devstral-medium → gpt-5.3-codex → minimax-m3 → morph-dsv4flash → kiro qwen3-coder-next → deepseek-v4-flash-0731 …
- **context-1m** (≥1M only): nemotron-3-ultra → minimax-m3 → morph-dsv4flash → agy/gemini pro → grok-4.20 → claude-opus-4.7 …
- **writing**: gpt-5.5 → claude-opus-4.7 → agy claude-sonnet-4-6 → mistral-large → kiro sonnet-4.5 …
- **tooling**: gpt-5.4-mini → codestral → devstral → deepseek-v4-flash-0731 → morph …
- **small / moa-fast / infalible**: codestral + ministral + nemotron-nano + flash-lite + morph + CF gpt-oss-120b + OR free nemotron

## Explicitly removed / skipped
- gpt-4o / gpt-4o-mini
- nvidia `deepseek-v4-flash` + `deepseek-v4-pro` (EOL 410)
- bazaarlink `llama-4-scout` (unknown model 400)
- groq (broken affinity / 404)
- cerebras (unavailable cooldown)
- bynara (no active credentials)
- github current IDs unsupported on this keyset
- xiaomi-mimo unsupported model IDs on live probe

## Counts
parameters 127 | coding 138 | context-1m 81 | writing 117 | tooling 138 | small 138 | infalible 145 | moa-fast 122

## Follow-ups
- Re-probe groq/cerebras/bynara when accounts recover; fold back in
- Prefer demoting providers that consistently lose affinity so winners stay frontier (nvidia ultra for context-1m/parameters)
- Optional: nightly combo health probe that auto-drops 410/404 models
