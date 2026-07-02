# GoalWorld — Agent Index
> **Start here. Always.** This is the map. Read this before opening any other file.
> Last updated: 2026-07-02

---

## What exists, what matters, what to ignore

### ACTIVE — open these
| File/Folder | What it is | When to open it |
|-------------|------------|-----------------|
| `docs/infrastructure/systems-index.md` | Master nav hub — points to every system | Orientation, "where do I look?" |
| `docs/infrastructure/memory-map.md` | Full architecture, live services, DNS, combos | System health, infra questions |
| `docs/infrastructure/startup-credits.md` | $600K credits dashboard + critical path | Credits work |
| `docs/infrastructure/blockers.md` | Active blockers (business + infra) | Prioritization |
| `docs/IMPLEMENTATION_STATUS.md` | What is implemented in code vs pending | Before any code task |
| `docs/intake/` | Active decisions, tasks, voice notes | New tasks, intake |
| `CLAUDE.md` | Hermes CEO coding rules | Before delegating to Hermes CEO |
| `AGENTS.md` | Agent routing rules | Before creating issues |

### IGNORE unless asked
| Folder/File | Why |
|-------------|-----|
| `docs/archive/` | Historical only. Stale. |
| `docs/SESSION_*.md` | Old session logs. Use `session_search()` instead. |
| `docs/PROJECT_INDEX.md` | Points to Mac paths — stale. Superseded by this INDEX. |
| `docs/GOALCHAIN_*.md` | Pre-rebrand. Archive context only. |
| `docs/assets/` | Static assets. Not context. |
| `docs/scratch/` | Throwaway. Never canonical. |

---

## Where to go for each type of task

| Task type | Start here |
|-----------|-----------|
| **Code feature / bug** | `docs/IMPLEMENTATION_STATUS.md` → `CLAUDE.md` → create GitHub issue |
| **Infra / services** | `docs/infrastructure/systems-index.md` |
| **OmniRoute / combos** | `docs/infrastructure/combos.md` |
| **Startup credits** | `docs/infrastructure/startup-credits.md` |
| **New task from Nico** | `docs/intake/` → write intake note → create issue if code needed |
| **Economy / tokenomics** | `docs/ECONOMIC_CANONICAL_CONFIG.json` + `docs/ECONOMIC_BLUEPRINT.md` |
| **On-chain / Anchor** | `contracts/` + `docs/IMPLEMENTATION_STATUS.md` |
| **Marketing / video** | `scripts/video_automation/` + `data/marketing_pipeline/runs.json` |
| **Historical context** | `session_search(query="...")` — not files |
| **Semantic recall** | `honcho_search(query="...")` |

---

## Repo layout (one line each)

```
GoalWorld/
├── INDEX.md              ← YOU ARE HERE
├── CLAUDE.md             ← Hermes CEO rules
├── AGENTS.md             ← Agent routing
├── api/                  ← Node.js API (pm2 hermes-api-server :3001)
├── webapp/               ← React frontend (Vercel → play.goalworld.fun)
├── contracts/            ← Solana Anchor program (Rust)
├── sdk/                  ← GoalWorld SDK
├── oracle/               ← Sports data oracle
├── scripts/
│   └── video_automation/ ← Marketing pipeline (pm2 hermes-video-daemon)
├── ops/hermes/           ← Manager scripts (create-task, context, health)
├── docs/
│   ├── infrastructure/   ← ACTIVE: memory-map, combos, credits, blockers, index
│   ├── intake/           ← ACTIVE: decisions, tasks, runbooks
│   ├── archive/          ← IGNORE: stale historical
│   └── *.md              ← Mixed: check IMPLEMENTATION_STATUS.md first
├── ai_context/           ← gBrain import source (auto-synced every 5min)
└── data/
    └── marketing_pipeline/ ← Pipeline run state + schedule
```

---

## Current state (2026-07-02)

- **API**: ✅ pm2 id=12 `:3001` healthy
- **gBrain**: ✅ systemd `:8648` syncing every 5min
- **OmniRoute**: ✅ Docker `100.101.211.44:20128`
- **Frontend**: ✅ `play.goalworld.fun` (Vercel)
- **P0 blocker**: Legal entity (Delaware C-Corp) — needed for Google/MS/AWS credits
- **Mundial 2026 MVP**: Devnet implemented, mainnet pending
