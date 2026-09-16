# GoalWorld — Systems Index
> Navigation hub for all infrastructure docs. If you don't know where to look, start here.
> Last updated: 2026-08-16

---

## Quick Reference: "I need to..."

| Need | Go to |
|------|-------|
| Edit live marketing HTML (`goalworld.fun`) | `/data/apps/GoalChain/docs` — this tree is frozen. See `docs/README.md` |
| Understand system architecture | `[[01-memory-map]]` |
| Check/update OmniRoute combos | `[[02-combos]]` |
| Track startup credit applications | `[[03-startup-credits]]` |
| See current blockers | `[[04-blockers]]` |
| Read the Achievements Manifesto | `[[05-achievements-manifesto]]` |
| Understand HERMPro MoA preset | `[[06-moa-hermpro]]` |
| Recall a past session or task | `session_search(query="...")` |
| Read user preferences / rules | Hermes Memory (`memory()`) |
| Query past context semantically | `honcho_search(query="...")` |
| SSH into VPS | `ssh ubuntu@100.101.211.44` |
| Check API health | `curl -s http://localhost:3001/health` |
| Check all daemons | `pm2 list` + `systemctl --user status gbrain-sync` |

---

## docs/infrastructure/ Index

| File | Contents | When to use |
|------|----------|-------------|
| `memory-map.md` | Full architecture diagram, all systems, DNS, combos summary, anti-noise rules | Onboarding, orientation, system overview |
| `combos.md` | OmniRoute combo configs (tiers, models, rules) | Before touching OmniRoute |
| `startup-credits.md` | Credits dashboard, critical path, deliverables, company profile | Working on applications |
| `blockers.md` | Active infrastructure and business blockers | Prioritization, weekly review |
| `05-achievements-manifesto.md` | Core pivot to "Mundo de Logros" (SaaS Saga, AI Video, Trading, GoalChain) | General vision, side-project orientation |
| `06-moa-hermpro.md` | HERMPro MoA preset configuration, reference models, aggregator, degraded policy | Understanding the current chat model setup |
| `systems-index.md` | This file — navigation hub | When lost |

---

## Live Services

| Service | URL / Endpoint | pm2 / systemd name |
|---------|---------------|---------------------|
| Frontend | https://play.goalworld.fun | Vercel (auto-deploy) |
| CRM | https://crm.goalworld.fun | Vercel (auto-deploy) |
| API Server | http://localhost:3001 | node dist/main (Docker: goalworld-api) |
| Video Daemon | Internal | pm2: `hermes-video-daemon` (id=8) |
| Raft Daemon | Internal | pm2: `raft-daemon` (id=7) |
| Notion Intake | Internal | pm2: `hermes-notion-intake` (id=4) |
| gBrain | :8648 (Tailscale) | `gbrain serve` (bun process) |
| OmniRoute | http://100.101.211.44:20128 | Docker on VPS |

---

## Hermes Memory Structure (what's stored where)

| Topic | System | Tool |
|-------|--------|------|
| OmniRoute rules + combos | Hermes Memory | `memory()` |
| Nico's preferences + steering | Hermes Memory + Honcho | `memory()` / `honcho_profile()` |
| Startup credits anchors | Hermes Memory | `memory()` |
| Full docs / architecture | Obsidian (`docs/infrastructure/`) | `read_file()` / `write_file()` |
| Semantic context | gBrain + Honcho | `honcho_search()` / `honcho_reasoning()` |
| Task history | Session DB | `session_search()` |
| How-to procedures | Skills | `skill_view()` / `skills_list()` |

---

## Repo Layout

```
/data/apps/GoalWorld/
├── INDEX.md              ← YOU ARE HERE
├── CLAUDE.md             ← Hermes CEO rules
├── AGENTS.md             ← Agent routing
├── api/                  ← Node.js API server (Docker: goalworld-api)
├── webapp/               ← React frontend (Vercel)
├── sdk/                  ← GoalWorld SDK
├── contracts/            ← Solana Anchor program (Rust)
├── scripts/              ← Automation & ops scripts
│   └── video_automation/ ← Marketing pipeline scripts
├── ops/hermes/           ← Hermes manager scripts
├── data/marketing_pipeline/ ← Pipeline run state, logs, schedule
├── docs/
│   ├── infrastructure/   ← YOU ARE HERE (memory-map, combos, credits, index)
│   ├── intake/           ← Active decisions, tasks, runbooks
│   └── proposals/        ← Feature / architecture proposals
├── ai_context/           ← gBrain import source
└── ventures/             ← Active ventures (agentic-trading, ai-cinema, publisher-lore, goalchain-soccer)
```

---

## Current state (2026-08-16)

- **API**: ✅ Docker `goalworld-api` :3001 healthy
- **gBrain**: ✅ `gbrain serve` :8648 active
- **OmniRoute**: ✅ Docker `100.101.211.44:20128` healthy
- **Frontend**: ✅ `play.goalworld.fun` (Vercel)
- **Mundial 2026 MVP**: Devnet implemented, mainnet pending
- **Postiz**: ⚠️ Unhealthy (6 weeks) — needs diagnosis
- **Honcho**: ⚠️ Cold storage — needs manual resume at https://app.honcho.dev
