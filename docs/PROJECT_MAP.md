# PROJECT MAP — where everything lives

**Read this before touching anything.** It is the map of record: repos, server
paths, backups, and how work actually gets merged. If reality disagrees with this
file, fix the file.

Last verified: 2026-09-16.

---

## 1. How work gets merged (the GitHub truth)

**PR merging on GitHub works and costs nothing.** PRs and `gh pr merge` are free
on a public repo, and this repo is public. What is unavailable is **GitHub
Actions (CI)** — the account is locked for a billing issue, so workflows die
immediately with *"The job was not started because your account is locked due to
a billing issue."*

The consequences, stated plainly:

| Thing | Status |
|---|---|
| Open / review / merge PRs on GitHub | **Works, free.** This is how we merge. |
| GitHub Actions (CI, tests, lint gates) | **Dead.** Billing lock. Assume nothing runs automatically. |
| GitHub Pages | Still deploys on push, independently of the CI failure. |

So we did **not** move to "merging on the server". We merge **on GitHub**; the
server is where the **verification** happens, because CI no longer does it. That
is the whole reason every PR here carries its own evidence.

### The merge lifecycle (canonical: `docs/MERGE_POLICY.md`)

1. `gh pr view <n>` → `mergeable=MERGEABLE` + `mergeStateStatus=CLEAN`
2. Own review of the exact diff, including a **secret scan** (and note: secret
   redaction masks credentials in tool output, so a grep can lie — measure the
   raw value)
3. **Area build, on the PR tip**: `cargo check -p goalworld_program` (underscore) ·
   `npx tsc --noEmit` · `bash -n` / `py_compile` / `node --check` for scripts
4. `gh pr merge <n> --squash` (history is linear; prior PRs were squashed)
5. **Verify on the base branch**, not the PR page: `git cat-file -e <base>:<path>`,
   `git diff --numstat` for the line delta
6. Delete the throwaway head branch

**Who merges:** Hermes (`default` or `hermes-ceo`). Nico keeps veto. Deploy or
upgrade to **mainnet** requires an explicit order from Nico — merging code does not.

### Forbidden

`git add -A` · `stash -u` · checkout over a dirty tree · merging a remote PR whose
diff no longer matches what was reviewed · patching contracts outside a dedicated PR.

---

## 2. Repos on the server

### Ours (origin = `TheNeuralWars`)

| Path | Branch | Role |
|---|---|---|
| `/data/apps/GoalWorld` | `feat/env-migration` | The product monorepo: webapp, contracts, sdk, api, oracle, ops, docs. **Main working repo.** Branches: `main` (stale, 2026-07-04), `mainnet-prep` (release), `feat/env-migration` (where work lands) |
| `/data/apps/GoalChain` | `main` | The Hub / publication side (goalworld.fun content, film pipeline, trading-sim) |
| `/data/apps/Lucas` | `main` | LukooFit (separate product) |

### Vendor clones — NOT ours, do not "fix" them

`Agent-Reach` (Panniantong) · `CloakBrowser` (CloakHQ) · `codebase-memory-mcp`
(DeusData) · `hermes-plugins` (42-evey) · `OmniVoice-Studio` and `VoiceStudio`
(debpalash). Their `origin` points at someone else's account. Treat as
dependencies: read, use, but never push or "tidy".

### Branch model

```
main              stale (2026-07-04). Do not target it.
mainnet-prep      release branch. Promotion from feat/env-migration needs Nico.
feat/env-migration  integration branch — all work lands here first.
```

---

## 3. Server layout outside the repos

| Path | What it is |
|---|---|
| `/data/apps/<name>` | The git repos above |
| `/data/hermes-home` | Hermes runtime for the **default** profile: `config.yaml`, `.env`, `auth.json`, `state.db`, `sessions/`, `logs/` |
| `/data/hermes-home/profiles/<name>` | Per-profile Hermes homes (10 profiles: hermes-ceo, dev, qa, money, trader, product, creative, research, social, default). **Each has its own config.yaml, .env, auth.json — settings do NOT propagate.** |
| `/data/hermes-home/skills` | Skills library (the repo's `skills/` mirrors it) |
| `/data/docker/volumes/omniroute-data/_data/storage.sqlite` | OmniRoute router DB (root-owned; hot-reloads combo edits, needs a container restart for **deletions** and cached API keys) |
| `/data/backups` | **The one place for backups.** See §4 |
| `/tmp` | Scratch only. Nothing here survives a reboot by design. |

### Services

- `hermes-gateway-hermes-ceo` (Discord/Telegram for this profile), plus `-social`,
  `-trader`. **Only one gateway per platform token.**
- `hermes-discord-gw-watchdog.timer` — every 5 min, defers a `try-restart` if Discord is unhealthy
- OmniRoute container (LLM router, `:20128`) · nginx/Caddy (`:80`/`:443`) · ttyd (`127.0.0.1:7681`)
- **Hermes API server on `:8642`** — OpenAI-compatible, bound to the tailnet IP only. This is what Grok Bot drives.

---

## 4. Backups

```
/data/backups/
  README.md    the retention rule
  configs/     Hermes config.yaml / .env backups
  goals/       *.bak-* moved out of the project repos
  scratch/     throwaway artefacts, safe to delete
```

**Rule: backups never live inside a repo tree.** They show as untracked noise and
can be swept into a commit by `git add -A`. Move them here instead.

Two large historical items sit there and are **not** needed to run anything —
delete only with Nico's explicit OK:

- `goalworld-audit-20260816/` — **5.5 GB** (a 3.9 GB copy of `hermes` plus tarballs) from an August audit
- `profiles-pre-free-20260816.tar.gz` — 261 MB

---

## 5. Known open disorder (measured 2026-09-16)

| Item | State | Action |
|---|---|---|
| `GoalWorld` | clean, in sync, on `feat/env-migration` | none — this is the healthy reference |
| `GoalChain` | **176 dirty** (150 untracked, most under `docs/publishing`), 3 unpushed commits, `.git` = **2.3 GB** | triage the dirty set, push the 3, then compact |
| `GoalChain` commit msgs | one commit message contains a literal `\n\n` — an automated job stuffed a newline into the subject | fix when rewriting that history |
| `GoalWorld/.git` | 502 MB, ~500 MB of it is history (4 copies of the PressKit zip, videos, two `codebase.db` versions) | needs a `filter-repo` rewrite — Nico's call |
| `Lucas`, vendor clones | 1–2 dirty files each | ignore; not our work |

---

## 6. From where to continue

1. **Product code** → `/data/apps/GoalWorld`, branch `feat/env-migration`. Branch
   off it, PR back into it, verify locally (no CI), merge with `gh pr merge --squash`.
2. **Hub / content / film** → `/data/apps/GoalChain`. Triage its dirty tree first —
   it is the least tidy repo and the easiest place to lose work.
3. **Runtime config** (models, platforms, credentials) → the per-profile
   `config.yaml` + `.env` under `/data/hermes-home/profiles/<name>/`.
4. **Router / models** → OmniRoute DB or its API at `127.0.0.1:20128`.
5. **Machine-to-machine** → Grok Bot drives Hermes over `:8642` (API) or SSH relay.
   See `ops/grokbot-bridge/BRIEFING_FOR_GROKBOT.md`.