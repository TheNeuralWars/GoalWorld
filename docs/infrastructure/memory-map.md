# GoalWorld — Memory & Systems Map
> Last updated: 2026-07-02 | Maintainer: Hermes Manager

---

## Architecture Overview

```mermaid
graph TD
    subgraph "Knowledge Layer"
        OBS[Obsidian\n/docs/ + /ai_context/]
        GB[gBrain\nsystemd :8648\ntimer every 5min]
        HM[Hermes Memory\n/data/hermes-home/memory/]
        HON[Honcho\nHybrid mode - auto-injected]
    end

    subgraph "Infra Layer"
        OR[OmniRoute\n100.101.211.44:20128\nDockerized]
        API[API Server\npm2 id=12 :3001\n/data/apps/GoalWorld/api]
        FE[Frontend\nplay.goalworld.fun\nVercel]
        CRM[CRM\ncrm.goalworld.fun\nVercel]
    end

    subgraph "Compute Layer"
        VPS[VPS ubuntu\n100.101.211.44\nTailscale]
        CF[Cloudflare DNS\neve/ezra.ns.cloudflare.com]
    end

    OBS -->|gbrain-sync daemon| GB
    GB -->|semantic queries| HM
    HON -->|auto-injected context| HM
    HM -->|system prompt| LLM[LLM Context]

    OR -->|SSH run_remote_python| VPS
    API -->|node dist/index.js| VPS
    FE -->|CNAME| CF
    CRM -->|CNAME → cname.vercel-dns.com| CF
```

---

## Systems Reference

### 1. Knowledge & Memory

| System | Location | Access | Sync | Notes |
|--------|----------|--------|------|-------|
| **Obsidian** | `/data/apps/GoalWorld/docs/` + `/ai_context/` | `read_file()` / `write_file()` | Pushed via `obsidian-git` on Mac | Source of truth for docs |
| **gBrain** | systemd `gbrain-sync.service` on VPS | `gbrain query` | Timer every 5 min, port `:8648` | Semantic KB — already active ✅ |
| **Hermes Memory** | `/data/hermes-home/memory/` | `memory()` tool | Manual (this session) | Rules, prefs, infra anchors |
| **Honcho** | Honcho backend API | `honcho_profile()` / `honcho_search()` / `honcho_conclude()` | Auto (conversation flow) | User profiles + deductions |
| **Session Search** | Local SQLite | `session_search()` | Auto | Historical task recall |

### 2. Infrastructure & Services

| Service | Endpoint | Process | Health Check |
|---------|----------|---------|-------------|
| **OmniRoute** | `100.101.211.44:20128` | Docker container | `GET /api/combos` |
| **API Server** | `localhost:3001` | pm2 id=12 `hermes-api-server` | `GET /health` → `{"status":"OK"}` ✅ |
| **Video Daemon** | N/A | pm2 id=8 `hermes-video-daemon` | `pm2 logs hermes-video-daemon` |
| **Raft Daemon** | N/A | pm2 id=7 `raft-daemon` | `pm2 status` |
| **Notion Intake** | N/A | pm2 id=4 `hermes-notion-intake` | `pm2 status` |
| **gBrain Sync** | `:8648` | systemd `gbrain-sync.service` | `systemctl --user status gbrain-sync` |

### 3. DNS (Cloudflare)

| Record | Type | Target | Proxy |
|--------|------|--------|-------|
| `goalworld.fun` | A | Vercel (104.21.73.224) | ✅ |
| `play.goalworld.fun` | CNAME | `cname.vercel-dns.com` | ✅ |
| `crm.goalworld.fun` | CNAME | `cname.vercel-dns.com` | ✅ |
| MX | MX | `route1/2/3.mx.cloudflare.net` | Email routing → Gmail |

---

## OmniRoute Combos

> Detailed config: `[[combos]]`

| Combo | Tier 1 | Tier 2 | Tier 3 | Key Rule |
|-------|--------|--------|--------|----------|
| `coding-best` | NV `nemotron-3-ultra-550b-a55b` | KC `moonshotai/kimi-k2.6` | OR fallback | NV priority for >32K ctx |
| `coding-fast` | NV `qwen3.5-122b-a10b` (10 keys) | KC `qwen/qwen3-coder` | OR `qwen2.5-coder-32b:free` | Omit `connectionId` in KC |
| `deep-reasoning` | `x-ai/grok-4.3` | NV `nemotron-3-ultra-550b-a55b` | `deepseek/deepseek-r1` | Isolate streaming/non-streaming |
| `coding-extreme` | KC pinned (explicit `connectionId`) | NV | OR | Pin KC for rate-limit isolation |

**Rules:**
- **Nvidia (NV):** 1 entry per `connectionId` → 10 keys = 10 entries.
- **Kilocode (KC):** Omit `connectionId` for auto-balancing (8 accounts), except `coding-extreme`.
- **SQLite updates:** Always via `run_remote_python` over SSH. Never edit directly.
- **Resilience:** Persist via `PATCH /api/resilience` (survives restarts).

---

## Critical Workflows

### OmniRoute: Update a Combo
```bash
ssh ubuntu@100.101.211.44 "python3 /path/to/update_script.py --combo coding-fast"
curl -X PATCH -H "Authorization: Bearer sk-cac9fb818e70e6bb-f4dcba-60525661" \
  -d '{"retry": 3}' http://100.101.211.44:20128/api/resilience
```

### API Server: Restart
```bash
pm2 restart hermes-api-server
curl -s http://localhost:3001/health
```

### gBrain: Manual Import
```bash
systemctl --user status gbrain-sync.service
# or force import:
cd /data/apps/GoalWorld && python3 ops/hermes/gbrain-sync-server.py
```

### PM2: Save State
```bash
pm2 save  # persists current process list across reboots
```

---

## Anti-Noise Rules

| ❌ Don't Store | ✅ Store Here Instead |
|---------------|----------------------|
| Process logs, run IDs, pipeline outputs | Session search (`session_search()`) |
| Temporary task status ("issue #42 in progress") | `todo()` or GitHub Issues |
| Duplicated configs from OmniRoute | Link to `[[combos]]` |
| Tutorial/how-to content | Skills (`skill_manage()`) |
| Stale facts (>7 days, version-specific) | Remove from memory |

---

## Related Docs
- `[[combos]]` — OmniRoute combo configs
- `[[blockers]]` — Active infrastructure blockers
- `[[startup-credits]]` — $600K credits program tracker
