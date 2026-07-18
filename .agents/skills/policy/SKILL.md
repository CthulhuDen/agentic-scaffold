---
name: policy
description: >-
  ALWAYS invoke this skill before your first work in the session, including answering the user's question; writing,
  editing, reading, debugging or reviewing any code or documentation; researching code structure or behaviour;
  planning implementation of a new feature; running any subagent. NEVER go straight to the code without having
  invoked it. One invocation is enough: once its content is in context, do not invoke it again.
---

## Read SPEC.md and policy/README.md before doing any work.

[`SPEC.md`](../../../SPEC.md) (with the per-component specs under [`specs/`](../../../specs)) is authoritative
for product and feature decisions; [`policy/README.md`](../../../policy/README.md) is the index of the project's
governance rules. When in doubt about a technical decision, the answer is in SPEC; when in doubt about a convention
or a gate, the answer is in `policy/`. If the answer is not in either place, update the relevant document first; do not
invent rules from training-data instinct.

## Apply the project-specific general rules in project.md before doing any work.

[`project.md`](project.md) in this skill's directory carries general rules specific to this project; every rule it
states is binding.

## Apply policy/code-quality.md before writing, editing, or reviewing code.

Load [`policy/code-quality.md`](../../../policy/code-quality.md) before you write, edit, or review any code; every rule
it states is binding.

## Apply policy/doc-quality.md and policy/markdown.md + policy/charts.md to every documentation change or review.

Load [`policy/doc-quality.md`](../../../policy/doc-quality.md) and [`policy/markdown.md`](../../../policy/markdown.md) +
[`policy/charts.md`](../../../policy/charts.md) before you write, edit, or review any documentation; every rule they
state is binding.

## Never judge a planning document by the documentation or formatting policies.

`ROADMAP.md` and any other temporary planning document — drafted to plan or track work in progress, deleted when
done — are exempt from [`policy/doc-quality.md`](../../../policy/doc-quality.md),
[`policy/markdown.md`](../../../policy/markdown.md), and [`policy/charts.md`](../../../policy/charts.md). Do not
apply those rules to one, do not reformat it, and do not run `tools/markdown.sh` against it — the script skips
`ROADMAP.md` on its own. See [`Planning documents`](../../../policy/doc-quality.md#planning-documents).

## Delete scratch files before declaring a task complete.

If you create a file during a task for research or exploratory purposes, delete it before considering the task
complete, unless it lands in a directory that is already gitignored.

## Invoke `tools/*` directly, not through an interpreter, and from the repository root.

Tools under `tools/` carry shebangs that handle their own runtime and resolve paths relative to cwd.

## Keep bash invocations to the simplest form that works.

The user approves bash commands by their shape, so every needless variation forces another approval, and unusual
shell constructs trigger expansion-based approval prompts. Specifically:

- Avoid shell expansions beyond `$?` (e.g., `${PIPESTATUS[N]}`, `$(…)`).
- Run `git` and other tools from the repository root without `-C <path>` or a `cd` prefix — the working directory
  already is the repository root and persists between calls, and an explicit path changes the command's shape so it
  no longer matches the user's pre-approved rules.
