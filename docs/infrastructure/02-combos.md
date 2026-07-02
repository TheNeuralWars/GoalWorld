# OmniRoute Combos Configuration

## Active Combos

### coding-best
- **Tier 1**: `nvidia/nemotron-3-ultra-550b-a55b`
- **Tier 2**: `moonshotai/kimi-k2.6`
- **Tier 3**: `deepseek/deepseek-v4-pro` (NV)
- **Rule**: Use NV first for heavy context tasks (>32K tokens).

### coding-fast
- **Tier 1**: NV (10 keys) — `qwen3.5-122b-a10b`
- **Tier 2**: KC — `qwen/qwen3-coder` + `deepseek/deepseek-v4-flash`
- **Tier 3**: OpenRouter fallback — `qwen2.5-coder-32b-instruct:free`
- **Rule**: Omit `connectionId` for KC auto-balancing.

### deep-reasoning
- **Tier 1**: `x-ai/grok-4.3`
- **Tier 2**: `nvidia/nemotron-3-ultra-550b-a55b`
- **Tier 3**: `deepseek/deepseek-r1`
- **Rule**: Isolate streaming/non-streaming requests to NV.

## Resilience Config
```json
{
  "retry": 3,
  "timeout": 300,
  "fallback_strategy": "next_provider"
}
```

## How to Update
1. **Edit `storage.sqlite`** (remote SSH):
   ```bash
   ssh ubuntu@100.101.211.44 "python3 /path/to/update_script.py --combo coding-fast"
   ```
2. **Apply resilience**:
   ```bash
   curl -X PATCH -H "Authorization: Bearer sk-cac9fb818e70e6bb-f4dcba-60525661" -d '{"retry": 3}' http://100.101.211.44:20128/api/resilience
   ```