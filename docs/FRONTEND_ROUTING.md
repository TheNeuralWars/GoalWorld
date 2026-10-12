# Frontend routing (marketing vs transactional)

> **GW-SRC-001 (2026-08-21):** live marketing HTML is **`/data/apps/GoalChain/docs`**, not this tree.
> This file is a map of `https://goalworld.fun`. Do not edit GoalWorld `docs/*.html` to change production.
> Freeze pointer: [`README.md`](./README.md).

## Canonical URLs

| Surface | URL | Package | Role |
|--------|-----|---------|------|
| **Hub (Mundo de Logros)** | `https://goalworld.fun` | `docs/index.html` | Studio front door: lore, matchday, cinema, betting, trading |
| **AI Cinema** | `https://goalworld.fun/cinema` | `docs/cinema.html` | Vertical 2: trailer slot, stills, marketing-control |
| **Map** | `https://goalworld.fun/map.html` | `docs/map.html` | Full inventory of public surfaces |
| Matchday (legacy homepage) | `https://goalworld.fun/goalchain.html` | `docs/goalchain.html` | Football marketing (World Cup, packs, ticker) |
| Books | `https://goalworld.fun/go/reader` | `docs/go/reader` → Play `/reader` | Fractured Code / Neural Wars Kindle |
| Lore portal | `https://goalworld.fun/goalworld.html` | `docs/goalworld.html` | Neural Wars / lore door |
| Author studio | `https://goalworld.fun/studio.html` | `docs/studio.html` | Lore-first desk (forge, saga seed, KDP math). `/go/studio` redirects here. Do **not** send authors to Play `/studio` — that path is the GoalChain SPA fallback (dashboard clutter). |
| Transactional webapp | `https://play.goalworld.fun` | `goalchain_webapp/` | Wallet, apuestas, claims, perfil on-chain |
| Short alias | `https://goalworld.fun/go` | `docs/go/index.html` | Redirect → `play.goalworld.fun` |
| Legacy path | `https://goalworld.fun/app.html` | `docs/app.html` | Redirect → `play.goalworld.fun` |

## Information architecture

```
GoalWorld hub (read-only)
├── Publisher Lore     → /goalworld.html  ·  /studio.html  ·  /go/reader
├── GoalChain Matchday → /goalchain.html  (sports marketing)
├── Settlement (Play)  → play.goalworld.fun
│     ├── /estadio     live betting
│     ├── /club        roster
│     ├── /defi        swarm
│     └── /            ops dashboard
├── AI Cinema          → /cinema.html  (trailers, stills; Play /marketing-control)
├── Arcade             → arcade.html · play/penalty · play/pack
└── Docs               → pitch · mega-guide · agents · tokenomics · colabs · ceo · legal
```

**Rule:** GoalChain is the *cadence* (transactions). GoalWorld is the *world* (orientation). The former homepage is preserved at `/goalchain.html`. Nothing was deleted.

Shared top chrome (`assets/js/gw-shell.js`) injects **World · Matchday · Books · Lore · Play** on every marketing HTML page except `body.pitch-mode`. Absolute URLs, Outfit / `#14f195` / `logo_3d_clean`. Matchday keeps its own page header — do not restyle it.

## Ownership rules

- **`docs/`** no ejecuta transacciones reales. CTAs de juego/apuestas apuntan a `/go/` o `play.goalworld.fun`.
- **`goalchain_webapp/`** es el único cliente transaccional soportado en devnet/mainnet.

## Deploy

### Marketing (`/data/apps/GoalChain/docs/`)

Vercel project **goal-chain** deploys repo **TheNeuralWars/GoalChain**, Root Directory = `docs`. Domain `goalworld.fun`.

Verified 2026-08-21 19:07 UTC: live `/` bytes matched `/data/apps/GoalChain/docs/index.html` and differed from this repo's copy. Later disk edits to GoalChain `index.html` ship on the next GoalChain deploy, not from here.

`/data/apps/GoalChain/docs/vercel.json` is the routing source of truth:

- `cleanUrls: true` — `/pitch.html` and `/pitch/` both 308 to `/pitch`
- `trailingSlash: false` — no directory-style marketing URLs
- **No SPA catch-all.** Unknown paths serve `docs/404.html` (GoalWorld chrome), never `index.html` and never `/go` (the Play redirect shell).

GitHub Pages still works as a fallback host; it also picks up `404.html`.

### Play (`goalchain_webapp/`)

Separate Vercel project. Domain `play.goalworld.fun`. Menu group **World** links back to the hub.

Config de menú: `goalchain_webapp/src/config/playNav.ts`.
`MARKETING_BASE` default = `https://goalworld.fun`.

## Shared constant

Browser-side play URL for docs redirects: `docs/assets/js/play_url.js` (`goalworld_PLAY_URL`).
