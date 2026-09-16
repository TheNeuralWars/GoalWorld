# HERMPro MoA Preset — Configuration & Usage
> Documented: 2026-08-16 | Maintainer: Hermes Manager

---

## What is HERMPro?

HERMPro is a **Mixture of Agents (MoA)** preset for Hermes. It uses 4 reference models to generate diverse perspectives, then aggregates them into a single robust response. This reduces individual model bias and improves output quality for complex tasks.

## Configuration

```yaml
moa:
  default_preset: HERMPro
  presets:
    HERMPro:
      reference_models:
        - model: solar-pro4
          provider: nous
        - model: hy3
          provider: nous
        - model: step-3.7-flash
          provider: nous
        - model: laguna-s-2.1
          provider: nous
      aggregator:
        model: longcat-2.0
        provider: nous
      temperatures:
        reference: 0.6
        aggregator: 0.4
      max_tokens: 4096
      degraded_policy: loud
      fanout: user_turn
```

## Reference Models

| Model | Provider | Strengths |
|-------|----------|-----------|
| **Solar Pro 4** | Nous (upstage) | Strong reasoning, coding, math |
| **HY3** | Nous (tencent) | Multilingual, creative tasks |
| **Step 3.7 Flash** | Nous (stepfun) | Fast inference, good for quick tasks |
| **Laguna S 2.1** | Nous (poolside) | Balanced, good for general tasks |

## Aggregator

- **Model**: Longcat 2.0 (meituan/nous)
- **Temperature**: 0.4 (lower = more focused/deterministic)
- **Role**: Synthesizes the 4 reference outputs into a single coherent response

## When to Use HERMPro

**Best for:**
- Complex debugging sessions
- Document analysis and synthesis
- Multi-perspective decision making
- Tasks where single-model bias is a concern

**Not ideal for:**
- Simple questions (adds latency)
- Direct chat (overkill)
- Tasks requiring real-time responses

## Degraded Policy

`loud` — If a reference model fails, the system announces it explicitly rather than silently dropping the response. This ensures transparency about which perspectives are missing.

## Fanout Strategy

`user_turn` — All 4 reference models respond to each user turn, then the aggregator synthesizes. This provides maximum diversity at the cost of higher token usage.

## Free Tier Considerations

All models in HERMPro are `:free` tier from Nous. This means:
- **No direct cost** for using these models
- **Rate limits** apply (shared across all free-tier users)
- **No SLA** — free models may be slower or unavailable during peak times
- **Fair use** — Nous may throttle excessive usage

## Switching Presets

```bash
# Switch to HERMPro
/model HERMPro

# Switch to default (single model)
/model default

# Other presets
/model MAX    # Heavy debug (coding + parameters + writing -> context-1m)
/model FAST   # Low latency (small models)
/model PRO    # Agents/JSON (tooling + coding -> context-1m)
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Slow responses | 4 models + aggregator = higher latency | Switch to FAST for quick tasks |
| Inconsistent quality | One reference model degraded | Check `loud` degraded announcements |
| Token exhaustion | High fanout usage | Monitor usage, switch to default for simple tasks |
