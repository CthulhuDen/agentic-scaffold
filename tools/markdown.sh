#!/usr/bin/env bash
# Check or reformat Markdown with dprint: aligns table columns by display width while
# preserving source line wrapping (unlike Prettier, dprint keeps a wrapped inline code
# span's continuation indented to the list-item content column).
#
# Usage:
#   tools/markdown.sh check [<file>...]   # report files that are not formatting-clean (exit nonzero)
#   tools/markdown.sh fmt [<file>...]     # reformat in place
#
# With no files, operates on every tracked or untracked-but-not-ignored *.md in the repo,
# excluding the CLAUDE.md symlink (its target AGENTS.md is covered on its own).
#
# Planning documents are never formatted (see policy/doc-quality.md): ROADMAP.md is dropped
# from the no-file sweep and skipped by name when passed explicitly, and explicitly passed
# gitignored files — where other planning documents live — are skipped as well.
set -euo pipefail

DPRINT_VERSION=0.54.0
MARKDOWN_PLUGIN=https://plugins.dprint.dev/markdown-0.17.8.wasm

usage() {
  echo "usage: $0 {check|fmt} [<file>...]" >&2
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

verb=$1
case "$verb" in
  check | fmt) ;;
  *)
    echo "error: unknown action '$verb' (expected check or fmt)" >&2
    usage
    exit 2
    ;;
esac
shift

cd "$(git rev-parse --show-toplevel)"

if [[ $# -gt 0 ]]; then
  files=()
  for f in "$@"; do
    if [[ "$f" == ROADMAP.md || "$f" == */ROADMAP.md ]]; then
      echo "skipping $f: planning documents are exempt from formatting" >&2
    elif git check-ignore -q -- "$f"; then
      echo "skipping $f: gitignored files are exempt from formatting" >&2
    else
      files+=("$f")
    fi
  done
else
  files=()
  while IFS= read -r -d '' f; do
    files+=("$f")
  done < <(git ls-files -z --cached --others --exclude-standard '*.md' ':!CLAUDE.md' ':!ROADMAP.md')
fi

if [[ ${#files[@]} -eq 0 ]]; then
  echo "no markdown files found" >&2
  exit 0
fi

exec npx --yes "dprint@$DPRINT_VERSION" "$verb" --plugins "$MARKDOWN_PLUGIN" -- "${files[@]}"
