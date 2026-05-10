# Tools

Tools the scaffold installs into a client project for use within that project. Distinct from the
scaffold↔client sync tooling, which is documented in [`sync.md`](sync.md).

## `tools/sync-agents.py`

Regenerates per-harness subagent files from the canonical `.claude/agents/*.md` source. Reads each source
file's YAML frontmatter and body and renders equivalents at `.opencode/agents/<name>.md` and
`.codex/agents/<name>.toml`, each carrying an `AUTO-GENERATED` marker. See [`agents.md`](agents.md) for the
agent-layer artifacts this tool operates on. Translation covers:

- Model aliases — CC's `opus` / `sonnet` / `haiku` / `inherit` map onto Codex model + reasoning-effort pairs;
  explicit `effort` in the source overrides the model-derived default. OpenCode never receives a `model`
  field, since the downstream user configures their own provider.
- Tool allow- and deny-lists — CC's `tools` and `disallowedTools` map onto OpenCode's `permission` block;
  Codex's coarser sandbox is set to `read-only` only when both `Bash` and every edit-class tool are denied.
- Body text — copied verbatim into both targets so the runtime prompt is identical.

CLI flags: `--check` (exit 1 if any output would change; no writes), `--dry-run` (print the diff; exit 0),
`--opencode` / `--codex` (limit regeneration to that target; default is both), and `--repo-root <path>`
(override repo discovery; default is `git rev-parse --show-toplevel` or cwd).

Each harness has a SessionStart hook that runs `tools/sync-agents.py --check` and halts the session when any
output would change.
