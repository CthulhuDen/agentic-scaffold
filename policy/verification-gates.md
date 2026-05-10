# Verification gates

Define this project's verification gates here: the static checks every code change must pass locally before
commit, with the exact command to run and the pass criterion. Until they are defined, the implementer
subagent's "Always verify your work" rule and the code-reviewer's gate-running step have nothing to run.

Each entry has the shape:

> N. `<command>` — pass criterion.

Examples (replace with this project's actual gates):

- A formatter check that produces no diff.
- A linter or static-analysis run that exits clean.
- The unit-and-integration test suite under the race detector.
- A clean release build of the project's primary binaries.
