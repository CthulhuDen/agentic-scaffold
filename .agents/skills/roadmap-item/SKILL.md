---
name: roadmap-item
description: >-
  Invoke this skill when the user asks to "do the next roadmap item", "run roadmap iteration N", or any
  equivalent phrasing.
---

# Roadmap iteration executor

You orchestrate one `ROADMAP.md` iteration: initial implement → review-and-fix loop → commit. Always run
subagents in the background — pass `run_in_background: true`.

Invoke the `roadmap` skill before step 1.

## 1. Pick the iteration, set the budget

From the user's request, determine:

- **Iteration number.** If they named one (e.g. "iteration 3", "the next one"), use that. Otherwise read
  `ROADMAP.md` and pick the lowest-numbered `in-progress` iteration (resuming an aborted prior run); failing
  that, the lowest `pending` one.
- **Fix-loop budget.** If they specified one (e.g. "5 fix rounds", "max 20 retries"), use it. Otherwise default
  to `10`.

If the chosen iteration's status is `done`, halt and tell the user. If no iterations are `pending` or
`in-progress`, tell the user and stop.

## 2. Implement

Run the implementer subagent (replace `<N>` with the iteration number):

> Implement Iteration `<N>` from `ROADMAP.md`. Invoke the `roadmap` skill for the rules before you continue.
> If the iteration's status is already `in-progress`, this is a resume of an aborted prior run — inspect the
> working tree and any existing `### Plan adjustments` / `### Follow-ups` entries to pick up where it left off.
>
> Do not commit and do not run code review yourself. Verification gates apply as usual.
> When finished, flip the iteration's status in `ROADMAP.md` to `done`.
>
> ## Response format
>
> Reply with these sections, in order:
>
> 1. `## Summary` — one line on what changed.
> 2. `## Suggested commit message` — fenced code block, repo style (`git log --oneline -10`).
> 3. `## Notes` — anything the orchestrator should know.

## 3. Review-and-fix loop

Initialize `fix_round = 0`. Each iteration of the loop:

Run `git status --short`. If the tree is clean, halt — the implementer reported success but produced no diff.

Check the status of the current iteration in `ROADMAP.md`: if it's not `done`, halt — the implementer reported
success but did not follow the roadmap protocol.

Run the `reviewer` subagent:

> SCOPE: HEAD
>
> REQUIREMENTS: The change is the implementation of Iteration `<N>` from `ROADMAP.md`:
>
>> <verbatim: heading, SPEC references, `### Scope`, and `### Acceptance` — these only>
>
> The status flip to `done` and any `### Plan adjustments` or `### Follow-ups` subsections on the iteration's
> entry in `ROADMAP.md` are expected artifacts of this work, not scope creep.

On any verdict other than `approve for hand-off`, flip the `**Status:**` back from `done` to `in-progress` first
so a later resume picks the iteration up correctly. Then act on the verdict:

- `approve for hand-off` → exit the loop, go to step 4.
- `request changes` → if `fix_round >= budget`, halt: list the unresolved findings and ask the user how to
  proceed. Do NOT commit. Otherwise run a fresh implementer subagent with the fix prompt below, increment
  `fix_round`, and continue the loop.
- Anything else / unparseable → halt and ask the user.

**Fix prompt:**

> Continue Iteration `<N>` of `ROADMAP.md`. Invoke the `roadmap` skill for the rules before you continue.
> The reviewer returned `request changes` with the findings below; address every blocking and should-fix.
> Nit findings should be addressed as well unless you disagree on merit.
>
> Do not commit and do not run code review yourself. Verification gates apply as usual.
> When finished, flip the iteration's status in `ROADMAP.md` to `done`.
>
> ## Findings
>
> <verbatim: Findings section from reviewer>
>
> ## Response format
>
> Reply with these sections, in order:
>
> 1. `## Summary` — one line on what changed in this fix round.
> 2. `## Findings response` — for each reviewer finding, `🟢 [DONE]` (addressed) or `⚪ [SKIP]` (skipped);
>    name the judgment for non-mechanical fixes and the reason for skips.
> 3. `## Suggested commit message` — fenced code block, repo style (`git log --oneline -10`); reflect the final
>    state of all the iteration's work, not just this fix round.
> 4. `## Notes` — anything the orchestrator should know.

## 4. Commit

Use the implementer's `## Suggested commit message` verbatim. If your harness configures a commit-message
trailer (e.g., `Co-Authored-By:`), append it. Stage everything in the working tree and commit.

Don't push. Don't delete `ROADMAP.md` even if all iterations are now `done`. Report the new commit SHA and stop.
Don't chain into the next iteration unless the user asked you to.

## Reporting back

After each reviewer run, list the findings to the user as short bullets and close with the verdict on one line.
After every implementer run (initial or fix round), surface a 1–2 sentence extract from its `## Notes` section
if it has anything the user should see; for fix rounds, also relay the per-finding outcomes from its
`## Findings response`. Source everything from the implementer's reply, not the diff.

## Notes

- Don't skim the diff yourself; the reviewer reads the tree directly.
- For multiple iterations in one request, repeat the skill sequentially (not in parallel — overlapping files).
