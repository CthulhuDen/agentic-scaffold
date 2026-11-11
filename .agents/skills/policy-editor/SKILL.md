---
name: policy-editor
description: >-
  ALWAYS invoke this skill before declaring your first code or documentation change of the session complete. NEVER
  finish an edit without having invoked it. One invocation is enough: once its content is in context, do not invoke
  it again.
---

Invoke the `policy` skill as well before you continue, if you haven't already.

## Apply the project-specific editor rules in project.md before declaring a change complete.

[`project.md`](project.md) in this skill's directory carries editor rules specific to this project; every rule it
states is binding.

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

## Verify spec hunks against code

A spec hunk that reads well can still misstate the code, and a new member of an enumerated kind is easily added to one
table and missed in another. After any edit that touches `SPEC.md`, `specs/*.md`, or code those specs describe, run
this pass at the same two hand-off points as the compactness pass:

1. For every chart node in the spec hunks you produced this session, open the code it describes and confirm the
   operation exists on that path, in that order, with that effect. For an `audit:` or `log:` node, confirm the event
   name and level at the emit site.
2. For every table row in the hunks that states a code-level fact — a signal, a reason or detail value, a phase, a
   message key, an order of steps — confirm it against the code the same way.
3. Sibling sweep: when the change adds a member of a kind the specs already enumerate — a terminal path, an outcome,
   a reason or signal value, a documented residual, a phase — grep `SPEC.md` and `specs/` for the names of its
   existing siblings and add the new member to every table and chart that lists them. Name the grep in the hand-off
   message.
4. After editing a table, re-read the whole table and the table that follows it, then run the verification gates. An
   edit that matched a neighbouring table's divider row is a known failure.
5. Reverse direction: for every code hunk that adds, removes, or moves an audit event, a state write, or an externally
   visible effect, name the chart that owns it and confirm you edited that chart in this session (see
   [Charts in sync with code](../../../policy/doc-quality.md#specs)).

## Mutation-check new tests

Before either hand-off — before replying to the user that the change is applied, done, or ready, and before invoking the
reviewer subagent — apply the [mutation check](../../../policy/testing.md#mutation-check) to each behavioural test you
added: make the plausible regression it describes, confirm the test fails, revert it, and name the mutation in the
hand-off message.

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
