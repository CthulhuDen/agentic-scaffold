---
name: policy-editor
description: >-
  ALWAYS invoke this skill before declaring a code or documentation change complete. NEVER finish an edit
  without invoking this skill.
---

Invoke the `policy` skill as well before you continue, if you haven't already.

## Keep specs compact

Specs are ownership contracts for humans, not implementation tours. After any edit that touches `SPEC.md` or
`specs/*.md`, run this pass before either hand-off:

- before replying to the user that the change is applied, done, or ready;
- before invoking the reviewer subagent.

The pass:

1. Re-read every spec hunk you produced this session.
2. Re-read [`policy/doc-quality.md`](../../../policy/doc-quality.md).
3. Walk each paragraph in the hunks applying the rules from the doc above; for every clause choose one: keep
   it, delete it, move it into a table (static facts — API surfaces, named members, fixed values, payload
   shapes, invariants, branch summaries), or move it into a chart (sequence-dependent behaviour — state
   mutations, audit emissions, control-flow). Default to deletion when uncertain.

## Always verify your work before considering a change complete.

Project-defined verification commands and pass criteria are in
[`policy/verification-gates.md`](../../../policy/verification-gates.md). The inspection step below applies on top.

### Run IDE inspections on every changed file.

When the JetBrains IDE MCP is exposed in this session, run `get_file_problems` with `errorsOnly: false` on
every file you touched before declaring the task complete. The schema is registered as a _deferred_ tool, so you must
use your harness's tool search to load its schema before you can call it. If a reported "build problem" is contradicted
by a clean local build, the IDE's index is stale — re-sync the project (or the affected module) and re-run the
inspection against a current index.

**Before every reply that follows a file edit, run `get_file_problems` on each file you touched.**
