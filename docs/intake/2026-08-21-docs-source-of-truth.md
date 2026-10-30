# 2026-08-21 — marketing docs source of truth (GW-SRC-001)

## Decision

Pick **GoalChain/docs** as the only writable source for marketing HTML on `goalworld.fun`.

**Stop dual edits.** Do not sync GoalWorld/docs HTML to/from GoalChain. Freeze this repo's marketing HTML in place. Do not delete it.

## Evidence

- Live `GET https://goalworld.fun/` at 19:07 UTC = 7064 bytes, sha256 `e6097e8c73072f87…`, matched `/data/apps/GoalChain/docs/index.html`
- Same URL at 19:24 UTC still served that snapshot (`x-vercel-cache: HIT`)
- `/data/apps/GoalWorld/docs/index.html` did **not** match live at either check
- Almost every shared `*.html` had already diverged before this freeze
- GoalChain-only live pages at freeze time: `agents.html`, `arcade.html`, `protocol.html`, `tokenomics.html`, `mega-guide-v1.html`, plus `/go/{club,defi,estadio,goalworld}`
- GoalWorld-only pages (`studio.html`, `404.html`, `cinema.html`, `go/studio/`) are **not** on the live host
- Concurrent hotspot: GoalChain `index.html` was rewritten on disk during this run (7064 → 15529). That belongs on the next GoalChain deploy, not here.

## Policy

1. Edit marketing HTML only under `/data/apps/GoalChain/docs`.
2. Leave GoalWorld `docs/*.html`, `docs/go/`, `docs/play/`, marketing `docs/assets/`, `docs/vercel.json`, `docs/CNAME` untouched unless a later task archives them.
3. Keep writing operational docs in GoalWorld (`infrastructure/`, `intake/`, `ECONOMIC_CANONICAL_CONFIG.json`, `governance/`, `proposals/`, `kanban/`).
4. No automated mirror. A mirror would re-create drift.

## Pointer

`docs/README.md` is the freeze sign on this tree.
