# Prompt para Antigravity (Mac local) — copiar y pegar

- **Task Created:** https://github.com/TheNeuralWars/goalworld/issues/257
- **Task Status:** ready

**Fecha:** 2026-05-26  
**Rama sugerida:** `feat/mundial-integration` (desde `main` actualizado)

---

## Prompt (copiar desde aquí)

```
Eres el integrador único de goalworld en Mac. Hermes/FCC ya generan draft PRs en el VPS; tu trabajo es merge, P0 on-chain/oracle/ops, y deploy — sin competir archivo a archivo con FCC en curso.

## Contexto
- Issues #108–#157 creados en GitHub (backlog Mundial + auditoría).
- FCC activo: draft PRs #158–#165 (opencode) — NO reimplementes lo que ya traen esos PRs.
- `main` en remoto importa `SimulationBadge` y `EconomyConfigBanner` pero faltaban archivos — Cursor sube fix en rama `feat/cursor-mundial-handoff-fix` (mergear primero si existe).
- Merge stack #26 + #35 ya MERGED — no re-abrir #32–#34.

## Tu orden de trabajo (hoy)

### 1. Sync
git checkout main && git pull origin main
git fetch origin
# Si existe:
git merge origin/feat/cursor-mundial-handoff-fix   # o cherry-pick commit de archivos faltantes

### 2. P0 inmediato (issues GitHub)
- **#115** — Merge Mundial MVP / land código coherente en main (integración)
- **#109** — Deprecar `goalworld_oracle/src/migrate_config.ts` (ix no existe)
- **#110** — `vault_crank.ts`: execute NO fake txs (hard-fail o dry-run only)
- **#112** — Anchor tests: surfpool o ts-mocha en CI
- **#113** — Deploy play.goalworld.fun (`VITE_API_BASE_URL=https://crm.goalworld.fun/goalworld-api`) — pedir creds Vercel a Nico si faltan

### 3. Revisar y mergear FCC (uno a uno, CI verde)
Prioridad tras P0 fixes:
- #158 #114 QA runbook
- #159 #116 UserProfile
- #160 #117 Estadio badges
- #161 #119 coach apiBaseUrl (post-MVP ok)
- Cerrar/supersede drafts viejos #95–#99 si duplican main

NO mergear en paralelo dos PRs que toquen `FixturesPanel.tsx` o `goalworldClient.ts` sin rebase.

### 4. Verificación obligatoria antes de cada merge
cd goalworld_webapp && npm run build
cd goalworld_oracle && npm run lint
bash goalworld_webapp/scripts/smoke-devnet.sh   # API en :3001 o goalworld_API_BASE prod

### 5. Post-merge
gbrain import ai_context docs/intake
Comentar en #115 y epic #156 qué quedó en main.

## Archivos clave
- Plan: ai_context/MASTER_PLAN.md
- Handoff Hermes: docs/intake/2026-05-26-hermes-manager-handoff.md
- Runbook demo: docs/intake/MUNDIAL-2026-DEMO-RUNBOOK.md

## No hacer
- Cambiar valores en ECONOMIC_CANONICAL_CONFIG.json sin CEO
- Mainnet deploy
- Activar vault_crank execute con txs falsas
- Editar los mismos archivos que un PR FCC abierto sin coordinar

## Éxito hoy
- `main` build verde con SimulationBadge + EconomyConfigBanner presentes
- Al menos 1 P0 oracle fix merged (#109 o #110)
- Deploy Play o branch preview con API prod
- Nico puede demo bet→claim en devnet (issue #114)
```

---

## Issues P0 Antigravity (referencia rápida)

| Issue | Título corto |
|-------|----------------|
| #115 | Merge Mundial MVP |
| #109 | Deprecate migrate_config |
| #110 | Block vault_crank fake execute |
| #112 | Anchor CI surfpool |
| #113 | Deploy Play Vercel |

## FCC en vuelo (revisar, no rehacer)

PRs #158–#165 → issues #114, #116, #117, #119, #122, #123, #133, #134
