#!/usr/bin/env bash
# Shim: GBrain installer for Cursor. Logic lives in install-gbrain.sh.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install-gbrain.sh" --ide cursor "$@"
