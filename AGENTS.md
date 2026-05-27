<!-- These instructions live in `AGENTS.md` at the repository root; `CLAUDE.md` is a symlink to that file. -->

Do not modify files in response to questions or comments. When you notice a possible change in that context, explain it
and suggest the edit instead. Only edit files when the user explicitly asks to apply, fix, patch, change, write, or
commit.

## SPEC-Driven Workflow

1. **Plan before building.** For any non-trivial change:
   - Read the relevant `SPEC` sections.
   - Draft a plan (what files change, what the expected outcome is), researching the codebase as needed to inform it.
   - Only then begin making changes.

2. **Keep artifacts in sync.** After completing work, immediately update:
   - `SPEC.md` (and `specs/*.md`) — if any product or feature decisions evolved during implementation.
