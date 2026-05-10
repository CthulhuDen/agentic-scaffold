# Sync

The sync system moves managed files between the scaffold repository and a client project. Each client
records the scaffold commit its managed files were last reconciled against, so concurrent edits from multiple
clients diverge from a known common ancestor and produce real 3-way merges.

## Manifest

[`manifest.toml`](../manifest.toml) is the source of truth for which paths the scaffold owns and how each is
handled. Each entry has one of three classes:

- **managed** — the scaffold owns the file. Push overwrites it in the client; pull copies it back from the
  client into the scaffold.
- **stub** — the client owns the file after first seeding. Push writes it only when the file is absent in
  the client; pull never reads it. A stub may declare `source = "<path>"`, identifying the scaffold template
  copied to the client path; when absent, the scaffold source path matches the client path. A stub may
  declare `indexes = "<dir>/"`, identifying a directory the stub summarizes — push prints a notice when new
  managed files appear directly in that directory so the maintainer can update the index by hand.
- **symlink** — push creates or replaces the named path as a symbolic link to the given target.

## `tools/scaffold-sync.py`

Bidirectional sync between the scaffold and a client project. Lives only in the scaffold and is not
installed into clients. Both subcommands take the client project's path as their argument and require
both repositories to exist as git repositories.

### `push <client>`

Run from the scaffold. Copies the scaffold's managed payload into the client project.

Preconditions:

- The scaffold has no uncommitted changes in any client payload source: [`manifest.toml`](../manifest.toml),
  [`tools/scaffold-sync.py`](../tools/scaffold-sync.py), every managed file, and every stub source file.
- The client has no uncommitted changes in any managed path, in any path declared as a symlink, in
  `.agentic-scaffold-revision`, or in `.gitignore`.
- No path declared as a symlink in the manifest exists in the client as a regular file or directory; push
  refuses rather than silently destroying it.

Steps:

1. Reads the client's recorded scaffold revision (if any). When the recorded SHA is absent from the
   scaffold's history, or is present but neither equal to `HEAD` nor an ancestor of it, push warns that the
   client holds edits the maintainer has not merged and prompts for confirmation before proceeding.
2. Copies each managed file from the scaffold into the client, overwriting unconditionally. Each stub source
   is copied only when the client path is absent. Each symlink is created or replaced.
3. Writes the scaffold's current `HEAD` SHA into the client's `.agentic-scaffold-revision`.
4. Installs or refreshes the scaffold-owned block in the client's `.gitignore` (see
   [Gitignore block](#gitignore-block)).
5. For each stub with `indexes`, prints a notice listing newly-created managed files under that prefix.

### `pull <client>`

Run from the scaffold. Drafts an incoming branch carrying the client's edits to managed files. The
maintainer merges the branch into the scaffold's default branch by hand.

Preconditions:

- The scaffold has no uncommitted changes in any managed path.
- The client has no uncommitted changes in `.agentic-scaffold-revision`.
- The client's `.agentic-scaffold-revision` names a commit reachable in the scaffold's history.

Pull checks the whole scaffold worktree after copying client managed files to decide whether the incoming
branch has changes to commit. A dirty non-managed scaffold path is part of that check, so the scaffold
worktree must be clean before relying on pull's no-change result.

Steps:

1. Checks out `incoming/<client-name>-<UTC-timestamp>` in the scaffold from the recorded revision.
2. Copies each managed file from the client onto the branch. Files missing in the client are skipped
   with a warning.
3. If nothing changed, deletes the incoming branch, restores the previous branch, and exits without
   committing.
4. Otherwise stages the managed paths and commits with message
   `incoming from <client-name> @ <client-sha>`.
5. Writes the new branch-tip SHA into the client's `.agentic-scaffold-revision`, advancing the recorded
   merge base for the next push to this client.
6. Prints the merge command for the maintainer to run by hand.

If any step after branch creation fails, pull restores the previous branch and deletes the incoming branch.

## `tools/scaffold.sh`

Client-side wrapper that drives `scaffold-sync.py` from inside the client project.

- `tools/scaffold.sh push <scaffold-path>` — upstream this project's edits to the scaffold.
- `tools/scaffold.sh pull <scaffold-path>` — bring scaffold updates into this project.

The wrapper resolves the client's git toplevel via `git rev-parse --show-toplevel`, `cd`s into
`<scaffold-path>`, and execs `scaffold-sync.py <inverse-action> <client-toplevel>` there: a
`tools/scaffold.sh push` invokes `scaffold-sync.py pull`, and `tools/scaffold.sh pull` invokes
`scaffold-sync.py push`.

## Revision tracking

`.agentic-scaffold-revision` in the client records the scaffold commit that the client's managed files
were last reconciled against. Push updates it to the scaffold's `HEAD`; pull updates it to the tip of the
freshly-created incoming branch. The recorded SHA is the merge base for this client's next push and pull.
When two clients diverge from a shared scaffold commit and both upstream their edits, the maintainer
resolves a 3-way merge between two incoming branches in the scaffold repository.

## Gitignore block

Push manages a marked block in the client's `.gitignore`, delimited by `# >>> agentic-scaffold begin <<<`
and `# >>> agentic-scaffold end <<<`. The block excludes harness working state and uv caches while preserving
the version-controlled subdirectories of each harness's tree. Push replaces the entire block on each run;
content outside the markers is untouched.

## Out of scope

- **No upstreaming of new files from a client.** Pull is bounded by the manifest. To add a new file to the
  scaffold, add it in the scaffold repo, list it in [`manifest.toml`](../manifest.toml), and rely on the next
  push to deliver it.
- **No automatic merges.** Pull produces an incoming branch the maintainer merges by hand, resolving
  conflicts the normal way.
- **No version tags.** Each client tracks the scaffold's `HEAD` SHA in `.agentic-scaffold-revision`;
  tagged releases are not part of the workflow.
