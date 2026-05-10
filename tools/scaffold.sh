#!/usr/bin/env bash
# Sync this project's scaffold with the upstream agentic-scaffold repo.
#
# Usage:
#   tools/scaffold.sh push <scaffold-path>   # upstream local edits to the scaffold
#   tools/scaffold.sh pull <scaffold-path>   # pull scaffold updates into this project
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 {push|pull} <scaffold-path>" >&2
  exit 2
fi

action=$1
scaffold_path=$2
client_path=$(git rev-parse --show-toplevel)

case "$action" in
  push) remote_action=pull ;;
  pull) remote_action=push ;;
  *)
    echo "error: unknown action '$action' (expected push or pull)" >&2
    exit 2
    ;;
esac

cd "$scaffold_path"
exec tools/scaffold-sync.py "$remote_action" "$client_path"
