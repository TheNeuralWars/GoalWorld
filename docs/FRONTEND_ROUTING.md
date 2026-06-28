# Frontend routing (marketing vs transactional)

## Canonical URLs

| Surface | URL | Package | Role |
|--------|-----|---------|------|
| Marketing / read-only | `https://goalworld.fun` | `docs/` | Landing, docs, dashboards informativos |
| Transactional webapp | `https://play.goalworld.fun` | `goalworld_webapp/` | Wallet, apuestas, claims, perfil on-chain |
| Short alias | `https://goalworld.fun/go` | `docs/go/index.html` | Redirect permanente → `play.goalworld.fun` |
| Legacy path | `https://goalworld.fun/app.html` | `docs/app.html` | Redirect permanente → `play.goalworld.fun` |

## Ownership rules

- **`docs/`** no ejecuta transacciones reales. CTAs de juego/apuestas apuntan a `/go/` o `play.goalworld.fun`.
- **`goalworld_webapp/`** es el único cliente transaccional soportado en devnet/mainnet.

## Deploy

### Marketing (`docs/`)

GitHub Pages via `.github/workflows/goalworld-ci-cd.yml` → dominio `goalworld.fun`.

### Play (`goalworld_webapp/`)

Vercel project con **Root Directory** = `goalworld_webapp`.

1. Import repo en Vercel.
2. Set custom domain: `play.goalworld.fun` (CNAME → Vercel).
3. Optional: add redirect rule on DNS/hosting so `goalworld.fun/go` stays on GitHub Pages (already handled by `docs/go/index.html`).

Config: `goalworld_webapp/vercel.json`.

**Navegación unificada (Play):** el menú de Play replica las secciones de `goalworld.fun`:
- **Jugar** → rutas in-app: `/`, `/fixtures`, `/trading`, `/squad`, `/feed`
- **Explorar** → enlaces a anclas del sitio marketing (`VITE_MARKETING_URL`, default `https://goalworld.fun`)
- **Recursos** → pitch, mega-guías, colabs, legal (marketing)
- **Cuenta** → `/crear-usuario` o `/perfil/:username`

Config de menú: `goalworld_webapp/src/config/playNav.ts`.

## Shared constant

Browser-side play URL for docs redirects: `docs/assets/js/play_url.js` (`goalworld_PLAY_URL`).
