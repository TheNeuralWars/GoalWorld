#!/usr/bin/env bash
# Shim: hermes-ceo flavoured task creation. Logic lives in create-task.sh.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/create-task.sh" --source ceo "$@"
