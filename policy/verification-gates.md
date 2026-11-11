# Verification gates

The checks every code change must pass locally before commit.

1. `uv run --cache-dir .tmp/uv-cache --with ruff -- ruff check tools/ tests/` — exits clean.
2. `bash -n tools/*.sh` — exits clean.
3. `tools/markdown.sh check` — every tracked or untracked-but-not-ignored Markdown file except `ROADMAP.md` is
   formatting-clean: table columns aligned by display width, source line wrapping preserved, and no line over the
   120-character cap outside code blocks, tables, and lines carrying a URL (see [`markdown.md`](markdown.md)). Planning
   documents are exempt (see [`doc-quality.md`](doc-quality.md#planning-documents)): the script skips `ROADMAP.md` by
   name even when it is passed explicitly, and skips explicitly passed gitignored files — where every other planning
   document lives — the same way. Run `tools/markdown.sh fmt` to fix alignment; it lists over-cap lines but does not
   re-flow them. The script needs Node and `npx` on `PATH`.
4. `uv run --cache-dir .tmp/uv-cache --with pytest --with pyyaml -- pytest tests/` — exits clean.
