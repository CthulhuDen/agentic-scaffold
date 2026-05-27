---
name: review
description: >-
  ALWAYS invoke this skill before every git commit; when the user asks to run the reviewer subagent for a one-off
  review (e.g. "run the reviewer") or when the user asks to run the review loop. NEVER commit any changes before
  invoking this skill. Do not invoke this skill for a simple review request without mentioning the loop or the
  reviewer subagent, unless the user also asked to commit. NEVER invoke this skill if you are the reviewer subagent.
---

<SUBAGENT-STOP>
If you are the reviewer subagent, stop and do not follow this skill.
</SUBAGENT-STOP>

## `reviewer` subagent

Independent reviewer that verifies code and docs against `policy/` and `SPEC.md` / `specs/`. **You must respect
its contract** regarding the arguments and only pass SCOPE and optional REQUIREMENTS, and never attempt to steer
its behaviour (e.g. "Check such and such feature I just implemented. Do not pay attention to the changes to docs...").

## Loop

Mandatory before every commit, unless the user explicitly requested to skip the review before commit. If the user
asked to run the review loop but did not ask to commit — do not commit after the review loop is finished.

Invoke with SCOPE=`HEAD` (full uncommitted working tree). Loop on `blocking` and
`should-fix` findings until the verdict is `approve for hand-off` (issued only when none remain); `nit` should be
fixed as well, but you can ignore them when disagreeing on the merits or when `nit`s are the only findings.
The implementing agent does not stand in for the reviewer in any form — not by reading its own diff, not by judging
the gates have nothing to find, not by deciding the change is too small. The loop ends only when the most recent
reviewer run on the current working tree returned `approve for hand-off`. Any edit after that verdict — including
fixes applied in response to `nit` findings — invalidates the approval and requires another reviewer iteration
before the loop can close.

### Circuit-breaker

If the implementing agent cannot satisfy the reviewer — five fix attempts fail to reach `approve for hand-off`,
the agent disagrees with a finding on the merits, or the requested fix is out of scope for the current task —
halt the loop, _do not_ commit, and _do not_ declare the task complete. The five-attempt budget is the default;
the user may raise or lower it. Return control to the user with: (a) the latest reviewer report quoted verbatim,
(b) the list of findings that remain unresolved, and (c) for each one, a concrete reason why the implementing
agent did not (or could not) apply a fix.

## One-off invocation

When the user asks for a review without committing (e.g., "run the reviewer"), invoke the subagent once
on the current uncommitted tree and report findings without entering the loop. Do not apply any fixes on a one-off
review — only present the reviewer's findings.

## Background execution

When the user requests a review (one-off or loop), launch the `reviewer` subagent in the background and then
immediately return control to the user. **Do not use your harness's tools to wait for the result**, unless the user
explicitly requests it.

For user-requested review loops, each iteration also runs in the background. Start the reviewer, return control
and continue the loop only after the reviewer's results arrive or the user explicitly asks you to resume/wait.

## Reporting back

After every reviewer run — one-off or loop iteration — list the findings to the user as short bullets and close
with the verdict on one line. If you applied fixes in response, tag each finding `🟢 [DONE]` (addressed; name
the judgment for non-mechanical fixes) or `⚪ [SKIP]` (skipped; state why). Circuit-breaker exits follow
[Circuit-breaker](#circuit-breaker) instead.
