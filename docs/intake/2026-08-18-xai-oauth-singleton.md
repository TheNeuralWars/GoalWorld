# xAI OAuth fleet = singleton root (2026-08-18)

## What broke
`goalchain-credential-maintain.timer` ran `sync-xai-oauth-fleet.py`, which preferred `hermes-ceo` and copied its Aug-16 grant (including `refresh_token`) onto every profile. That overwrote the fresh 19:56 login on `research`. xAI rotates refresh tokens; the copy produced `invalid_grant` / Refresh token has been revoked.

## Fix
- Live grant lives only on `/data/hermes-home/auth.json` (hardlinked to `~/.hermes/auth.json`).
- Profiles no longer carry `providers.xai-oauth` or `credential_pool.xai-oauth` — they inherit + write-through (Hermes #43589 / #74339).
- Sync picks newest healthy `last_refresh`, never ceo-first.
- `hermes-xai-oauth-refresh.py --all-agent-profiles` refreshes root once (no per-profile loop).
- Restored from `profiles/research/state-snapshots/20260818-200024-pre-update/auth.json`.
- Verified: `hermes --profile trader` + `grok-4.6` / `xai-oauth` returned `PONG`. Root fingerprints unchanged after the call.

## Do not
- Copy `refresh_token` into 9 `auth.json` files.
- Set fleet `model.default` to `grok-4.6` (opt-in via `/model`).
