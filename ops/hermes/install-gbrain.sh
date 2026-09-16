#!/usr/bin/env bash
# Install GBrain for a supported IDE on macOS/Linux (goalworld repo).
#
#   install-gbrain.sh                    # cursor (default, historical behaviour)
#   install-gbrain.sh --ide cursor
#   install-gbrain.sh --ide antigravity
#
# install-gbrain-cursor.sh / install-gbrain-antigravity.sh are thin shims
# kept for existing docs, cron entries and runbooks.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GBRAIN_IDE="${GBRAIN_IDE:-cursor}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ide) GBRAIN_IDE="${2:-}"; shift 2 ;;
    --ide=*) GBRAIN_IDE="${1#*=}"; shift ;;
    -h|--help)
      sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

case "${GBRAIN_IDE}" in
  cursor|antigravity) ;;
  *) echo "ERROR: --ide must be cursor or antigravity (got '${GBRAIN_IDE}')" >&2; exit 2 ;;
esac

# shellcheck source=lib/gbrain-install-common.sh
source "${REPO_ROOT}/ops/hermes/lib/gbrain-install-common.sh"

gbrain_install_main "$@"
