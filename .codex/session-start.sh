#!/usr/bin/env bash
# Codex SessionStart hook wrapper for sync-agents.
#
# Runs `tools/sync-agents.py --check`. On success: exit 0, no output, codex continues.
# On drift: emit JSON {continue:false, stopReason, systemMessage} so codex halts the
# session with a clear instruction to regenerate.
#
# See https://developers.openai.com/codex/hooks for the hook output schema.

set -uo pipefail

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$repo_root" || exit 0

if tools/sync-agents.py --check >/dev/null 2>&1; then
  exit 0
fi

cat <<'JSON'
{"continue":false,"stopReason":"sync-agents check failed — generated agent files are out of date","systemMessage":"`.codex/agents/` and `.opencode/agents/` are out of date relative to `.claude/agents/`.\n\nRegenerate with:\n\n    tools/sync-agents.py\n\nThen restart this codex session."}
JSON
