---
name: roadmap-item
description: >-
  Execute a single `ROADMAP.md` iteration end-to-end: implementer subagent makes the change, code-reviewer reviews,
  fix loop runs until approval, then commit. Use when the user asks to "do the next roadmap item", "run roadmap
  iteration N", or any equivalent phrasing.
---

# Roadmap iteration executor

You orchestrate one `ROADMAP.md` iteration: initial implement → review-and-fix loop → commit. Always spawn
sub-agents with `run_in_background: true`.

Load the [`roadmap`](../roadmap/SKILL.md) skill — it owns the iteration rules this skill orchestrates.

## 1. Pick the iteration, set the budget

From the user's request, determine:

- **Iteration number.** If they named one (e.g. "iteration 3", "the next one"), use that. Otherwise read
  `ROADMAP.md` and pick the lowest-numbered iteration whose `**Status:**` line says `pending`.
- **Fix-loop budget.** If they specified one (e.g. "5 fix rounds", "max 20 retries"), use it. Otherwise default
  to `10`.

If the chosen iteration's status is not `pending`, halt and tell the user. If no iterations are `pending`, tell
the user and stop.

## 2. Implement

Spawn the `implementer` sub-agent (replace `<N>` with the iteration number):

> Implement Iteration `<N>` from `ROADMAP.md`. Load the `roadmap` skill for the rules.
>
> Reply with these sections, in order:
>
> 1. `## Summary` — one line on what changed.
> 2. `## Verification` — each gate command and its outcome (pass/fail); for IDE inspections, each file checked
>    via `get_file_problems` and the result. State preexisting/unrelated failures explicitly.
> 3. `## Suggested commit message` — fenced code block, repo style (`git log --oneline -10`).
> 4. `## Notes` — anything the orchestrator should know.

## 3. Review-and-fix loop

Initialize `fix_round = 0`. Each iteration of the loop:

Run `git status --short`. If the tree is clean, halt — the implementer reported success but produced no diff.

Spawn the `code-reviewer` sub-agent:

> SCOPE: HEAD
>
> REQUIREMENTS: The change is the implementation of Iteration `<N>` from `ROADMAP.md`:
>
> > <verbatim: heading, SPEC references, `### Scope`, and `### Acceptance` — these only>
>
> The implementer's edits to the iteration's entry in `ROADMAP.md` — the status flip from `pending` to `done`,
> plus any `### Plan adjustments` or `### Follow-ups` subsections appended per the `roadmap` skill — are
> expected artifacts of this work, not scope creep.

From the reviewer's verdict:

- `approve for hand-off` → exit the loop, go to step 4.
- `request changes` → if `fix_round >= budget`, halt: list the unresolved findings and ask the user how to
  proceed. Do NOT commit. Otherwise spawn the `implementer` with the fix prompt below, increment `fix_round`,
  and continue the loop.
- Anything else / unparseable → halt and ask the user.

**Fix prompt:**

> Continue Iteration `<N>` of `ROADMAP.md`. Load the `roadmap` skill for the rules. The reviewer returned
> `request changes` with the findings below; address every blocking and should-fix. Nit findings are at your
> discretion.
>
> ## Findings
>
> <verbatim: Findings section from reviewer>
>
> Reply with these sections, in order:
>
> 1. `## Summary` — one line on what changed in this fix round.
> 2. `## Verification` — each gate command and its outcome (pass/fail); for IDE inspections, each file checked
>    via `get_file_problems` and the result. State preexisting/unrelated failures explicitly.
> 3. `## Suggested commit message` — fenced code block, repo style (`git log --oneline -10`); reflect the final
>    state of all the iteration's work, not just this fix round.
> 4. `## Notes` — anything the orchestrator should know.

## 4. Commit

Use the implementer's `## Suggested commit message` verbatim. If your harness configures a commit-message
trailer (e.g., `Co-Authored-By:`), append it. Stage everything in the working tree (the implementer's edits
are the only changes expected) and commit:

```
git add -A
git commit -m "$(cat <<'EOF'
<suggested message verbatim>
EOF
)"
```

Don't push. Don't delete `ROADMAP.md` even if all iterations are now `done`. Report the new commit SHA and stop.
Don't chain into the next iteration unless the user asked you to.

## Notes

- Don't skim the diff yourself; the reviewer reads the tree directly.
- For multiple iterations in one request, repeat the skill sequentially (not in parallel — overlapping files).
