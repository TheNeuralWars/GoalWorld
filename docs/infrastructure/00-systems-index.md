# GoalWorld — Systems Index
> Navigation hub for all infrastructure docs. If you don't know where to look, start here.
> Last updated: 2026-07-02

---

## Quick Reference: "I need to..."

| Need | Go to |
|------|-------|
| Understand system architecture | `[[01-memory-map]]` |
| Check/update OmniRoute combos | `[[02-combos]]` |
| Track startup credit applications | `[[03-startup-credits]]` |
| See current blockers | `[[04-blockers]]` |
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
| `systems-index.md` | This file — navigation hub | When lost |

---

## docs/intake/ Structure

| Folder/File | Contents |
|-------------|----------|
| `startup-credits/` | All credit application files (tracker, answers, runbook, pitch deck) |
| `MUNDIAL-2026-DEMO-RUNBOOK.md` | Demo runbook for World Cup 2026 launch |
| `2026-05-26-mundial-fcc-queue-freeze.md` | MVP freeze decision |
| `2026-06-22-dot-hermes-vs-profiles-*.md` | Hermes profile setup decisions |
| `voice-task-*.md` | Historic voice task transcripts (archive, low priority) |
| `growth-task-*.md` | Growth tasks (landing, badges, metadata) |

---

## Live Services

| Service | URL / Endpoint | pm2 / systemd name |
|---------|---------------|---------------------|
| Frontend | https://play.goalworld.fun | Vercel (auto-deploy) |
| CRM | https://crm.goalworld.fun | Vercel (auto-deploy) |
| API Server | http://localhost:3001 | pm2: `hermes-api-server` (id=12) |
| Video Daemon | Internal | pm2: `hermes-video-daemon` (id=8) |
| Raft Daemon | Internal | pm2: `raft-daemon` (id=7) |
| Notion Intake | Internal | pm2: `hermes-notion-intake` (id=4) |
| gBrain Sync | :8648 (Tailscale) | systemd: `gbrain-sync.service` |
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
├── api/                  # Node.js API server (dist/index.js → pm2)
├── webapp/               # React frontend (Vercel)
├── sdk/                  # GoalWorld SDK (symlinked as goalworld-sdk in api)
├── scripts/              # Automation & ops scripts
│   └── video_automation/ # Marketing pipeline scripts
├── ops/hermes/           # Hermes manager scripts
├── data/marketing_pipeline/ # Pipeline run state, logs, schedule
├── docs/
│   ├── infrastructure/   # ← YOU ARE HERE (memory-map, combos, credits, index)
│   ├── intake/           # Active decisions, tasks, voice notes
│   ├── archive/          # Stale / historical docs
│   └── proposals/        # Feature / architecture proposals
└── ai_context/           # gBrain import source
```
