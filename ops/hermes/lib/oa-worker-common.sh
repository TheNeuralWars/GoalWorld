#!/usr/bin/env bash
# Shared OA worker helpers.
#
# Sourced by oa-worker.sh (single worker) and by
# oa-worker-autonomous-wrapper.sh (partitioned alpha..kappa workers).
# Never executed directly.
#
# Why this file exists: the two scripts each carried their own copy of these
# helpers. Four were byte-identical, three differed by a single line, and one
# copy had a regex bug (see parse_task_from_text). The genuinely divergent
# loop internals (consume_webhook_queue, pick_next_hermes_issue,
# process_hermes_issue, main_loop) deliberately stay in their own scripts.
#
# Requires these to be set before calling (the callers' preambles set them):
#   HERMES_HOME  REPO  STATE_DIR  LOG_DIR  GITHUB_REPO
# Optional:
#   WORKER_ID    set only by the partitioned wrapper. When set, log lines are
#                tagged with it and research publishing is restricted to alpha.

log() { printf '[%s]%s %s\n' "$(date -u '+%F %T UTC')" "${WORKER_ID:+ [${WORKER_ID}]}" "$*"; }

is_urgent_text() {
  local text="${1:-}"
  text="$(printf '%s' "${text}" | tr '[:upper:]' '[:lower:]')"
  [[ "${text}" == *"cambio urgente"* ]] || [[ "${text}" == *"policy:direct-main"* ]] || [[ "${text}" == *"bypass-review"* ]] || [[ "${text}" == *"bypass_review"* ]] || [[ "${text}" == *"auto-merge"* ]]
}

publish_research_updates() {
  # X-Scout owns ai-radar-* posts (hermes-x-scout.timer). Worker must not republish them.
  # Partitioned mode: only alpha publishes, so research posts are not duplicated.
  if [[ -n "${WORKER_ID:-}" && "${WORKER_ID}" != "alpha" ]]; then
    return 0
  fi
  if [[ "${OA_WORKER_PUBLISH_RESEARCH:-false}" != "true" ]]; then
    return 0
  fi
  if [[ "${OA_RESEARCH_PUBLISHER_ENABLED:-false}" != "true" ]]; then
    return 0
  fi
  if [[ -z "${DISCORD_RESEARCH_WEBHOOK_URL:-}" && ( -z "${DISCORD_TOKEN:-}" || -z "${DISCORD_RESEARCH_CHANNEL_ID:-}" ) ]]; then
    return 0
  fi
  [[ -f "${RESEARCH_PUBLISHER}" ]] || return 0
  local cooldown_file="${STATE_DIR}/research-discord-next-attempt.txt"
  local now
  now="$(date +%s)"
  if [[ -f "${cooldown_file}" ]]; then
    local retry_at
    retry_at="$(cat "${cooldown_file}" 2>/dev/null || echo 0)"
    if [[ "${retry_at}" =~ ^[0-9]+$ ]] && (( now < retry_at )); then
      return 0
    fi
  fi
  python3 "${RESEARCH_PUBLISHER}" \
    --state-file "${STATE_DIR}/research-discord-posted.json" \
    --max-per-run 1 \
    --exclude-glob "ai-radar-*.md" \
    >> "${LOG_DIR}/worker.log" 2>&1 || {
      echo "$(( now + 7200 ))" > "${cooldown_file}"
      return 0
    }
  rm -f "${cooldown_file}"
}

ensure_branch_clean() {
  git -C "${REPO}" fetch origin -q || true
}

create_issue_from_webhook() {
  local owner="$1"
  local priority="$2"
  local title="$3"
  local objective="$4"
  local out issue_url
  out="$(bash "${HERMES_HOME}/scripts/create-task.sh" "${owner}" "${priority}" "${title}" "${objective}" 2>&1 || true)"
  issue_url="$(python3 -c 'import re,sys
t=sys.stdin.read()
m=re.findall(r"https://github\.com/[^\s]+/issues/\d+", t)
print(m[-1] if m else "")' <<< "${out}")"
  if [[ -z "${issue_url}" ]]; then
    log "WARN create-task failed for owner=${owner}: ${out}"
    return 1
  fi
  echo "${issue_url}"
}

agent_command_for_owner() {
  case "${1:-}" in
    cursor) printf '%s' "${OA_AGENT_CURSOR_CMD}" ;;
    antigravity) printf '%s' "${OA_AGENT_ANTIGRAVITY_CMD}" ;;
    grok) printf '%s' "${OA_AGENT_GROK_CMD}" ;;
    hermes) printf '%s' "${OA_AGENT_HERMES_CMD}" ;;
    *) printf '' ;;
  esac
}

ensure_issue_labels() {
  gh label create "status:in_progress" --repo "${GITHUB_REPO}" --color "fbca04" --description "Task is running" >/dev/null 2>&1 || true
}

dispatch_issue_to_waiting_agent() {
  local owner="$1"
  local priority="$2"
  local title="$3"
  local objective="$4"
  local issue_url="$5"
  local command issue_number issue_log worker_note=""

  command="$(agent_command_for_owner "${owner}")"
  [[ -n "${command}" ]] || return 0
  issue_number="${issue_url##*/}"
  issue_log="${LOG_DIR}/dispatch-${owner}-${issue_number}.log"
  [[ -n "${WORKER_ID:-}" ]] && worker_note=" (worker: ${WORKER_ID})"
  ensure_issue_labels
  gh issue edit --repo "${GITHUB_REPO}" "${issue_number}" --remove-label "status:ready" --add-label "status:in_progress" >/dev/null 2>&1 || true
  gh issue comment --repo "${GITHUB_REPO}" "${issue_number}" --body "Auto-dispatch: sent to waiting agent \`${owner}\` command runner${worker_note}." >/dev/null 2>&1 || true

  (
    export OA_TASK_OWNER="${owner}"
    export OA_TASK_PRIORITY="${priority}"
    export OA_TASK_TITLE="${title}"
    export OA_TASK_OBJECTIVE="${objective}"
    export OA_TASK_ISSUE_URL="${issue_url}"
    export OA_TASK_ISSUE_NUMBER="${issue_number}"
    export OA_TASK_REPO="${REPO}"
    bash -lc "${command}"
  ) >> "${issue_log}" 2>&1 &
  log "Auto-dispatched issue #${issue_number} to ${owner} wait-mode command"
}

parse_task_from_text() {
  local text="${1:-}"
  python3 -c 'import json,re,sys,unicodedata
text=(sys.argv[1] or "").strip()
if not text:
    print("")
    raise SystemExit(0)

def norm(s):
    s = s.lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))

n = norm(text)
owners = ["cursor","antigravity","hermes","grok"]

task = re.match(r"^task\s+(cursor|antigravity|hermes|grok)\s+(P0|P1|P2)\s+\"([^\"]+)\"\s+\"([^\"]+)\"$", text, flags=re.I)
assign = re.match(r"^assign\s+(cursor|antigravity|hermes|grok)\s+(P0|P1|P2)\s*\|\s*([^|]+)\s*\|\s*(.+)$", text, flags=re.I)
urgent = ("cambio urgente" in n) or ("policy:direct-main" in n) or ("urgente" in n)

if task:
    owner, priority, title, objective = task.groups()
    item = {"owner": owner.lower(), "priority": priority.upper(), "title": title.strip(), "objective": objective.strip()}
elif assign:
    owner, priority, title, objective = assign.groups()
    item = {"owner": owner.lower(), "priority": priority.upper(), "title": title.strip(), "objective": objective.strip()}
else:
    owner = next((o for o in owners if re.search(rf"\b{o}\b", n)), "hermes")
    has_exec_verb = any(v in n for v in ["spike", "integr", "implement", "elabora", "hace", "haz", "crear", "mejora"])
    priority = "P1" if has_exec_verb else "P2"
    title_words = re.sub(r"\s+", " ", text).strip().split(" ")
    title = " ".join(title_words[:10]).strip() or "OA task"
    if has_exec_verb:
        title = f"Spike: {title}"
    item = {"owner": owner, "priority": priority, "title": title, "objective": text}

if urgent:
    item["priority"] = "P0"
    if "CAMBIO URGENTE" not in item["title"]:
        item["title"] = f"[CAMBIO URGENTE] {item['title']}"
    item["objective"] = item["objective"] + "\n\nPolicy: direct main push requested by Nico via keyword cambio urgente."

print(json.dumps(item, ensure_ascii=True))
' "${text}"
}