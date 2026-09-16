#!/usr/bin/env bash
# Shim: canonical credential maintenance lives in scripts/hermes-credential-maintain.sh.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts/hermes-credential-maintain.sh" "$@"