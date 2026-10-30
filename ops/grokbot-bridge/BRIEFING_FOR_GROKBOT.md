# Briefing for Grok Bot — Hermes bridge is live

Paste this to the Grok Bot that should drive Hermes. It is written to be read by
Grok Bot with no prior context.

---

You can now drive a Hermes Agent host (`goalchain`) directly. Two interfaces exist;
use whichever fits the task. Both are **Tailscale-only** — never expose or Funnel them.

## Interface A — native API (preferred for orchestration)

```
Base URL : http://100.101.211.44:8642/v1
Auth     : Authorization: Bearer $HERMES_API_KEY
Model id : hermes-ceo
```

Verified working from the Hermes side: `/health` returns
`{"status":"ok","version":"0.21.3"}`, auth is enforced (401 without a key, 200
with it), and a real completion returns `API_OK`.

Endpoints: `/v1/chat/completions`, `/v1/responses`, `/v1/models`,
`/v1/capabilities`, `/api/sessions`, `/v1/runs`, `/api/jobs`, `/health`.

**Get your key first** (it is never sent over chat):

```bash
scp ubuntu@100.101.211.44:/data/apps/GoalWorld/ops/grokbot-bridge/.staged/hermes-api.env \
    ~/.hermes-api.env && chmod 600 ~/.hermes-api.env
set -a; . ~/.hermes-api.env; set +a
curl -s http://100.101.211.44:8642/health
curl -s http://100.101.211.44:8642/v1/models -H "Authorization: Bearer $HERMES_API_KEY"
```

## Interface B — SSH relay (works with just SSH)

```bash
scp -r ubuntu@100.101.211.44:/data/apps/GoalWorld/ops/grokbot-bridge ~/grokbot-bridge
cd ~/grokbot-bridge && bash setup-grokbot.sh relay
```

That installs a stdio MCP which SSHs out and runs `hermes -z "<prompt>"` on the
far side. Verified: the exec path returns `RELAY_OK`. The script prints the MCP
config to paste into your app.

## Your own identity — and why it matters

You hold a **dedicated** OmniRoute key, `grokbot-jefe-gabinete`, with `self:usage`
scope only. It **cannot administer keys** (we verified it gets 403 on `/api/keys`).
The fleet has a separate key. This keeps usage attributable per host and scopes
any compromise. Do not share keys across hosts, and never paste one into a chat,
a repo, or a template — the Hermes repo is public and a key that reached it once
had to be rotated.

## Behavioural rules

- **Tailscale only.** No Funnel, no public bind. Non-tailnet traffic to `:8642`
  and `:8645` is dropped on the Hermes host.
- **Do not write into Hermes memory plugins** (Hindsight, LCM, Graphiti, Omega)
  without an explicit memory plan agreed with the human.
- **Understand what a call does:** the Hermes terminal backend is `local`
  (unsandboxed), so agent work dispatched through this endpoint runs as the host
  user with full terminal and file access. Treat every call as production.
- **Confine each identity bot in its system prompt** — account-wide MCP tools are
  visible to all of a user's Grok Bots.
- Prefer `hermes -z` for a single question; use the API when you want parallel
  asks or lower overhead.

## What changed recently on the Hermes side

- A publicly-exposed OmniRoute key was **rotated and deleted**; scripts read
  `OMNIROUTE_API_KEY` from the environment now, no key literals in the repo.
- The API server was enabled on the tailnet address only, and the firewall was
  tightened to drop non-tailnet traffic.
- The Hermes repo tree was cleaned and is in sync; merges are handled by Hermes.

## Health checks that actually mean something

Use `/health` and `/api/*` — **not** `/v1/models`. On the neighbouring OmniRoute
router `/v1/models` answers 200 for *any* key (including garbage), so it proves
nothing. On Hermes `:8642` auth is enforced properly (401 without a key), but keep
the habit of probing `/health` first.

## Model tiers — pick the right one per task

Hermes is configured so that **real work is advanced and loops/small jobs are free**:

| Task | Model | How you ask for it |
|---|---|---|
| Anything that matters (analysis, code, decisions, research) | `deepseek/deepseek-v4.1-flash` | it is the **default** — just call normally |
| Tiny tasks, polling, summaries, loops, high-volume chatter | `upstage/solar-pro4:free` (free) | via the relay, pass the flag (below) |

Through the **API** (`:8642`) every call runs the profile default, which is
`deepseek/deepseek-v4.1-flash` — so your delegated work already gets the advanced
model with no extra work on your side.

Through the **SSH relay** you can choose per call, so a small job costs nothing:

```bash
ssh ubuntu@100.101.211.44 'hermes -z "summarise this" -m "upstage/solar-pro4:free"'
```

Both paths are verified live: the free flag returns a real completion, and the API
reports `deepseek/deepseek-v4.1-flash via provider nous`.

**Two rules that will save you from silent failures:**

- Never pin **Super Grok** (`grok-4.6` / provider `xai-oauth`) on a loop or a
  subagent. It is a scarce weekly budget reserved for chat and Grok Imagine media.
  All Hermes cron jobs now run on the free tier.
- Prefer `upstage/solar-pro4:free` for automated loops. `stepfun/step-3.7-flash:free`
  and several other free slugs are **reasoning** models: under a small `max_tokens`
  they spend the whole budget thinking and return `content: null`, which a loop
  reads as an empty answer rather than an error.
- Free slugs rot without notice. Re-check the live `/models` list before pinning one.
