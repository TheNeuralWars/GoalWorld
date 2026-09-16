# GoalWorld /docs — freeze pointer (GW-SRC-001)

**Do not delete this tree.** It is frozen for marketing HTML, not discarded.

| Surface | Canonical path | Status in *this* repo |
|---|---|---|
| Live marketing HTML (`goalworld.fun`) | `/data/apps/GoalChain/docs` · repo [TheNeuralWars/GoalChain](https://github.com/TheNeuralWars/GoalChain) | **FROZEN.** Do not edit. |
| Operational / agent docs | this `docs/` tree (`infrastructure/`, `intake/`, economy JSON, …) | **ACTIVE.** Edit here. |

Decision date: **2026-08-21**. Policy: **stop dual edits**. No sync job. No copy-back.

---

## Why

`goalworld.fun` is served by Vercel project **goal-chain**, root directory `docs`, from **GoalChain**.

Verified 2026-08-21 19:07 UTC: `GET https://goalworld.fun/` body (7064 bytes, sha256 `e6097e8c…`) was byte-identical to `/data/apps/GoalChain/docs/index.html` and **differed** from this repo's `docs/index.html`.

Vercel still served that 7064-byte snapshot at 19:24 UTC (`x-vercel-cache: HIT`). GoalChain `index.html` was then edited on disk (grew to 15529) — next deploy of **GoalChain** is what will change production. Edits in this tree still cannot.

Editing HTML here cannot change production. Dual edits are how this tree drifted.

---

## Freeze rule (marketing)

Do **not** change these paths in GoalWorld to "fix" or "improve" the live site:

- `docs/*.html`
- `docs/go/**`
- `docs/play/**`
- `docs/assets/**` consumed by those pages (css / js / img / video)
- `docs/vercel.json`
- `docs/CNAME`

If the live page is wrong, open a change in **GoalChain** (`/data/apps/GoalChain/docs/...`) and deploy from that repo.

HTML that exists only here (`studio.html`, `404.html`, `cinema.html`, `go/studio/`) is **not live**. To ship it, add it to GoalChain/docs. Do not treat this copy as the source.

---

## Still active in this tree

Keep writing here:

| Path | Role |
|---|---|
| `docs/infrastructure/` | Platform memory-map, combos, blockers, manifesto |
| `docs/intake/` | Decisions, runbooks, voice tasks |
| `docs/ECONOMIC_CANONICAL_CONFIG.json` | GoalChain economy SoT (on-chain params) |
| `docs/governance/` | Economy / mainnet audits |
| `docs/proposals/` | Feature proposals |
| `docs/kanban/` | Venture backlogs |
| `docs/hermes-workflow/` | Agent runbooks |
| `INDEX.md`, `AGENTS.md`, `CLAUDE.md` (repo root) | Agent routing |

Economy JSON is **not** marketing HTML. It stays canonical in GoalWorld even though the public tokenomics page lives in GoalChain.

---

## What we will not do (yet)

- Delete `docs/` or any HTML snapshot
- rsync / submodule / CI mirror between the two trees
- Point Vercel at this repo without a separate, explicit task

When (if) this snapshot is archived, do it in a dedicated task after GoalChain has every page that still matters.

---

## Map of the live site

URL inventory and dock rules: `FRONTEND_ROUTING.md` (describes production).  
Transactional app remains `https://play.goalworld.fun` (`goalchain_webapp/` in GoalChain).

Intake record: `intake/2026-08-21-docs-source-of-truth.md`.
