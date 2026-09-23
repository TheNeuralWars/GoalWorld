#!/usr/bin/env bash
# KDP commercial slice — chained task dispatch (audit 2026-09-10).
#
# Why: the audit (docs/intake/2026-09-10-deepseek-v41-commercial-audit-report.md) split the
# first-dollar work into 5 tasks. T1 (#877) and T2 (#878) are dispatched by hand. T3 depends on
# T2's *verdict* (which Book 1 tree is canonical), which lands in SOURCE_OF_TRUTH.md on main.
# This script watches main and dispatches T3 the moment that verdict exists — one task at a time,
# no human in the loop. It is idempotent: it creates T3 at most once and records the issue URL.
#
# Stage 1: wait for SOURCE_OF_TRUTH.md on origin/main  -> create T3 issue -> done.
# Stage 2: watch the T3 issue; when it closes, log "READY FOR T4/T5" (both need Nico's hands:
#          hiring a line editor, KDP dashboard) and stop.
#
# Manual run: bash /data/apps/GoalWorld/ops/hermes/audit-chain-dispatch.sh
set -euo pipefail

REPO_DIR="${GOALWORLD_REPO_PATH:-/data/apps/GoalWorld}"
# The publishing tree lives in the GoalChain repo (same remote that create-task.sh files to) —
# SOURCE_OF_TRUTH.md lands there, NOT in the GoalWorld repo. Keep the two dirs separate.
CODE_DIR="${GOALCHAIN_REPO_PATH:-/data/apps/GoalChain}"
GH_REPO="${GH_REPO:-TheNeuralWars/GoalChain}"
STATE_DIR="${HERMES_STATE_DIR:-$HOME/.hermes/state}"
LOG_DIR="${HERMES_LOG_DIR:-$HOME/.hermes/logs}"
STATE="$STATE_DIR/kdp-chain.json"
LOG="$LOG_DIR/kdp-chain.log"
SOT_PATH="docs/publishing/the_neural_wars_trilogy/BOOK_01_FRACTURED_CODE/SOURCE_OF_TRUTH.md"

mkdir -p "$STATE_DIR" "$LOG_DIR"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG"; }

# --- state helpers -----------------------------------------------------------
state_get() { # $1 = jq path, $2 = default
  if [[ -f "$STATE" ]]; then
    jq -r "${1} // empty" "$STATE" 2>/dev/null || true
  fi
}
state_set() { # $1 = key, $2 = value (string)
  local tmp; tmp="$(mktemp)"
  if [[ -f "$STATE" ]]; then
    jq --arg v "$2" ".$1 = \$v" "$STATE" >"$tmp" 2>/dev/null || echo "{\"$1\":\"$2\"}" >"$tmp"
  else
    echo "{\"$1\":\"$2\"}" >"$tmp"
  fi
  mv "$tmp" "$STATE"
}

T3_ISSUE="$(state_get .t3_issue)"
STAGE="$(state_get .stage)"

# --- stage 2: T3 closed -> hand off to Nico ----------------------------------
if [[ -n "$T3_ISSUE" ]]; then
  T3_STATE="$(gh issue view "$T3_ISSUE" --repo "$GH_REPO" --json state --jq .state 2>/dev/null || echo UNKNOWN)"
  if [[ "$T3_STATE" == "CLOSED" && "$STAGE" != "t3_done" ]]; then
    state_set stage t3_done
    log "T3 ($T3_ISSUE) closed. READY FOR T4/T5 — both need Nico: line editor hire + KDP dashboard."
    log "Handoff docs: $REPO_DIR/docs/intake/2026-09-10-T4-line-editor-brief.md and .../2026-09-10-T5-kdp-listing-runbook.md"
  elif [[ "$T3_STATE" == "OPEN" ]]; then
    log "stage 2: T3 ($T3_ISSUE) still open — nothing to do."
  fi
  exit 0
fi

# --- stage 1: wait for the T2 verdict on main --------------------------------
cd "$CODE_DIR"
git fetch --quiet origin main || { log "WARN: git fetch failed; retry next tick."; exit 0; }

if ! git show "origin/main:$SOT_PATH" >/dev/null 2>&1; then
  log "stage 1: waiting for $SOT_PATH on origin/main (T2 #878 not landed yet)."
  exit 0
fi

DECISION="$(git show "origin/main:$SOT_PATH" | head -60)"
if [[ -z "$DECISION" ]]; then
  log "stage 1: $SOT_PATH exists but is empty; refusing to dispatch T3 on an empty verdict."
  exit 0
fi

log "stage 1: T2 verdict detected on main. Dispatching T3."

OBJ="$(cat <<OBJEOF
## Why
Audit: \`docs/intake/2026-09-10-deepseek-v41-commercial-audit-report.md\` — task T3 of the 14-day cash plan.
T2 (#878) landed the canonical Book 1 verdict. This issue executes the surgical continuity list against
that verdict. T1 (#877) gated the free reader; this issue fixes the manuscript itself.

## Canonical verdict inherited from main (${SOT_PATH})
\`\`\`
${DECISION}
\`\`\`
If that block is ambiguous, STOP and ask Manager — do not guess which tree is canonical.

## Objective
Apply the 8-item surgical list from
\`docs/intake/2026-09-02-fractured-code-forensic-editorial-audit.md\` to the canonical tree(s) declared
above, as reviewable edits with per-file references:
1. One Martin thread (no dead -> ward -> rediscovered contradiction).
2. One Vance (rename the duplicate).
3. One frequency (432 or 528 Hz — never both).
4. EN dialogue punctuation: quotation marks, not Spanish em-dash transcription.
5. Kill English calques and translation tells on the canonical EN tree (e.g. "for three lustrums").
6. Cut the prologue's significance inflation; move the Gardeners frame to Book 2 if it is not earned.
7. Climax expansion on the canonical tree: >= 4,000 words, the Architect gets a rational scene,
   Mileo's erasures return as faces, Kora pays an irreversible cost.
8. Strip inline production beat tags (\`[Cosmic]\`, \`[Reflection]\`, \`[Action]\`, any \`[Tag]\`) from any
   tree destined for KDP export.

## META constraints
- Only the tree(s) declared canonical. Do not touch the non-canonical trees, the reader
  (\`docs/go/reader/**\`, owned by #877), \`contracts/\`, APIs or webapps.
- No new chapters beyond the climax expansion. No god-rewrite. No new dependencies.
- Keep the Series Bible consistent; if a fix contradicts \`00_SERIES_BIBLE_AND_CANON/\`, update the bible
  in the same PR and say so.
- English-only for anything public.
- Branch \`exp/hermes-<issue-number>\`, DRAFT PR, no direct merge to \`main\`.

## Acceptance test (paste real output into the PR)
- \`grep -ric "lustrum" <canonical EN dir>\` == 0
- \`grep -rc "528" <canonical dirs>\` == 0 and \`grep -rc "432" <canonical dirs>\` == 0  (pick one, document which)
- \`grep -rocE "\\[(Cosmic|Reflection|Action)\\]" <canonical dirs>\` == 0
- exactly one character named Vance: \`grep -ric "vance" <canonical EN dir>\` matches the chosen name only
- climax chapter word count >= 4000: \`wc -w <canonical dir>/FC-15*\`
- a written continuity note (in the PR body or a \`CONTINUITY_NOTES.md\`) proving a single Martin thread with chapter references
- re-export still works: the \`docs/publishing/KDP_EXPORT.md\` command exits 0 after the edits

## Dependency
Depends on T2 (#878). Created automatically by \`ops/hermes/audit-chain-dispatch.sh\`.
OBJEOF
)"

ISSUE_URL="$(bash "$REPO_DIR/ops/hermes/create-task.sh" hermes P1 "[DRAFT] Book 1 surgical continuity pass (T3 of the 14-day KDP plan)" "$OBJ" | tee -a "$LOG" | grep -oE 'https://[^ ]+')"

if [[ -z "$ISSUE_URL" ]]; then
  log "ERROR: create-task.sh returned no issue URL. Not recording state."
  exit 1
fi

ISSUE_NUM="${ISSUE_URL##*/}"
state_set t3_issue "$ISSUE_NUM"
state_set stage t3_open
log "T3 dispatched: $ISSUE_URL"
