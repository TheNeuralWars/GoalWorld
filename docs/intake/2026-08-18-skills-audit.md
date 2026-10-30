# Audit de Skills y Estado de Infraestructura — 2026-08-18

Fecha: 2026-08-18 · Host: GoalWorld VPS (`100.101.211.44` / `89.168.20.135`) · Ejecutado como subagente desde el gateway (sin aplicar cambios desde dentro del gateway).

---

## 1. Hermes Agent — Versión Core

| Item | Valor |
|---|---|
| Versión CLI | **v0.20.4** (2026.8.18) |
| Commit upstream | `9664e386` (44 commits *después* de tag `v2026.8.18`) |
| Install | git (`/data/ubuntu/.hermes/hermes-agent`) |
| Estado | **UP TO DATE** — `git rev-list --count HEAD..origin/main` = 0 commits behind |
| Último tag remoto | `v2026.8.18` |

No hay actualización pendiente de Hermes core.

---

## 2. Skills Instalados — Resumen

`hermes skills list` → **263 habilitados, 0 deshabilitados**: 1 hub-install, 77 builtin, 185 local.

- **Raíz skills:** `/data/hermes-home/skills/` (symlink `~/.hermes/skills` → mismo directorio).
- **Bundle GoalWorld:** `/data/apps/GoalWorld/skills/` (63 dirs, 58 con `version:` en SKILL.md).
- **Profiles:** `/data/hermes-home/profiles/<name>/skills/` (~9 profiles; se propagan configs nuevas).
- Los skills OKX son symlinks a `~/.agents/skills/`.

### Versionado — skills clave del stack

| Skill | Ruta | Versión local |
|---|---|---|
| omniroute-ops | hermes-home/skills/devops/ | *(sin campo `version`)* |
| omniroute-management | hermes-home/skills/devops/ | *(sin campo `version`)* |
| omniroute-combo-management | hermes-home/skills/goalworld/ | `1.7.0` |
| omniroute-db-access | hermes-home/skills/goalworld/ | `1.0.0` |
| video-marketing-automation | hermes-home/skills/media/ | *(sin campo `version`)* |
| gbrain-advisor | hermes-home/skills/ | `1.0.0` |
| onchain-os-integration | hermes-home/skills/devops/ | `1.0.0` (autor Antigravity) |
| goalchain-empresa | **NO INSTALADO** — no se encuentra ningún skill/`goalchain*` excepto `goalchain-sdk` en GoalWorld/api | — |
| goalworld-ops | **NO EXISTE** como skill; existe `brain-ops` en GoalWorld/skills | — |

> **Nota:** `goalworld-ops` y `goalchain-empresa` no existen como skills. Los aproximados del flujo operativo son `omniroute-ops`, `omniroute-combo-management`, `goalworld-*` (brand-content, market-intel, moa-selection) y `brain-ops`.

### Registry / updates verificados

`hermes skills check` (oficial / hub) → **solo 1 skill desactualizado:**

| Skill | Source | Estado |
|---|---|---|
| **yuanbao** | official | **update_available** |

Comando para aplicar (desde shell externo, NO dentro del gateway):
```
hermes skills update yuanbao
```

El resto de skill checks no reportó hits — los 185 skills `local` y los 77 `builtin` no tienen delta de registry detectable vía `hermes skills check` (el check de updates cubre skills de hub "oficial" y hu "hub-installed"; el resto son locales/sin versión en registry). 90,641 skills del hub disponibles; solo el oficial `yuanbao` del instalado requiere update.

### Versionado local de bundle GoalWorld (58 skills con version)

Rangos: `0.1.0`–`2.2.0`. Ejemplos: briefin `1.3.0`, daily-task-manager `2.0.0`, meeting-ingestion `2.2.0`, skillify `2.0.0`, soul-audit `2.0.0`, omniroute-combo-management `1.7.0`. Skills sin campo `version`: capture, ingest, publish (heredan de repo principal, no versionados individualmente).

---

## 3. OmniRoute — Estado

| Item | Valor |
|---|---|
| Contenedor | `6e8bf9e3df04` diegosouzapw/omniroute:**latest** |
| Status | **Up 6 days (healthy)** |
| Creado | 2026-07-23 |
| Paquete `/app/package.json` | **3.8.43** |
| Latest en npm registry | **3.8.49** → **UPDATE disponible (Δ 3.8.43 → 3.8.49)** |
| DB | `/data/docker/volumes/omniroute-data/_data/storage.sqlite` (306 MB, root-owned, hot-reload) |
| Acceso | host-network en VPS local; API `http://127.0.0.1:20128` |
| UI dashboard | Respondiendo (Next.js serve 200, `/dashboard` OK) |

> **V16.2?** El `latest` actual del contenedor reporta `3.8.43` como versión de paquete npm — no `v16.2`. La versión "16.2" del contexto no corresponde al paquete npm actual; el contenedor corre el `latest` de Docker Hub con paquete interno 3.8.43.

**Comando de update (desde shell externo del VPS, NO dentro del gateway):**
```
cd /data/apps/GoalWorld && docker compose pull omniroute && docker compose up -d omniroute
```
(o si es contenedor standalone: `docker pull diegosouzapw/omniroute:latest && docker stop omniroute && docker run ...`)
Verificar tras update: paquete → `3.8.49`, `docker ps` → healthy.

> Recordatorio de rutina (fuera de este audit): tras actualizar, re-verificar combos 402/429 y limpieza `call_logs/` (306 MB DB creciendo).

---

## 4. Onchain OS — Estado

| Item | Valor |
|---|---|
| Containers | **NINGUNO** (`docker ps -a | grep onchain` → vacío) |
| Directorios | Sin dir `/onchain*` bajo `/data` ni `/data/apps` |
| Skill | `onchain-os-integration` v1.0.0 (autor Antigravity) instalado en hermes-home/skills/devops |
| CLI | Se invoca vía `npx skills add okx/onchainos-skills --yes -g` / `onchainos` bin |
| Integración | Preflight obligatorio: `onchainos preflight --skill-version 1.0.0` |

Onchain OS es una integración **skill+CLI** (no un servicio docker). Sin proceso activo en el VPS; operación bajo demanda vía a skill.

---

## 5. Keys E2B — Estado ("revoking keys" en memoria)

| Item | Valor |
|---|---|
| `/data/hermes-home/.env` | **NO contiene ninguna variable E2B** |
| `/data/apps/GoalWorld/.env` | NO E2B |
| webapp/.env, oracle/.env | NO E2B |
| OmniRoute server.env | NO E2B (solo `STORAGE_ENCRYPTION_KEY`, `JWT_SECRET`, `API_KEY_SECRET`) |
| config.yaml | Sin bloque `E2B`/`sandbox`/`executor` |
| Skills | E2B solo se menciona como *instrucción de uso* de la pipeline: `video-marketing-automation/references/modal-e2b-pipeline.md` (`pip install e2b` + `E2B_API_KEY` + `Sandbox.create`) |

**Conclusión:** No existe ningún `E2B_API_KEY` configurado en el entorno. La referencia a "revoking keys" en memoria corresponde al **provider "nvidia"/e2b del combo de OmniRoute**, no a una key en `.env` de Hermes. Evidencia en `omniroute-combo-management`:
- `api_keys` tiene columna `revoked_at` — el mecanismo "revoking" es del esquema de OmniRoute.
- `references/provider-key-preflight.md`: "the key batch was **revoked** / mistyped at source" (llamadas al batch de **nvidia**, HTTP 403 → `invalid`).
- `references/402-reset-verification`: `nvidia conn=7c93e2b3 -> HTTP 403`.

⇒ La "revocación de keys" de la memoria es el **batch de llaves nvidia/e2b revocado en origen** (los 10 keys fallaron). **No hay key E2B activa configurada en Hermes** — la pipeline de video actualmente no tiene credencial E2B; si se necesita, hay que volver a crear/provisionar `E2B_API_KEY` y meterlo en `.env`.

---

## 6. Resumen de Deltas / Items que requieren update

| # | Item | Local | Registry/Remoto | Δ | Acción |
|---|---|---|---|---|---|
| 1 | Hermes core | v0.20.4 (`9664e386`) | up-to-date con main | **none** | — |
| 2 | Skill `yuanbao` | out-of-date | update_available | **update** | `hermes skills update yuanbao` |
| 3 | OmniRoute paquete | 3.8.43 | 3.8.49 | **update** | pull+recreate container |
| 4 | Skill goalchain-empresa | no existe | n/a | — | (no aplica) |
| 5 | Skill goalworld-ops | no existe | n/a | — | (no aplica; usar omniroute-ops + brain-ops) |
| 6 | Key E2B | no configurada | — | **provisionar si se usa video de nuevo** | crear `E2B_API_KEY` |
| 7 | OnchainOS CLI | no corriendo | bajo demanda | — | usar skill `onchain-os-integration` |

### Comandos para aplicar (desde shell externo — PROHIBIDO dentro del gateway)

```bash
# 1. Actualizar skill yuanbao (hub oficial)
hermes skills update yuanbao

# 2. Actualizar OmniRoute (paquete 3.8.43 → 3.8.49)
cd /data/apps/GoalWorld
docker pull diegosouzapw/omniroute:latest
docker stop omniroute && docker rm omniroute   # si standalone
# (recrear con la config exacta previa — ver docker inspect para env/mounts)
docker ps | grep omniroute   # verificar healthy

# 3. (Opcional) Re-provisionar E2B para pipeline de video
#    - Crear E2B_API_KEY en portal E2B
#    - Añadir a /data/hermes-home/.env
```

---

## Reglas respetadas
- ✅ NO se ejecutó ningún update dentro del gateway (todo lectura).
- ✅ NO se leyeron ni loguearon secrets — solo nombres de variables y metadata.
- ✅ Firecrawl no fue necesario: los fetches de registry (npm, Docker Hub) se hicieron vía curl directo.
- ✅ Registry privado (OmniRoute/OnchainOS) accedido localmente en el VPS (`127.0.0.1:20128`), sin necesidad de Tailscale (misma máquina).