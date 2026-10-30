# goalworld Frontend Ownership Policy (P3)

Fecha: **2026-05-22** · pointer update **2026-08-21**

> Live marketing HTML source of truth is `/data/apps/GoalChain/docs` (GW-SRC-001). This file only splits *role* (read-only docs vs transactional webapp). Freeze pointer: [`README.md`](./README.md).

## Scope oficial por superficie

- `goalworld_webapp`: frontend transaccional oficial.
  - Wallet connect
  - Claims
  - Markets / bets
  - Rent / operaciones con impacto on-chain
- `docs`: marketing, documentación, transparencia económica y dashboards read-only.

## Deprecaciones aplicadas en docs

- Los flujos de preventa/simulación transaccional en `docs/index.html` quedan explícitamente en modo read-only.
- Cualquier CTA económica en `docs` debe redirigir a `goalworld_webapp` o documentación operativa.
- URL transaccional canónica: **`https://play.goalworld.fun`** (alias **`https://goalworld.fun/go`**).
- Los datos KPI de economía se consumen desde `GET /api/economy/metrics` cuando el backend está disponible.

## Regla de aceptación para releases

- Ningún flujo de firma o envío de transacciones debe vivir en `docs`.
- Toda operación que modifique estado on-chain debe ejecutarse desde `goalworld_webapp` (o tooling de ops autorizado).
