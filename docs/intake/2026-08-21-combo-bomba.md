# Combo `bomba` (2026-08-21)

Live-probed free-tier max-quality OmniRoute combo. 41 candidates, 16 HTTP 200.

## Dead this pass
- groq: Cloudflare 1010
- cerebras: unavailable ~5h
- opencode: 403
- zenmux: 404 invalid model
- kilocode: 402
- nvidia circuit-breaker after probe thrash (lightning still 200)

## Winners used
Gemini 3.6/3.5 flash, NVIDIA nemotron-3.5-lightning, Mistral medium, Codestral, HF MiMo-V2.5-Pro + DeepSeek-V4-Flash-0731, OpenRouter nemotron-3-ultra-550b:free (3 keys).

## Smoke
5/5 `goalworld_omniroute.py test bomba` → `gemini/gemini-3.6-flash` 200.

Use: `/model bomba` (provider omniroute).
