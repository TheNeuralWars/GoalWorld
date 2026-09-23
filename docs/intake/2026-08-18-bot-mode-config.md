---
title: "2026-08-18 Bot Mode Discord (Slack-style threads) — configuration"
date: 2026-08-18
status: config-done / needs-gateway-restart / needs-channel-IDs
owner: Nico / hermes-ceo
tags: [discord, bot-mode, gateway, threads, slack-style, hermes-config]
---

# 2026-08-18 Bot Mode Discord — #dev-room / #trading (Slack-style threads)

## Objectivo
Configurar Bot Mode de Hermes para Discord con **threads estilo Slack** en los
canales **#dev-room** y **#trading** de GoalWorld, perfil **hermes-ceo** (el
único gateway activo del VPS — regla estricta: **NO** iniciar un segundo gateway).

## Estado del gateway (verificado)
- Unidad systemd `hermes-gateway-hermes-ceo.service` **running**, PID `470482`,
  iniciada `2026-08-18 16:35:22 UTC` (proceso manual, no servicio separado).
- Ejecuta `python -m hermes_cli.main --profile hermes-ceo gateway run` con
  `HERMES_HOME=/data/hermes-home/profiles/hermes-ceo`.
- `gateway_state.json` → `running`, plataformas: **telegram: connected**. 
  **Discord NO estaba conectado**: la clave del token en `.env` era
  `DISCORD_TOKEN` (obsoleta/muerta). Hermes sólo lee `DISCORD_BOT_TOKEN`
  (`gateway/config.py` `PLATFORM_TOKEN_ENV_NAMES[Platform.DISCORD]` y
  `plugins/platforms/discord/adapter.py` `_is_connected`). Por eso el bot
  Discord nunca aparecía.
- `ps aux` confirma un único gateway para hermes-ceo. No se tocó.

## Hallazgo crítico — variable de token equivocada
El repositorio GoalWorld y todos los perfiles tienen `DISCORD_TOKEN`, pero
**Hermes (esta versión) sólo reconoce `DISCORD_BOT_TOKEN`**. El token de bot
es válido (formato `MT…` de 72 chars); sólo cambió el nombre de la variable.
Ese fue el bloqueador real de todo el Bot Mode Discord.

## Cambios realizados

### 1. `/data/hermes-home/profiles/hermes-ceo/.env`
Añadido alias paralelo (mismo valor que `DISCORD_TOKEN`):
```dotenv
DISCORD_BOT_TOKEN="<mismo token que DISCORD_TOKEN>"
```
Backup: `.env.bak-bot-mode-20260818-173602`.

Validado: `hermes_cli.gateway.get_env_value('DISCORD_BOT_TOKEN')` devuelve SET
(len 72). Tras esto, `gateway.config.load_gateway_config()` muestra:
```
Platform.DISCORD: enabled=True | token set=True
discord home_channel = 1504234802734174310
discord extra free_response = 1508596088125522001
discord extra channel_prompts keys = ['1506815180129173504']
```

### 2. `/data/hermes-home/profiles/hermes-ceo/config.yaml`
Añadido al final un bloque `discord:` + `group_sessions_per_user: true`
(Slack-style).
Backup: `config.yaml.bak-bot-mode-20260818-174004`. YAML validado
(`yaml.safe_load` OK; `load_gateway_config()` OK).

```yaml
discord:
  require_mention: true            # @mention para disparar en canales de servidor
  thread_require_mention: false    # bot ya en un hilo → sin @mention
  auto_thread: true                # auto-crea un hilo por @mention = threading Slack
  reactions: true                  # feedback visual 👀✅❌
  history_backfill: true
  history_backfill_limit: 50
  allow_mentions:
    everyone: false
    roles: false
    users: true
    replied_user: true
  free_response_channels:
    - 1508596088125522001          # #hermes ops — responde sin @mention
  channel_prompts:
    "1506815180129173504": |
      #dev-announcements — technical/dev updates in English (public surface).
      Keep it concise, one update per post.
group_sessions_per_user: true       # aísla sesión por usuario en canales compartidos
```

### 3. Canales conocidos del servidor GoalWorld (IDs verificados en repo)
| Canal | ID | Nota |
|---|---|---|
| home (todos los perfiles) | `1504234802734174310` | `DISCORD_HOME_CHANNEL` |
| #hermes ops | `1508596088125522001` | free-response ya configurado |
| #dev-announcements | `1506815180129173504` | `post_video_update.py` |
| #📢 announcements | `1503668120521408513` | marketing |
| #👑 genesis-lounge | `1504207669773336639` | marketing |
| #🍻 degen-locker-room | `1504251275175264352` | marketing |
| active-research forum | `1508206161000923176` | `config.env.example` |

### 4. Channel IDs — #dev-room collected; #trading still missing
Update 2026-08-21 (GW-SOC-001). Do not invent IDs.

| Canal | ID | Evidence |
|---|---|---|
| #💻┃dev-room | `1504234802734174310` | Hermes session origin `chat_name` = `GoalChain / #💻┃dev-room`. Same ID as `DISCORD_HOME_CHANNEL`. |
| #trading | **unknown** | No session, router, widget, or live REST listing. Bot token 401. Invite dead. |

→ **GW-SOC-002 done:** `#dev-room` `1504234802734174310` is in hermes-ceo
  `discord.channel_prompts` (English economy/on-chain/UI; threading; not
  free-response). `#trading` still unknown — do not invent. Full note:
  `docs/intake/2026-08-21-discord-channel-ids.md`.

## Cómo funciona el "threading estilo Slack" en Discord (Hermes)
- `discord.auto_thread: true` (default) — cada `@mention` en un canal de texto
  crea un **hilo Discord** nuevo, aislado (Slack-like) con su propia sesión.
- Dentro del hilo ya participante, no se requiere más `@mention`
  (`thread_require_mention: false`).
- `free_response_channels` = canales que responden **sin** @mention (siendo
  ellos también salta auto-threading → ligero chat inline). GUIDED para #hermes;
  para #dev-room/#trading queremos threading (así que NO los haremos free-response).
- `group_sessions_per_user: true` aísla sesión por usuario en canales compartidos.
- `channel_prompts` = prompt efímero por canal/hilo (por tema). Placeholder ya
  para #dev-announcements.

## Pendientes / bloqueadores
1. **Restart del MISMO gateway** (`systemctl --user restart hermes-gateway-hermes-ceo`)
   para que Hermes lea `DISCORD_BOT_TOKEN` + bloque `discord:`. Debe hacerlo
   quien opera el DÍA (parent agent / hermes-ceo), respetando "un solo gateway".
   NO iniciar `hermes gateway run` por separado.
2. **Nico debe dar el ID de #trading** (snowflake real). #dev-room already
   wired (`1504234802734174310` in `channel_prompts`). When #trading exists:
   add it the same way (English signals/execution/risk; threading ON; do not
   add to `free_response_channels`).
3. **Verificación post-restart**: enviar un @mention de prueba al bot en Discord
   y comprobar que crea un hilo nuevo y responde. Revisar `journalctl --user -u
   hermes-gateway-hermes-ceo` → "✓ discord connected".

## Diff de cambios
- `.env`: +`DISCORD_BOT_TOKEN` (alias).
- `config.yaml`: +bloque `discord:` y `group_sessions_per_user`.
- No se tocaron otros perfiles (regla: no modificar otros profiles sin confirmar;
  todos tenían el mismo `DISCORD_TOKEN` muerto — se informa, no se cambia).
- Backups creados (enumerados arriba).