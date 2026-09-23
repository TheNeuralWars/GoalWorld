# CEO sovereign takeover — 2026-09-02

Manager assumed GoalWorld/GoalChain operational CEO. Command line: Discord `#hermes` + this Desktop 1:1. Spanish with Nico; English on every public surface and all code.

## Sync (verified, not claimed)

- **GoalWorld** `/data/apps/GoalWorld` stays on `feat/env-migration` (Mainnet Prep Frozen). Dirty tree, ahead 2 / behind 5. Branch `phase1-responsive-shell-landing-split` **does not exist** on `TheNeuralWars/GoalWorld`.
- **GoalChain** `/data/apps/GoalChain` live checkout is `main` **ahead 109** + dirty trading-sim. Did **not** merge or checkout `phase1-responsive-shell-landing-split` onto live main.
- Fetched `origin/phase1-responsive-shell-landing-split` @ `83a1f409` (`refactor(hermes): upgrade to grok-4.6, purge whatsapp, and formalize discord #hermes ops`).
- Archetypes materialized from that branch into:
  - `/data/apps/GoalChain/.agents/archetypes/`
  - `/data/apps/GoalWorld/.agents/archetypes/`
- gBrain CLI import blocked (PGLite lock on `gbrain serve` + embed credentials missing on `sync_brain`). Page `goalworld-archetype-matrix` written via MCP `put_page`.

## Code policy (Hermes CEO)

Do not implement features in Manager chat. Dispatch via `create-task.sh` / `oa-run-code.sh`.

Inject into issue body:

| Domain | Line |
|---|---|
| Contracts / Anchor / Tokenomics | `Adopt Archetype: .agents/archetypes/solana-architect.md` (Program ID `FbDhM4itBS2Cco7c7PbNvC98Fx7Y5HxqXS1JuXdNcBwg`) |
| Frontend / React / Vite | `Adopt Archetype: .agents/archetypes/frontend-craftsman.md` (0 TS errors, bundle < 500kB) |
| Novels / KDP / Lore | `Adopt Archetype: .agents/archetypes/bestseller-novelist.md` |
| Video / X / Discord copy | `Adopt Archetype: .agents/archetypes/web3-growth-hacker.md` (100% English Max Law) |
| Match / 528 NFTs / Mundial | `Adopt Archetype: .agents/archetypes/sports-commentator.md` |
| Security | `Adopt Archetype: .agents/archetypes/security-auditor.md` |

Live OA worker: `OA_CODE_ENGINE=fcc` (Free Claude Code). Default model slug in script is `nvidia/nemotron-3-super-120b-a12b` but engine is still FCC. On-chain PRs: report, do not merge (frozen).

## Fleet actions taken this session

- Installed `hermes-x-scout.timer` (`OnCalendar=*-*-* 0/2:15:00`). Next: 22:16 UTC. First fire **failed**: xAI HTTP 403 spend/credit cap on `XAI_API_KEY` (not Super Grok OAuth).
- Copied `BUFFER_TOKEN` + `BUFFER_ORG_ID` GoalWorld `.env` → GoalChain `.env` (mode 600, values not logged). Restarted `hermes-video-daemon`. Optimizer now resolves Buffer slots (TikTok/IG/YT). Last published run in `runs.json` remains 2026-06-23.
- Did **not** start a default `hermes-gateway` (ceo/social/trader already running). Desktop talks to `hermes serve` over SSH.

## Health snapshot 2026-09-02 21:06 UTC

- `goalworld-api` :3001 up. `play.goalworld.fun` 200. `goalworld.fun` 200.
- `healthcheck.sh` FAIL: `vault_crank.stale=TRUE` (dry-run timestamp 2026-06-21) — expected, not a live crank.
- Mint gate: pause 48h (burn/emit 0.116 < 0.85).
- Open draft PRs: #876, #875, #873. Hermes issues 856–871 labeled both `status:blocked` and `status:done`.
