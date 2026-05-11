#!/usr/bin/env bash
# Sync this project's scaffold with the upstream agentic-scaffold repo.
#
# Usage:
#   tools/scaffold.sh push [<scaffold-path>]   # upstream local edits to the scaffold
#   tools/scaffold.sh pull [<scaffold-path>]   # pull scaffold updates into this project
set -euo pipefail

usage() {
  echo "usage: $0 {push|pull} [<scaffold-path>]" >&2
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 2
fi

action=$1
client_path=$(git rev-parse --show-toplevel)

case "$action" in
  push) remote_action=pull ;;
  pull) remote_action=push ;;
  *)
    echo "error: unknown action '$action' (expected push or pull)" >&2
    exit 2
    ;;
esac

last_scaffold_path_file="$client_path/.tmp/agentic-scaffold-path"
if [[ $# -eq 2 ]]; then
  scaffold_path=$2
else
  if [[ ! -f "$last_scaffold_path_file" ]]; then
    echo "error: scaffold path not specified and $last_scaffold_path_file does not exist" >&2
    usage
    exit 2
  fi
  IFS= read -r scaffold_path < "$last_scaffold_path_file" || true
  if [[ -z "$scaffold_path" ]]; then
    echo "error: $last_scaffold_path_file is empty" >&2
    exit 2
  fi
fi

cd "$scaffold_path"
exec tools/scaffold-sync.py "$remote_action" "$client_path"
