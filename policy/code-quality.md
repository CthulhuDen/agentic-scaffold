# Code quality

These rules apply to all code in this repository. Documentation rules live in [`doc-quality.md`](doc-quality.md).

## Verification gates

Code changes pass the repository's verification gates. The concrete commands and pass criteria are defined in
[`verification-gates.md`](verification-gates.md).

## IDE inspections

Code is free of errors and warnings reported by the project's IDE inspections.

## Best practices

- **Names reveal intent.** A reader can tell from the name what the named thing is or does.
- **One responsibility per unit.** Functions, types, and packages each have a single reason to change.
- **Shallow nesting.** Guard clauses with early returns are preferred over deep `if`/`else` pyramids.
- **Comments capture why, not what.** Well-named code conveys what it does. Comments record rationale,
  invariants, or constraints the code shape can't express.
- **No SPEC paraphrasing in code.** When behavior is owned by `SPEC.md` or a per-component spec, a comment
  links to that section (`// See specs/runner.md §7.`) instead of restating it — paraphrase drifts out of sync.
  Inline `// Step N` / `// (a)` headings that mirror the SPEC's pipeline step numbers or bullet labels are
  redundant: link once, then let the code speak.
- **No dead code.** Unused symbols, parameters, and commented-out blocks are removed. Version control preserves
  history.
- **State-machine defaults are explicit.** Enum-like values that drive control flow have a deliberate zero value:
  either a named zero state (`…None`, `…Unknown`) the code accounts for, or no state at zero at all (`iota + 1`).
  Functions returning decision structs set the state field on every control-flow return; callers never rely on an
  all-zero struct to mean success, continue, or handled. Switches over such states handle the named expected states
  explicitly, so reordering or removing a constant cannot silently re-map one onto the zero value.
- **Constants, not magic values.** Non-obvious literals (timeouts, buffer sizes, sentinels) are named.
- **No premature abstraction.** An abstraction is introduced only when a concrete duplication has emerged and
  its shape is clear.
- **No speculative code.** Features, error branches, and configuration knobs each serve a present caller.
- **Validation at trust boundaries.** Untrusted input — CLI args, network payloads, file contents, subprocess
  output, environment variables — is validated where it enters. Past that boundary, internal callers are trusted.
- **Errors propagate until handled.** An error is wrapped for context and propagated until some layer can decide
  what to do. The interface boundary (CLI, HTTP handler, top of `main`) is the terminal handler.

## Established patterns

Code follows the patterns established by surrounding code — same file first, then neighboring files. Deviations
need explicit justification.

## Scope of changes

When making a change to address a specific task, the change set contains the edits the task calls for, plus only
extras of these kinds:

- **(a)** a mechanical consequence of the requested change (e.g., an import path updating with a renamed symbol);
- **(b)** an edit mandated by a rule the requested change forces into play (e.g., a SPEC update describing the new
  behavior);
- **(c)** a documentation improvement;
- **(d)** a bridge over a pre-existing gap between specs and implementation;
- **(e)** a fix for a pre-existing policy violation.

Categories (c)–(e) are encouraged. Drift between specs, code, and policies erodes the project's coherence.

Anything else — unrelated refactors, tangential cleanups, "while I was here" fixes — is scope creep.
An "out of scope" disclaimer in the change description does not exempt an edit.
