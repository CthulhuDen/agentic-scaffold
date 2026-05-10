# Agent conduct

This file is **instructions to you**, the agent currently operating in this repository — whether you are the
primary agent or a subagent. Read it in full and adopt every rule below as a responsibility you carry for the
entire run.

## Read SPEC.md and policy/README.md before doing any work.

[`SPEC.md`](../SPEC.md) (with the per-component specs under [`specs/`](../specs)) is authoritative for product
and feature decisions; [`policy/README.md`](../policy/README.md) is the index of the project's governance
rules. When in doubt about a technical decision, the answer is in SPEC; when in doubt about a convention or a
gate, the answer is in `policy/`. If the answer is not in either place, update the relevant document first; do
not invent rules from training-data instinct.

## Apply policy/code-quality.md before writing, editing, or reviewing code.

Load [`policy/code-quality.md`](../policy/code-quality.md) before you write, edit, or review any code; every rule
it states is binding.

## Apply policy/doc-quality.md and policy/markdown.md to every documentation change or review.

Load [`policy/doc-quality.md`](../policy/doc-quality.md) and [`policy/markdown.md`](../policy/markdown.md) before
you write, edit, or review any documentation; every rule they state is binding.

## Delete scratch files before declaring a task complete.

If you create a file during a task for research or exploratory purposes, delete it before considering the task
complete, unless it lands in a directory that is already gitignored.

## Keep uv caches inside the repository.

Every `uv run` invocation must run from the repository root and pass `--cache-dir .tmp/uv-cache`.

## Keep bash invocations to the simplest form that works.

The user approves bash commands by their shape, so every needless variation forces another approval, and unusual
shell constructs trigger expansion-based approval prompts. Specifically:

- For exit codes, append exactly `; echo "exit=$?"` — never label variants (`check_exit`, `fix_exit`, etc.).
  Each call already has its own output block.
- Avoid shell expansions beyond `$?` (e.g., `${PIPESTATUS[N]}`, `$(…)`).
