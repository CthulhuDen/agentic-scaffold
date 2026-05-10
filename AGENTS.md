<!-- These instructions live in `AGENTS.md` at the repository root; `CLAUDE.md` is a symlink to that file. -->

**Your first action this session is to read [`.agents/conduct.md`](.agents/conduct.md) and
[`.agents/implementer.md`](.agents/implementer.md) in full**. The rules in those files are standing obligations
for the rest of the run; treat every one as binding from that point on.

Do not modify files in response to questions or comments. When you notice a possible change in that context, explain it
and suggest the edit instead. Only edit files when the user explicitly asks to apply, fix, patch, change, write, or
commit.

## SPEC-Driven Workflow

1. **Roadmap for large efforts.** Multi-step projects use `ROADMAP.md` for explicit iteration planning; simple,
   self-contained changes do not. When `ROADMAP.md` is in play, the [`roadmap`](.agents/skills/roadmap/SKILL.md)
   skill owns every rule about creating, editing, and executing iterations — load it before reading or writing
   the file.

2. **Plan before building.** For any non-trivial change:
   - Read the relevant `SPEC` sections.
   - Read the relevant ROADMAP iteration (if one exists for this work).
   - Draft a plan (what files change, what the expected outcome is), researching the codebase as needed to inform it.
   - Only then begin making changes.

3. **Keep artifacts in sync.** After completing work, immediately update:
   - `ROADMAP.md` — mark the iteration as complete (if the work corresponds to a roadmap iteration).
   - `SPEC.md` (and `specs/*.md`) — if any product or feature decisions evolved during implementation.
