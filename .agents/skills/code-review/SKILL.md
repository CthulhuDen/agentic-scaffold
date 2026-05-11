---
name: code-review
description: >-
  Procedure for invoking the code-reviewer subagent on uncommitted changes. Load this skill BEFORE every git
  commit, when the user asks to run the code-reviewer subagent for a one-off review (e.g. "run the review",
  "review what I have"), or when the user asks to run the review loop. Specifies the invocation contract,
  the loop and three-attempt circuit-breaker, one-off mode (no fixes applied), and background-execution
  defaults.
---

# `code-reviewer` subagent

Independent reviewer that verifies code and docs against `policy/` and `SPEC.md`. The implementing agent invokes
it before each commit; the user may also invoke it on demand for a one-off review or to run the loop to prepare
a changeset for commit.

When the user requests a review without explicitly asking to commit afterward, do not commit.

## Loop

Mandatory before every commit. Invoke with SCOPE=`HEAD` (full uncommitted working tree). Loop on `blocking` and
`should-fix` findings until the verdict is `approve for hand-off` (issued only when none remain); `nit` may be
deferred. No exemptions: doc-only, cosmetic, "obviously safe" — all trigger the loop. The implementing agent
does not stand in for the reviewer in any form — not by reading its own diff, not by judging the gates have
nothing to find, not by deciding the change is too small. Approval applies only to the exact working-tree state
inspected; any subsequent edit invalidates it.

## Circuit-breaker

If the implementing agent cannot satisfy the reviewer — three fix attempts fail to reach `approve for hand-off`,
the agent disagrees with a finding on the merits, or the requested fix is out of scope for the current task —
halt the loop, *do not* commit, and *do not* declare the task complete. The three-attempt budget is the default;
the user may raise or lower it. Return control to the user with: (a) the latest reviewer report quoted verbatim,
(b) the list of findings that remain unresolved, and (c) for each one, a concrete reason why the implementing
agent did not (or could not) apply a fix. Silent give-ups, partial commits that skip unresolved findings, or
paraphrased summaries of the report in place of the verbatim report are all violations of this rule.

## One-off invocation

When the user asks for a review without committing (e.g., "run the review", "review what I have"), invoke the
subagent once on the current uncommitted tree and report findings without entering the loop. Do not apply any
fixes on a one-off review — only present the reviewer's findings. The user requests fixes separately if they
want them.

## Background execution

When the user requests a review (one-off or loop), launch the `code-reviewer` subagent in the background and then
immediately return control to the user. Do **not** use your harness's tools to wait for the result, unless the user
explicitly requests it. Once the subagent's results arrive, summarize/report them normally.

For user-requested review loops, each iteration also runs in the background. Start the reviewer, return control
and continue the loop only after the reviewer's results arrive or the user explicitly asks you to resume/wait.
