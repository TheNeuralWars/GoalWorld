# OmniRoute — preset GoalWorld-balanced (2026-07-13)

Applied after user confirmation (`confirmado`).

## Script (re-apply)

```bash
python3 /data/apps/GoalWorld/ops/hermes/apply-omniroute-goalworld-balanced.py
```

## Compression

| Scope | Mode |
|--------|------|
| Global default | `off` |
| Auto-trigger | `lite` @ **56 000** tokens |
| `tooling`, `coding` | `stacked` (pipeline **RTK standard only**, no caveman full in stack) |
| `small`, `moa-fast`, `infalible` | `lite` |
| `context-1m`, `parameters`, `writing` | `off` (reasoning / prose quality) |
| Caveman **output** | **disabled** |

## Stability

- API key **`hermes`**: `allowed_models` → `[]` (resolved upstream models not blocked).
- **`debugMode`**: set `false` via dashboard or PATCH if full settings PUT returns 400.

## Caveman note

Input compression on tool combos (RTK) does **not** enable caveman output mode; reasoning combos stay uncompressed by override.

## Verify

```bash
curl -s -H "Authorization: Bearer $OMNI_KEY" http://127.0.0.1:20128/api/settings/compression | jq '.defaultMode,.autoTriggerTokens,.comboOverrides,.cavemanOutputMode'
python3 ops/hermes/goalworld_omniroute.py test context-1m
python3 ops/hermes/goalworld_omniroute.py test tooling
```