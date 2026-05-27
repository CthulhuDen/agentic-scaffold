# Sync

The sync system moves managed files between the scaffold repository and a client project. Each client
records the scaffold commit its managed files were last reconciled against, so concurrent edits from multiple
clients diverge from a known common ancestor and produce real 3-way merges.

## Manifest

[`manifest.yaml`](../manifest.yaml) is the source of truth for which paths the scaffold owns and how each is
handled. Each entry has one of three classes:

- **managed** — the scaffold owns the file. Push overwrites it in the client; pull copies it back from the
  client into the scaffold. A managed file may be listed directly, or it may be discovered under a
  `managed-dirs` directory. Managed directories recurse through their files, excluding paths declared as stubs.
- **stub** — the client owns the file after first seeding. Push writes it only when the file is absent in
  the client; pull never reads it. A stub may set `source` to the scaffold template copied to the client
  path; when absent, the scaffold source path matches the client path. A stub may set `indexes` to a directory
  the stub summarizes — push prints a notice when new managed files appear directly in that directory so the
  maintainer can update the index by hand.
- **symlink** — push creates or replaces the named path as a symbolic link to the given target.

## `tools/scaffold-sync.py`

Bidirectional sync between the scaffold and a client project. Lives only in the scaffold and is not
installed into clients. Both subcommands take the client project's path as their argument and require
both repositories to exist as git repositories.

### `push <client>`

Run from the scaffold. Copies the scaffold's managed payload into the client project.

Preconditions:

- The scaffold has no uncommitted changes in [`manifest.yaml`](../manifest.yaml), any file the manifest
  references as a managed file or stub source, or [`tools/scaffold-sync.py`](../tools/scaffold-sync.py).
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
4. Writes the scaffold repository's absolute path into the client's `.tmp/agentic-scaffold-path`.
5. Installs or refreshes the scaffold-owned block in the client's `.gitignore` (see
   [Gitignore block](#gitignore-block)).
6. For each stub with `indexes`, prints a notice listing newly-created managed files under that prefix.

### `pull <client>`

Run from the scaffold. Applies the client's edits to managed files. Pull commits directly on `main` when
either local `main` equals the recorded scaffold revision and is at or ahead of `main@{upstream}`, or
`main@{upstream}` equals the recorded revision and local `main` lags or matches it (in which case `main` is
fast-forwarded to the recorded revision first). Other pulls draft an incoming branch for the maintainer to
merge by hand.

Preconditions:

- The scaffold has no uncommitted changes in any managed path.
- The client has no uncommitted changes in `.agentic-scaffold-revision`.
- The client's `.agentic-scaffold-revision` names a commit reachable in the scaffold's history.

Pull detects no-change by running `git status --porcelain` on the whole scaffold worktree, not just the managed
paths, so a dirty non-managed path defeats the check and pull proceeds as if managed files had changed.
Uncommitted changes in non-managed scaffold paths never enter the pull commit because pull stages only managed
paths.

Shared steps:

1. Reads the recorded scaffold revision from the client's `.agentic-scaffold-revision`.
2. Takes the direct-to-main path if either local `main` equals the recorded revision and is at or ahead of
   `main@{upstream}`, or `main@{upstream}` equals the recorded revision and local `main` lags or matches it;
   otherwise takes the incoming-branch path.

Direct-to-main path:

1. Checks out `main`. If `main` lags behind the recorded revision, fast-forwards `main` to it.
2. Copies each managed file from the client onto `main`. Files missing in the client are skipped with a warning.
3. If nothing changed, restores the previous branch and exits without committing.
4. Otherwise stages only the managed paths, commits with message
   `incoming from <client-name> @ <client-sha>`, and writes the new commit SHA into the client's
   `.agentic-scaffold-revision`.

If any step after checking out `main` fails, pull resets `main` back to its pre-pull commit, restores managed
files, and returns to the previous branch.

Incoming-branch path:

1. Checks out `incoming/<client-name>-<UTC-timestamp>` in the scaffold from the recorded revision.
2. Copies each managed file from the client onto the branch. Files missing in the client are skipped
   with a warning.
3. If nothing changed, deletes the incoming branch, restores the previous branch, and exits without
   committing.
4. Otherwise stages only the managed paths, commits with message
   `incoming from <client-name> @ <client-sha>`, and writes the new branch-tip SHA into the client's
   `.agentic-scaffold-revision`.
5. Prints the merge command for the maintainer to run by hand.

If any step after branch creation fails, pull restores the previous branch and deletes the incoming branch.

No-commit path (`--no-commit`):

1. Copies each managed file from the client onto the current branch. Files missing in the client are skipped
   with a warning.
2. Stops without checking the recorded revision, fast-forwarding, branching, committing, or writing the client's
   `.agentic-scaffold-revision`.

Of the preconditions above, only clean managed paths in the scaffold are required. This path serves a pull large
enough that no single committed result is coherent: the maintainer curates the working tree and commits by hand.

## `tools/scaffold.sh`

Client-side wrapper that drives `scaffold-sync.py` from inside the client project.

- `tools/scaffold.sh push [<scaffold-path>]` — upstream this project's edits to the scaffold.
- `tools/scaffold.sh pull [<scaffold-path>]` — bring scaffold updates into this project.

The wrapper resolves the client's git toplevel via `git rev-parse --show-toplevel`, `cd`s into
`<scaffold-path>`, and execs `scaffold-sync.py <inverse-action> <client-toplevel>` there. When
`<scaffold-path>` is omitted, the wrapper reads the scaffold path from `.tmp/agentic-scaffold-path` in the
client. A `tools/scaffold.sh push` invokes `scaffold-sync.py pull`, and `tools/scaffold.sh pull` invokes
`scaffold-sync.py push`.

## Revision tracking

`.agentic-scaffold-revision` in the client records the scaffold commit that the client's managed files were
last reconciled against. Push updates it to the scaffold's `HEAD`; pull updates it to the new scaffold commit
it created — the direct main commit, or the tip of the freshly-created incoming branch. The recorded SHA is
the merge base for this client's next push and pull. When two clients diverge from a shared scaffold commit
and both upstream their edits, the maintainer resolves a 3-way merge between two incoming branches in the
scaffold repository.

## Scaffold path cache

`.tmp/agentic-scaffold-path` in the client records the absolute path of the scaffold repository that last pushed
into that client. `tools/scaffold.sh` uses the path as its default scaffold repository when no explicit
`<scaffold-path>` argument is provided.

## Gitignore block

Push manages a marked block in the client's `.gitignore`, delimited by `# >>> agentic-scaffold begin <<<`
and `# >>> agentic-scaffold end <<<`. The block excludes harness working state and uv caches while preserving
the version-controlled subdirectories of each harness's tree. Push replaces the entire block on each run;
content outside the markers is untouched.

## Out of scope

- **No upstreaming of new files from a client.** Pull is bounded by the manifest. To add a new file to the
  scaffold, add it in the scaffold repo under a managed directory or list it in
  [`manifest.yaml`](../manifest.yaml), and rely on the next push to deliver it.
- **No automatic merges of incoming branches.** When pull falls back to an incoming branch, the maintainer
  merges it by hand, resolving conflicts the normal way.
- **No version tags.** Each client tracks the scaffold's `HEAD` SHA in `.agentic-scaffold-revision`;
  tagged releases are not part of the workflow.
