# Governance

The governance layer documents the rules every author of code, documentation, or change must follow. Rule
documents live under [`policy/`](../policy); [`policy/README.md`](../policy/README.md) indexes them.

## Application

Agents load the relevant policy file before performing the corresponding work:
[`code-quality.md`](../policy/code-quality.md) before writing or reviewing code,
[`doc-quality.md`](../policy/doc-quality.md) and [`markdown.md`](../policy/markdown.md) before writing or
reviewing documentation, and [`verification-gates.md`](../policy/verification-gates.md) to determine which
static checks every code change must pass before commit.

## Ownership

The scaffold owns the cross-project rule documents: [`code-quality.md`](../policy/code-quality.md),
[`doc-quality.md`](../policy/doc-quality.md), and [`markdown.md`](../policy/markdown.md). Push overwrites
them on every sync.

The client owns the project-specific files: [`policy/README.md`](../policy/README.md) (the index, since
the client may add policy documents the scaffold does not ship) and
[`policy/verification-gates.md`](../policy/verification-gates.md) (the concrete verification commands and
pass criteria for the client's tech stack). The scaffold seeds both as stubs on first install and never
overwrites them.
