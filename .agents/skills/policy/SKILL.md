---
name: policy
description: >-
  ALWAYS invoke this skill before doing any work in the project, including answering the user's question; writing,
  editing, reading, debugging or reviewing any code or documentation; researching code structure or behaviour;
  planning implementation of a new feature. NEVER go straight to the code without first invoking this skill.
---

## Read SPEC.md and policy/README.md before doing any work.

[`SPEC.md`](../../../SPEC.md) (with the per-component specs under [`specs/`](../../../specs)) is authoritative
for product and feature decisions; [`policy/README.md`](../../../policy/README.md) is the index of the project's
governance rules. When in doubt about a technical decision, the answer is in SPEC; when in doubt about a convention
or a gate, the answer is in `policy/`. If the answer is not in either place, update the relevant document first; do not
invent rules from training-data instinct.

## Apply policy/code-quality.md before writing, editing, or reviewing code.

Load [`policy/code-quality.md`](../../../policy/code-quality.md) before you write, edit, or review any code; every rule
it states is binding.

## Apply policy/doc-quality.md and policy/markdown.md + policy/charts.md to every documentation change or review.

Load [`policy/doc-quality.md`](../../../policy/doc-quality.md) and [`policy/markdown.md`](../../../policy/markdown.md) +
[`policy/charts.md`](../../../policy/charts.md) before you write, edit, or review any documentation; every rule they
state is binding.

## Delete scratch files before declaring a task complete.

If you create a file during a task for research or exploratory purposes, delete it before considering the task
complete, unless it lands in a directory that is already gitignored.

## Invoke `tools/*` directly, not through an interpreter, and from the repository root.

Tools under `tools/` carry shebangs that handle their own runtime and resolve paths relative to cwd.

## Keep bash invocations to the simplest form that works.

The user approves bash commands by their shape, so every needless variation forces another approval, and unusual
shell constructs trigger expansion-based approval prompts. Specifically:

- For exit codes, append exactly `; echo "exit=$?"` — never label variants (`check_exit`, `fix_exit`, etc.).
  Each call already has its own output block.
- Avoid shell expansions beyond `$?` (e.g., `${PIPESTATUS[N]}`, `$(…)`).
