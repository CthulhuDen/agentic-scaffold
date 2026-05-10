---
name: roadmap
description: >-
  Rules for creating, maintaining, and executing iterations in `ROADMAP.md`. Load whenever you create, read, or edit
  `ROADMAP.md`, when you start work on a roadmap iteration, or before invoking the `roadmap-item` skill.
---

# Working with ROADMAP.md

## When to use a roadmap

`ROADMAP.md` is reserved for large, multi-step projects (e.g. initial template adaptation, major feature
additions) that benefit from explicit iteration planning. It may not always be present in the repository. Simple,
self-contained changes — a CI tweak, a config update, a bug fix — do not need a roadmap entry; a git commit message
is sufficient. When a roadmap exists for the current effort, consult it before starting work and never jump ahead
or work on multiple iterations simultaneously.

## Iteration shape

Each iteration has: a number, a title, a status (`pending` / `in-progress` / `done`), SPEC section references,
a scope description, and acceptance criteria. Completed iterations may also carry optional `### Plan adjustments`
and `### Follow-ups` subsections.

Each iteration must be independently verifiable. An iteration should leave the project in a buildable, testable
state. Do not introduce changes that depend on incomplete future iterations.

## Status updates

Mark iterations as `done` immediately upon completion — do not batch status updates. The status flip is the final
edit of an iteration's work; everything else (including any Plan adjustments and Follow-ups subsections) must be
in place first, so an aborted run does not leave behind a misleading `done`.

## Editing scope and acceptance

Do not edit the `### Scope` or `### Acceptance` of an iteration once work on it has begun. Those sections preserve
the plan as it was authored and are read in retrospect to understand what was intended. When implementation reveals
that the plan needs adjusting, do not rewrite history — record the change instead:

- **Adjustments to the current step.** Append a `### Plan adjustments` subsection to the current iteration. Each
  entry names what changed relative to the original scope/acceptance and why (e.g. an artifact rename forced by
  upstream tooling, a step that turned out to be redundant, a smaller substitute chosen for a planned deliverable).
  The original scope and acceptance text stay intact.
- **Adjustments that affect future steps.** Future iterations are still in the planning state, so edit their
  `### Scope` / `### Acceptance` directly. Also record the cross-cutting change under the current step's
  `### Plan adjustments` so the trail is visible from where it was discovered.

Concerns surfaced during a step that did not change its outcome — a risk to re-check during a later iteration, an
open question about behavior that worked but might shift, follow-up work explicitly deferred — go under a
`### Follow-ups` subsection on the current iteration. Follow-ups are pointers, not unfinished business; the
acceptance criteria still need to be met before the iteration is marked `done`.

## Iteration ordering

Do not reorder completed iterations. New iterations may be inserted if scope is discovered during implementation.

## Lifecycle

When all iterations are complete, delete `ROADMAP.md` from the repository. A roadmap is a living planning document,
not an archive. Historical context is preserved in git history.

## Cross-references

Never reference `ROADMAP.md` (or specific iterations within it) from source code, KDoc, JavaDoc, inline comments,
or [`SPEC.md`](../../../SPEC.md). The roadmap is not a permanent member of the codebase — it is deleted once its
iterations are complete, which would leave dangling references behind. Code comments must be self-contained: explain
the constraint or decision in place rather than pointing at the planning document that authored it. If a rationale
is important enough to preserve long-term, it belongs in [`SPEC.md`](../../../SPEC.md).
