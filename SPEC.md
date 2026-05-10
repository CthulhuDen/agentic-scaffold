# SPEC

The agentic-scaffold installs a uniform agent-instruction and governance layer into a client project,
along with subagent definitions for multiple AI coding harnesses. The scaffold and each client are
independent git repositories; the sync system moves files between them on demand.

## Repository layout

| Path                     | Role                                                                                          |
|--------------------------|-----------------------------------------------------------------------------------------------|
| `AGENTS.md`              | Entry-point system prompt read by every harness on session start (`CLAUDE.md` symlinks to it) |
| `.agents/`               | Shared agent instructions (conduct, implementer responsibilities, skills)                     |
| `.claude/agents/*.md`    | Canonical subagent prompts                                                                    |
| `.codex/`, `.opencode/`  | Per-harness wiring; `agents/` is regenerated from `.claude/agents/`                           |
| `policy/`                | Governance rules consulted before writing code or docs                                        |
| `tools/scaffold-sync.py` | Bidirectional sync between scaffold and client (scaffold-only)                                |
| `tools/scaffold.sh`      | Client-side wrapper that invokes `scaffold-sync.py` in the scaffold                           |
| `tools/sync-agents.py`   | Regenerates Codex/OpenCode agent files from `.claude/agents/`                                 |
| `manifest.toml`          | Classification of every path the scaffold manages                                             |
| `specs/`                 | Per-component specs                                                                           |

## Tools convention

Every Python tool under `tools/` uses the uv-script shebang
`#!/usr/bin/env -S uv run --cache-dir .tmp/uv-cache --script`, declares its dependencies in the PEP 723
header, and is checked in with the executable bit set. The shebang's `--cache-dir` resolves relative to the
invocation cwd, so callers run tools from the repository root and uv's cache lands at `.tmp/uv-cache` inside
the repo.

## Layers

The scaffold has three concerns, each documented in its own component spec:

- **Behavior** — how the scaffold syncs files between itself and a client project, including the manifest,
  the sync tools, revision tracking, and gitignore-block management. Documented in
  [`specs/sync.md`](specs/sync.md). In-repo tools that the scaffold ships for use within a project are
  catalogued in [`specs/tools.md`](specs/tools.md).
- **Governance** — how code, documentation, and changes are written, tested, and reviewed. Documented in
  [`specs/governance.md`](specs/governance.md); the rule documents themselves live under
  [`policy/`](policy).
- **Agent conduct** — the standing obligations of the agent operating in the repository, plus the on-demand
  skills and subagent definitions agents invoke. Documented in [`specs/agents.md`](specs/agents.md); the
  rule documents themselves live in [`AGENTS.md`](AGENTS.md) and under [`.agents/`](.agents).

The scaffold seeds [`AGENTS.md`](AGENTS.md), [`policy/README.md`](policy/README.md), and
[`policy/verification-gates.md`](policy/verification-gates.md) once on first install and never overwrites
them. A client project authors its own `SPEC.md` and any `specs/*.md` for its components from scratch —
the scaffold ships no template. Everything else under `.agents/`, `.claude/agents/`, `.codex/`, `.opencode/`,
`policy/`, and `tools/` is managed by the scaffold, except `tools/scaffold-sync.py`, which lives only in the
scaffold.
