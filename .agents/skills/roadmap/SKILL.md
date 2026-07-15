---
name: roadmap
description: >-
  ALWAYS invoke this skill when user asks to create a roadmap or to start or continue working on a roadmap; or before
  invoking the `roadmap-item` skill. NEVER create/edit/follow the `ROADMAP.md` without first invoking this skill.
---

# Working with ROADMAP.md

## When to use a roadmap

`ROADMAP.md` plans large, multi-step efforts as numbered iterations; simple, self-contained changes don't need
one, and a roadmap may not be present in the repository at all. When a roadmap exists, consult it before starting
work, do not jump ahead, and work on at most one iteration at a time.

## Formatting and documentation policy

`ROADMAP.md` is a planning document, not repository documentation. It is exempt from
[`policy/doc-quality.md`](../../../policy/doc-quality.md), [`policy/markdown.md`](../../../policy/markdown.md),
and [`policy/charts.md`](../../../policy/charts.md), and [`tools/markdown.sh`](../../../tools/markdown.sh) skips
it. Never condense, reformat, restyle, or line-wrap roadmap content to satisfy those conventions — detail is the
roadmap's purpose. Research findings, file and line anchors, exact signatures, command sequences, verbatim
design notes, and long lines all belong here.

## Iteration shape

Each iteration carries a number, a title, a status (`pending` / `in-progress` / `done`), SPEC section references,
`### Scope`, and `### Acceptance`. Optional `### Plan adjustments` and `### Follow-ups` subsections are populated
as work progresses and freeze with the rest when the iteration is marked `done`.

Each iteration must be independently verifiable and must leave the project buildable and testable. Do not
introduce changes that depend on incomplete future iterations.

Acceptance criteria must read clearly to a fresh implementing agent.

## Status flow

`pending` → `in-progress` → `done`. The implementer makes both flips:

- `pending` → `in-progress` as the first edit when work starts (a no-op on a resumed run).
- `in-progress` → `done` as the final edit, after Plan adjustments, Follow-ups, downstream-reference sweeps,
  and every other change are in place — an aborted run must not leave a misleading `done` behind.

## What the implementer may edit

Once an iteration is `in-progress`:

- **Current iteration's `### Scope` / `### Acceptance`:** frozen — preserve the plan as authored. When
  implementation reveals a needed adjustment, append a `### Plan adjustments` entry naming what changed and why.
- **Current iteration's `### Plan adjustments` / `### Follow-ups`:** working records — add, revise, or remove
  entries as implementation evolves. If a later step or review finding contradicts an earlier entry, update or
  delete that entry rather than refusing the fix.
- **Future iterations' `### Scope` / `### Acceptance`:** edit directly — they are still in planning. Note any
  cross-cutting change under the current iteration's `### Plan adjustments` so the trail is visible from where
  it was discovered.
- **Completed (`done`) iterations:** frozen entirely — do not edit or reorder them.

Follow-ups are pointers, not unfinished business — acceptance criteria still need to be met before `done`.

## Downstream references

Before marking the iteration `done`, sweep later iterations for references the current work invalidated
(shifted SPEC section numbers, renamed artifacts, moved files) and update them in place. Purely mechanical
reference updates do not need a `### Plan adjustments` entry.

## Lifecycle

When all iterations are `done`, delete `ROADMAP.md` from the repository in a standalone commit — separate
from the commit that closes the last iteration, so that the closing commit records the last iteration's
final Plan adjustments and Follow-ups with the file still in place.

## Cross-references

Never reference `ROADMAP.md` (or specific iterations within it) from source code or its comments, or
[`SPEC.md`](../../../SPEC.md) / [`specs/`](../../../specs). The roadmap is deleted once its iterations are complete,
which would leave dangling references behind. Rationale important enough to preserve long-term belongs in the
specifications.
