# Verification gates

The static checks every code change must pass locally before commit.

This list is seeded by the scaffold; this project owns the file and is expected to add the gates that apply
to its own tech stack.

1. `uv run --cache-dir .tmp/uv-cache --with ruff -- ruff check tools/` — exits clean.
2. `bash -n tools/*.sh` — exits clean.
3. `tools/markdown.sh check` — every tracked or untracked-but-not-ignored Markdown file is formatting-clean:
   table columns aligned by display width, source line wrapping preserved (see [`markdown.md`](markdown.md)).
   Run `tools/markdown.sh fmt` to fix. The script needs Node and `npx` on `PATH`.
