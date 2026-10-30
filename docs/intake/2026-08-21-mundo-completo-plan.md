# Mundo Completo — plan de acción (2026-08-21)

GoalWorld es el **mundo**. GoalChain es la **cadencia** (txs). El hub ya existe;
esto lo lleva de “puerta” a producto correlacionado.

## Backtest (live, post-hub)

| Superficie | HTTP | Diagnóstico |
|------------|------|-------------|
| `/` hub | 200 | Funciona; aún pobre vs Matchday (sin hero art, sin covers) |
| `/goalchain` | 200 | Única página “completa” visualmente |
| `/goalworld.html` | 200 | Lore real; nav ahora apunta al hub |
| `/go/reader` | 200 | Libro vivo; dock ya no te tira a Play |
| `/pitch` | 200 | Deck JS; se veía vacío si `gc_lang` inválido (parcheado) |
| `/arcade` `/agents` `/mega-guide` `/tokenomics` `/colabs` `/ceo` `/protocol` `/legal` `/pre-nft` `/map` | 200 | HTML de marketing, chrome inconsistente |
| `play.goalworld.fun/*` | 200 (build viejo) | **dApp**: menús densos; **build actual ERROR** `@solana/web3.js` desde `goalchain-sdk` |
| GitHub Pages CI | fail | Job NFT naming; DNS real es Vercel |

### Concepto (general → particular)

1. **Mundo de Logros** — un estudio con 4 verticales que se *tocan* (IP, fútbol, trading, cine).
2. **Settlement** — una sola cadena de verdad (GoalChain / Play) para wallet, apuestas, royalties.
3. **Read-only vs transaccional** — docs nunca firman; Play nunca es la home.
4. **Correlación** — un personaje de Fractured Code puede ser carta, yield, o cutscene. Hoy están desconectados.
5. **Honestidad** — DEVELOPER MODE / simulación debe ser un banner único, no 12 copys distintos.

### Composición de páginas (objetivo)

Cada URL de marketing: **mismo chrome** (logo World · Matchday · Books · Play) + **un propósito** + **un CTA**.
Cada ruta Play: **una zona** (Matchday / Club / DeFi / Lore) sin 40 items de rail.

## Epics → perfiles

| Epic | Perfil | Por qué |
|------|--------|---------|
| Play build verde | `dev` | Sin esto no hay World-nav en dApp |
| Chrome unificado docs | `dev` + `qa` | Las subpáginas “no se entienden” |
| Hub cinematográfico | `creative` | Matchday ya gana; el hub debe igualarlo |
| Reader producto | `creative` | Cover, resume, book 2 teaser |
| Betting honesty + UX | `trader` + `money` | Presale/oracle vs simulación |
| Tokenomics vs chain | `money` | Página vs on-chain |
| Fixture WC2026 | `research` | Grupos/oráculo |
| Lore↔NFT bridge | `product` | Correlación |
| Cinema landing | `creative` | Vertical 2 vacía en el hub |
| Ship / CI / Vercel | `hermes-ceo` | Pages CI + play deploy |
| Social EN | `social` | Superficies públicas |
| Visual QA matrix | `qa` | Backtest continuo |

Kanban board: `mundo-completo` · workspace `dir:/data/apps/GoalWorld`.
