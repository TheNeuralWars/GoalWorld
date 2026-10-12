# Discord channel IDs — #dev-room / #trading (2026-08-21)

Collected for GW-SOC-001. Numeric IDs only; nothing invented.

Guild (widget, public): **GoalChain** `1503668119053406330`

## Collected

| Channel | Numeric ID | Evidence | Status |
|---------|------------|----------|--------|
| `#💻┃dev-room` | `1504234802734174310` | OpenClaw/Hermes session origin `chat_name` = `GoalChain / #💻┃dev-room` in `/data/apps/dot-hermes.archive/profiles/hermes-ceo/sessions/sessions.json` and matching `channel_directory.json`. Same snowflake as `DISCORD_HOME_CHANNEL` / hub home. | **Verified (historical session, not guessed)** |
| `#trading` | — | Not in any session origin, channel directory, ops router, or widget. Discord bot token (`DISCORD_BOT_TOKEN` alias in hermes-ceo) returns **401 Unauthorized**, so live `GET /guilds/{id}/channels` cannot be used. Public invite `discord.gg/nzjHNBfSh` is **Unknown Invite**. Widget lists only three **voice** channels (press-conference, stadium-tunnel, WAR-ROOM). | **Not found — do not invent** |

## Widget-only voice channels (not the targets)

| Channel | ID |
|---------|----|
| `🎙️┃press-conference` | `1504249626742751324` |
| `🏟️┃stadium-tunnel` | `1504249627921350786` |
| `🎥 WAR-ROOM (STREAMING)` | `1504592603084230687` |

## Already documented (not this task)

See `docs/intake/2026-08-18-bot-mode-config.md`: `#hermes` `1508596088125522001`, `#dev-announcements` `1506815180129173504`, `#announcements` `1503668120521408513`, `#genesis-lounge` `1504207669773336639`, `#degen-locker-room` `1504251275175264352`, `active-research` forum `1508206161000923176`.

## Wired (GW-SOC-002, 2026-08-21)

`#dev-room` `1504234802734174310` is in hermes-ceo `discord.channel_prompts` (English: economy / on-chain / UI). Threading stays ON (`auto_thread: true`, `require_mention: true`). **Not** in `free_response_channels` (still only `#hermes` `1508596088125522001`). `#trading` was not invented.

Same single gateway left running (PID 841352). Prompt takes effect after an out-of-band restart of that same unit — do **not** start a second gateway.

## Re-verified 2026-08-21 19:10 UTC (GW-SOC-003)

Live hunt still empty. **Do not invent.**

| Check | Result |
|-------|--------|
| Widget `GET /guilds/1503668119053406330/widget.json` | Same 3 **voice** channels only (press-conference, stadium-tunnel, WAR-ROOM). No `#trading`. |
| Invite `discord.gg/nzjHNBfSh` | HTTP 404 `Unknown Invite` (code 10006). |
| Live hermes-ceo `channel_directory.json` | Platforms: telegram only. No Discord listing. |
| Archive hermes-ceo `channel_directory.json` + `sessions.json` | Discord names: `#💻┃dev-room`, `#💬┃hermes-ceo`, `#hermes`, `nicobellopez` DM, `#player-images` thread, `#jito-strategy` thread, `#openclaw-chat`, `#👑┃genesis-lounge`. **No `#trading`.** |
| Gateway | Single PID `841352` still running. Not restarted. No second gateway started. |

## Next (GW-SOC-003 — blocked on Nico)

1. Nico (or a working Discord bot token) must confirm/create `#trading` and paste its snowflake.
2. Record the ID in this file.
3. Spawn hermes-ceo to add it to `discord.channel_prompts` (English: signals / execution / risk). Threading ON. Do **not** add it to `free_response_channels`.
4. Do **not** start a second gateway.
