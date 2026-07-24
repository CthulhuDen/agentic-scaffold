#!/usr/bin/env bash
# Codex SessionStart hook wrapper for sync-agents.
#
# Runs `tools/sync-agents.py --check`. On success: exit 0, no output, codex continues.
# Otherwise: emit JSON {continue:false, stopReason, systemMessage} so codex halts the
# session. The check's own stderr is not surfaced to the operator, so the instruction comes
# from the status alone: 3 (EXIT_DRIFT) says regenerate, anything else says read the error.
# See the EXIT_* constants in tools/sync-agents.py for why drift owns 3.
#
# See https://developers.openai.com/codex/hooks for the hook output schema.

set -uo pipefail

readonly EXIT_DRIFT=3 # tools/sync-agents.py

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
common_git_dir=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || exit 0
cache_dir="$(dirname "$common_git_dir")/.tmp/uv-cache"

cd "$repo_root" || exit 0
mkdir -p "$cache_dir" || exit 0

# Without uv neither the check nor the remedy the halt message names can run, so degrade to a
# no-op, as with the missing-checkout cases above.
command -v uv >/dev/null 2>&1 || exit 0

uv run --cache-dir "$cache_dir" --script tools/sync-agents.py --check >/dev/null 2>&1
status=$?

case $status in
0)
  exit 0
  ;;
"$EXIT_DRIFT")
  cat <<'JSON'
{"continue":false,"stopReason":"sync-agents check failed — generated agent files are out of date","systemMessage":"`.codex/agents/` and `.opencode/agents/` are out of date relative to `.claude/agents/`.\n\nRegenerate with:\n\n    tools/sync-agents.py\n\nThen restart this codex session."}
JSON
  ;;
*)
  cat <<'JSON'
{"continue":false,"stopReason":"sync-agents check failed — a .claude/agents/ definition is invalid, or the check could not run","systemMessage":"`tools/sync-agents.py --check` failed with an error instead of reporting drift, so regenerating will not help.\n\nSee the error with:\n\n    tools/sync-agents.py --check\n\nFix what it reports, then restart this codex session."}
JSON
  ;;
esac
