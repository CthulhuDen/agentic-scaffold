# agentic-scaffold

A portable AI-agentic workflow scaffold for software projects: a SPEC-driven governance layer, subagent
definitions for three harnesses (Claude Code, Codex, OpenCode), and the tooling that keeps them in lockstep.

See [`SPEC.md`](SPEC.md) for what the scaffold installs and how sync between scaffold and client works.

## Prerequisites

- `uv` — `tools/sync-agents.py` and `tools/scaffold-sync.py` are uv-script shebangs, and the SessionStart
  hooks for Codex and OpenCode invoke `tools/sync-agents.py --check` on each session start.

## Installing into a project

From the scaffold repo:

```sh
tools/scaffold-sync.py push /path/to/your-project
```

This writes managed files into the project, seeds stub files only if absent, installs the scaffold's
`.gitignore` block, and stamps `.agentic-scaffold-revision` with the scaffold's `HEAD` SHA. Then in the
project:

```sh
tools/sync-agents.py
```

to materialize the Codex/OpenCode agent files.

## Updating an existing project

From the project:

```sh
tools/scaffold.sh pull /path/to/agentic-scaffold
```

`scaffold.sh` cd's to the scaffold and invokes `scaffold-sync.py push <client>` there. Both sides must be
clean in managed paths; the client side must additionally be clean in `.agentic-scaffold-revision` and
`.gitignore`.

When the recorded revision is not an ancestor of the scaffold's current `HEAD` — typically because the client
pushed edits that the maintainer hasn't merged yet — pushing scaffold updates into the client would overwrite
the client's unmerged work. In that case the script warns and asks for confirmation before proceeding.

## Upstreaming local edits

From the project, after editing scaffold-canonical files in place:

```sh
tools/scaffold.sh push /path/to/agentic-scaffold
```

This invokes `scaffold-sync.py pull` in the scaffold. It reads the SHA recorded in the project's
`.agentic-scaffold-revision` and chooses between a fast path and an incoming-branch fallback.

**Fast path.** When the recorded SHA equals local scaffold `main` and `main@{upstream}` is an ancestor of
`main`, or it equals `main@{upstream}` and local `main` is an ancestor of `main@{upstream}`, the script
commits the project's managed-file edits directly on `main` and stamps `.agentic-scaffold-revision` with the
new commit. In the second case, `main` is fast-forwarded to the recorded SHA first.

**Incoming-branch fallback.** Otherwise the script checks out an `incoming/<client>-<ts>` branch from the
recorded commit, copies the project's managed files onto it, commits, and prints the merge command for the
maintainer to run by hand.
