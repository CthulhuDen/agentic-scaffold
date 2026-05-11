# Documentation quality

These rules apply to all documentation in this repository. Markdown mechanics live in
[`markdown.md`](markdown.md); code rules live in [`code-quality.md`](code-quality.md).

## IDE inspections

Documentation is free of errors and warnings reported by the project's IDE inspections.

## Agent-instruction documents

`AGENTS.md`, `.agents/*.md`, `.agents/skills/**/SKILL.md`, and `.claude/agents/*.md` are system prompts whose
primary purpose is to steer LLM behavior. That purpose overrides this document's rules, which apply as
guidelines rather than requirements. Persona language, explicit anti-pattern callouts, and end-of-prompt
reinforcement are functional in a system prompt and are allowed even when they read as flourish or redundancy.

## Roadmap

`ROADMAP.md` is a temporary planning artifact deleted once its iterations are complete. The rules in this
document apply as guidelines, not requirements. Iteration entries may be terse to the point of telegraphic, may
quote audit findings or design notes verbatim, may carry change-narrative ("dropped because …", "previously
…"), and need not justify the absence of alternatives. The acceptance criteria still need to read clearly to a
fresh implementing agent — that is the only hard constraint.

## Specs

Behavior — what the system does, when, and under what conditions — is documented in the owning spec. A per-component
spec under `specs/` documents only the business its own code path owns. When a component depends on another,
link to the owner's spec.

`SPEC.md` is the only file that describes the system end-to-end.

## Constraint integrity

Edits to specs (`SPEC.md`, `specs/*.md`) and policy (`policy/*.md`) must stand on their own merits, independent
of any code modified alongside them. The test:

> *Would this edit make sense if the implementation it accompanies weren't being made?*

Edits that fail this test are constraint-weakening and are rejected, even when each file passes its linter and
the post-edit spec agrees with the code.

Examples of constraint-weakening:

- a rule dropped or relaxed (`must` → `should`, `never` → `usually`, a `requires` clause removed);
- an `Out of scope` item silently removed (now in scope without acceptance text);
- acceptance criteria narrowed mid-iteration to match what the code happens to produce;
- an invariant the code cannot otherwise express, removed or paraphrased weaker;
- a previously-named failure mode dropped from a "Failure modes" section.

## Content

Documentation describes present-state behavior. The test for every sentence: *would a future reader who
arrived without context about why it was written still read it as a description of the system as it is?*

- **Default to terse.** If a particular detail or a whole sentence can be deleted without changing the meaning,
  delete it.
- **Voice.** Behavior is described in the present indicative ("the runner emits …"). Rules and obligations use
  the imperative ("link to the owner's spec"). Agent-instruction documents address the agent in the second
  person. Avoid first person.
- **No alternatives-defense narrative.** Don't document choices the system didn't make ("otherwise …",
  "rather than X") — except when the clause names an invariant or refactor pitfall the code can't express.
- **No redundant negatives.** "X does not affect Y" is already implied when the positive description of X is
  exhaustive — drop it. State a negative only when the positive form leaves it open whether Y is in scope.
  Exception: `Out of scope` sections, where absence *is* the rule.
- **No editorial flourishes**, such as `simply`, `intended as`, or `is just as important as`.
- **No change-narrative.** `now includes`, `rewritten to`, `previously …` — documentation is timeless.
- **No workflow rules in content.** Exception: agent-instruction documents.
- **Don't anchor general rules to specific instances.** When a rule applies broadly, state it broadly. (E.g., write
  "external tools validate their response shape" rather than naming a specific tool.) Naming a particular instance
  is justified only when (a) a generic term would genuinely mislead, (b) the instance is the irreducible reference
  and has no generic form, or (c) the rule is a workaround for a quirk of that instance, and the name must stay
  so the workaround can be dropped when the quirk is fixed.
- **No meta about the document.** Don't describe its audience, lifecycle, structure, or purpose ("this guide
  is for X", "rarely changes", "the sections below ..."). Describe the subject. (E.g., `code-quality.md`
  describes the requirements, not the reviewer or agent that enforces them.)

## Catalog references

A catalog is a list whose source of truth is a single document. When a link targets a catalog, the surrounding
prose must explain what *kind* of thing the catalog holds but not duplicate the catalog's items. If you need to
highlight a subset, link to its members directly rather than naming them inside the catalog link.
