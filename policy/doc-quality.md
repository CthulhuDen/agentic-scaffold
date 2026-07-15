# Documentation quality

These rules apply to all documentation in this repository. Markdown mechanics live in
[`markdown.md`](markdown.md); code rules live in [`code-quality.md`](code-quality.md).

## IDE inspections

Documentation is free of errors and warnings reported by the project's IDE inspections.

## Agent-instruction documents

[`AGENTS.md`](../AGENTS.md), `.agents/skills/**/SKILL.md`, `.agents/skills/**/project.md`, `.claude/agents/*.md`,
and the engine-prompt `*.md` assets embedded under `internal/` are system prompts whose primary purpose is to
steer LLM behavior. That purpose overrides this document's rules,
which apply as guidelines rather than requirements. Persona language, explicit anti-pattern callouts, and
end-of-prompt reinforcement are functional in a system prompt and are allowed even when they read as flourish or
redundancy.

## Planning documents

`ROADMAP.md` and any other temporary planning document — one drafted to plan or track work in progress and
deleted when that work completes, never maintained as a description of the system — is not documentation. No
rule in this document, in [`markdown.md`](markdown.md), or in [`charts.md`](charts.md) applies to a planning
document, and none may be cited against one in authoring or review. Detail is the point of a plan: research
findings, file and line anchors, exact signatures and command sequences, verbatim design notes, change-narrative,
and long unwrapped lines all belong in one. `ROADMAP.md` is the only planning document kept in tracked space —
`tools/markdown.sh` excludes it by name (see [`verification-gates.md`](verification-gates.md)); every other
planning document lives at a gitignored path, which the Markdown gate's file selection already excludes. The
only content requirements for `ROADMAP.md` are the `roadmap` skill's own.

## Specs

Specs are ownership contracts, not implementation tours. A component spec documents only the externally visible
behavior the component owns, its ownership boundaries, emitted audit events, audit-context availability, and its public
code API, configuration, schema, or storage surface. Internal helper ordering, local variable mechanics, and defensive
explanation stay out unless they change one of those contracts.

Behavior — what the system does, when, and under what conditions — is documented in the owning spec. A per-component
spec under `specs/` documents only the business its own code path owns. When a component depends on another,
link to the owner's spec.

Specs stay small enough for direct human maintenance. Prefer deletion over restatement. Remove duplicated prose,
historical explanation, examples that do not define a contract, and implementation detail that is not externally
visible.

[`SPEC.md`](../SPEC.md) is the only file that describes the system end-to-end.

**Orchestration specs.** A spec that documents an end-to-end flow may be designated an exception to the
per-component scope rule: it describes the surface-level flow from intake to terminal output, including the behavior
of the components it coordinates, and serves as [`SPEC.md`](../SPEC.md)'s delegate for per-surface narrative.
Cross-component invariants the orchestrator depends on still link to the owner's spec for detail.

**Temporal behavior.** Use charts for ordered behavior when state mutation, context-field availability, audit-context
availability, audit events, or externally visible effects depend on sequence. The chart shows the mutation or emission
point. Tables are the required form for static contracts, API surfaces, fixed values, payload shapes, ownership
invariants, and branch summaries. Prose paragraphs that state two or more such facts are a doc-quality defect and
rejected at review — convert them to a table row each. Two or more named members of the same kind — methods of a
surface, helpers, predicates, fields of a payload, error shapes, event names — go in a table; a single member may
stay inline.

**Charts in sync with code.** Any code edit that adds, removes, or relocates an audit event, runtime log, state
mutation, externally visible effect, or sequencing decision requires updating the owning chart in the same edit. A
diff that touches these surfaces in code and leaves the owning chart unchanged is incomplete and rejected at review.
This obligation is the chart-specific case of [`code-quality.md`](code-quality.md)'s scope rule (b).

## Constraint integrity

Edits to specs ([`SPEC.md`](../SPEC.md), `specs/*.md`) and policy (`policy/*.md`) must stand on their own merits,
independent of any code modified alongside them. The test:

> _Would this edit make sense if the implementation it accompanies weren't being made?_

Edits that fail this test are constraint-weakening and are rejected, even when each file passes its linter and
the post-edit spec agrees with the code.

Examples of constraint-weakening:

- a rule dropped or relaxed (`must` → `should`, `never` → `usually`, a `requires` clause removed);
- an `Out of scope` item silently removed (now in scope without acceptance text);
- acceptance criteria narrowed mid-iteration to match what the code happens to produce;
- an invariant the code cannot otherwise express, removed or paraphrased weaker;
- a previously-named failure mode dropped from a "Failure modes" section.

## Content

Documentation describes present-state behavior. The test for every sentence: _would a future reader who
arrived without context about why it was written still read it as a description of the system as it is?_

- **Default to terse.** If a particular detail or a whole sentence can be deleted without changing the meaning,
  delete it.
- **Voice.** Behavior is described in the present indicative ("the runner emits …"). Rules and obligations use
  the imperative ("link to the owner's spec"). Agent-instruction documents address the agent in the second
  person. Avoid first person.
- **No alternatives-defense narrative.** Don't document choices the system didn't make ("otherwise …",
  "rather than X") — except when the clause names an invariant or refactor pitfall the code can't express.
- **No redundant negatives.** "X does not affect Y" is already implied when the positive description of X is
  exhaustive — drop it. State a negative only when the positive form leaves it open whether Y is in scope.
  Exception: `Out of scope` sections, where absence _is_ the rule.
- **No restatement of adjacent charts.** When a chart shows a state mutation, an audit event, a runtime log, or a
  control-flow continuation, prose around the chart names the chart's entry and handoffs, not the steps the chart
  already shows. "Cleanup still runs after failure", "audit fires before reply", and "on success continue to X" are
  chart edges, not chart commentary.
- **No prose paragraphs for static invariants.** If a paragraph would consist of sentences like "X owns Y",
  "duplicates are allowed", "the runner records nothing directly", convert it to a one-row table per invariant.
  Prose adjacent to a chart is restricted to entry/handoff naming, per the rule above.
- **No restatement of cross-cutting policy.** Conventions owned by [`policy/`](.) and [`SPEC.md`](../SPEC.md) are
  referenced by link, not paraphrased. Audit-event level, universal audit fields, runtime-log levels, markdown
  wrapping, and chart shape live in their owners; a per-component spec does not repeat them.
- **No editorial flourishes**, such as `simply`, `intended as`, or `is just as important as`.
- **No change-narrative.** `now includes`, `rewritten to`, `previously …` — documentation is timeless.
- **No project-process rules in specs.** Specs describe behavior and owned contracts, not how contributors edit,
  review, or implement them. Operator-facing docs may include setup and runtime commands. Agent-instruction documents
  may include agent workflow rules.
- **Don't anchor general rules to specific instances.** When a rule applies broadly, state it broadly. (E.g., write
  "external tools validate their response shape" rather than naming a specific tool.) Naming a particular instance
  is justified only when (a) a generic term would genuinely mislead, (b) the instance is the irreducible reference
  and has no generic form, or (c) the rule is a workaround for a quirk of that instance, and the name must stay
  so the workaround can be dropped when the quirk is fixed.
- **No meta about the document.** Don't describe its audience, lifecycle, structure, or purpose ("this guide
  is for X", "rarely changes", "the sections below ..."). Describe the subject. (E.g.,
  [`code-quality.md`](code-quality.md)
  describes the requirements, not the reviewer or agent that enforces them.)

## Catalog references

A catalog is a list whose source of truth is a single document. When a link targets a catalog, the surrounding
prose must explain what _kind_ of thing the catalog holds but not duplicate the catalog's items. If you need to
highlight a subset, link to its members directly rather than naming them inside the catalog link.
