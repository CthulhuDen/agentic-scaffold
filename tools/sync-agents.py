#!/usr/bin/env -S uv run --cache-dir .tmp/uv-cache --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""Sync Claude Code subagents to opencode + codex.

Reads .claude/agents/*.md (CC = single source of truth) and writes equivalents:
  .opencode/agents/<name>.md
  .codex/agents/<name>.toml

One-way, deterministic, idempotent. Run after editing any CC subagent.

Codex auto-discovers per-agent files at .codex/agents/*.toml; no .codex/config.toml
registration is needed. The script does not touch .codex/config.toml.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import yaml

SUPPORTED_FIELDS = frozenset({"name", "description", "tools", "disallowedTools", "model", "effort"})

ALL_TARGETS = frozenset({"opencode", "codex"})

# CC `effort` enum (low/medium/high/xhigh/max) → codex `model_reasoning_effort`
# (none/minimal/low/medium/high/xhigh). CC `max` collapses to codex `xhigh` — codex's ceiling.
EFFORT_MAP: dict[str, str] = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "xhigh",
    "max": "xhigh",
}
ALLOWED_EFFORTS = frozenset(EFFORT_MAP.keys())

TOOL_MAP: dict[str, str] = {
    "Read": "read",
    "Write": "edit",
    "Edit": "edit",
    "MultiEdit": "edit",
    "NotebookEdit": "edit",
    "Bash": "bash",
    "Grep": "grep",
    "Glob": "glob",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
    "Task": "task",
    "Agent": "task",
    "TodoWrite": "todowrite",
}
KNOWN_CC_TOOLS = frozenset(TOOL_MAP.keys())
EDIT_CLASS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})


@dataclass(frozen=True)
class ModelTranslation:
    codex_model: str | None
    codex_effort: str | None
    codex_comment: str | None = None


# Hardcoded model alias table. Verified against upstream docs on 2026-05-10.
# Update when Anthropic / OpenAI ship new flagship models.
MODEL_TABLE: dict[str, ModelTranslation] = {
    "opus":    ModelTranslation("gpt-5.5", "high"),
    "sonnet":  ModelTranslation("gpt-5.5", "medium"),
    "haiku":   ModelTranslation("gpt-5.5", "low"),
    "inherit": ModelTranslation(None, None),
}


@dataclass
class CCSubagent:
    path: Path
    name: str
    description: str
    tools: list[str] | None     # None = field absent (inherit all)
    disallowed: list[str]
    model: str | None
    effort: str | None          # one of ALLOWED_EFFORTS, or None
    body: str                   # ends with exactly one newline


def die(msg: str) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------- parsing ----------

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


def parse_cc_subagent(path: Path) -> CCSubagent:
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        die(f"{path}: missing or unterminated YAML frontmatter")
    fm_text, body = m.group(1), m.group(2)
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        die(f"{path}: invalid YAML frontmatter: {e}")
    if not isinstance(fm, dict):
        die(f"{path}: frontmatter must be a mapping")
    extra = sorted(set(fm.keys()) - SUPPORTED_FIELDS)
    if extra:
        for f in extra:
            print(
                f"error: {path}: unsupported field {f!r} "
                f"(supported: {', '.join(sorted(SUPPORTED_FIELDS))})",
                file=sys.stderr,
            )
        sys.exit(1)
    name = fm.get("name")
    description = fm.get("description")
    if not isinstance(name, str) or not name:
        die(f"{path}: 'name' is required")
    if not isinstance(description, str) or not description.strip():
        die(f"{path}: 'description' is required")
    if name != path.stem:
        die(f"{path}: name field {name!r} does not match filename stem {path.stem!r}")
    tools = _normalize_tools(fm.get("tools"), "tools", path)
    disallowed = _normalize_tools(fm.get("disallowedTools"), "disallowedTools", path) or []
    model = fm.get("model")
    if model is not None and not isinstance(model, str):
        die(f"{path}: 'model' must be a string")
    effort = fm.get("effort")
    if effort is not None:
        if not isinstance(effort, str):
            die(f"{path}: 'effort' must be a string")
        if effort not in ALLOWED_EFFORTS:
            die(f"{path}: unknown effort {effort!r} (allowed: {', '.join(sorted(ALLOWED_EFFORTS))})")
    return CCSubagent(
        path=path,
        name=name,
        description=description.strip(),
        tools=tools,
        disallowed=disallowed,
        model=model,
        effort=effort,
        body=body.lstrip("\n").rstrip() + "\n",
    )


def _normalize_tools(value: object, field_name: str, path: Path) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        items = [s.strip() for s in value.split(",") if s.strip()]
    elif isinstance(value, list):
        items = [str(s).strip() for s in value if str(s).strip()]
    else:
        die(f"{path}: '{field_name}' must be a string or list, got {type(value).__name__}")
    for item in items:
        if item not in KNOWN_CC_TOOLS:
            die(f"{path}: unknown CC tool {item!r}")
    return items


def compute_denied(cc: CCSubagent) -> set[str]:
    denied: set[str] = set(cc.disallowed)
    if cc.tools is not None:
        denied |= (KNOWN_CC_TOOLS - set(cc.tools))
    return denied


def translate_model(cc: CCSubagent) -> ModelTranslation:
    if cc.model is None:
        return MODEL_TABLE["inherit"]
    m = cc.model.strip()
    if m in MODEL_TABLE:
        return MODEL_TABLE[m]
    if m.startswith("claude-"):
        return ModelTranslation(
            codex_model="gpt-5.5",
            codex_effort="medium",
            codex_comment=(
                f"NOTE: CC model {m!r} is Anthropic-specific; codex falls back to "
                "gpt-5.5 with medium reasoning effort."
            ),
        )
    die(f"{cc.path}: unknown model alias {m!r}")


# ---------- opencode emission ----------

MAX_YAML_WIDTH = 10**9

class _LiteralStr(str):
    pass


def _literal_str_repr(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.SafeDumper.add_representer(_LiteralStr, _literal_str_repr)


def render_opencode(cc: CCSubagent) -> str:
    # Opencode `model` is intentionally never emitted: we don't know which provider the
    # downstream user has configured, so we let opencode's own default apply. CC's `model`
    # field still flows to the codex side via translate_model().
    fm: dict[str, object] = {}
    fm["description"] = _LiteralStr(cc.description) if "\n" in cc.description else cc.description
    fm["mode"] = "subagent"
    permission = _build_opencode_permission(cc)
    if permission:
        fm["permission"] = permission
    fm_text = yaml.safe_dump(
        fm,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=MAX_YAML_WIDTH,
    )
    # YAML comment in the frontmatter; stripped by the parser, so it never enters the
    # subagent's runtime context. (An HTML comment in the body would be fed to the model.)
    marker = (
        f"# AUTO-GENERATED from .claude/agents/{cc.name}.md by tools/sync-agents.py. "
        "Do not edit."
    )
    return f"---\n{marker}\n{fm_text}---\n\n{cc.body}"


def _build_opencode_permission(cc: CCSubagent) -> dict[str, str]:
    if cc.tools is None and not cc.disallowed:
        return {}
    denied = compute_denied(cc)
    perm: dict[str, str] = {}
    for tool in denied:
        key = TOOL_MAP[tool]
        if key == "edit":
            continue
        perm[key] = "deny"
    if EDIT_CLASS.issubset(denied):
        perm["edit"] = "deny"
    return dict(sorted(perm.items()))


# ---------- codex per-agent emission ----------


def render_codex_agent(cc: CCSubagent) -> str:
    if "'''" in cc.body:
        die(f"{cc.path}: body contains literal '''; cannot emit codex TOML safely")
    if "'''" in cc.description:
        die(f"{cc.path}: description contains literal '''; cannot emit codex TOML safely")
    out: list[str] = []
    out.append(
        f"# AUTO-GENERATED from .claude/agents/{cc.name}.md by tools/sync-agents.py. "
        "Do not edit."
    )
    out.append(f'name = "{_toml_basic_escape(cc.name)}"')
    out.append(f"description = {_toml_string(cc.description)}")
    mt = translate_model(cc)
    if mt.codex_model is not None:
        if mt.codex_comment:
            out.append(f"# {mt.codex_comment}")
        out.append(f'model = "{mt.codex_model}"')
    # Effort: explicit cc.effort overrides the model-alias-derived default. Emitted
    # independently of `model` so that `effort: xhigh` works even when CC `model` is
    # absent/`inherit` (codex applies the override to the inherited parent model).
    final_effort = EFFORT_MAP[cc.effort] if cc.effort is not None else mt.codex_effort
    if final_effort is not None:
        out.append(f'model_reasoning_effort = "{final_effort}"')
    sandbox_line = _infer_codex_sandbox(cc)
    if sandbox_line:
        out.append(sandbox_line)
    out.append(f"developer_instructions = {_toml_multiline_literal(cc.body)}")
    return "\n".join(out) + "\n"


def _infer_codex_sandbox(cc: CCSubagent) -> str | None:
    """Map CC's tool denials onto codex's sandbox modes.

    Codex sandbox couples shell execution and file writes: `read-only` blocks both
    (commands need per-call approval), `workspace-write` allows both, `danger-full-access`
    allows everything plus network. There is no mode that allows shell while blocking
    file writes (or vice versa). We only emit `sandbox_mode` when CC's intent maps cleanly
    onto a codex mode that *restricts* something — namely `read-only` when both Bash and
    every edit-class tool are denied. Edit-only denial is deliberately left unmapped:
    forcing `read-only` would also block verifier subagents from running the shell
    commands they need to do their job. In every other case we omit the line and let
    codex inherit its parent default (typically `workspace-write`). Emitting the default
    explicitly would be a no-op; partial fits are documented by the CC source itself.
    """
    if cc.tools is None and not cc.disallowed:
        return None
    denied = compute_denied(cc)
    if "Bash" in denied and EDIT_CLASS.issubset(denied):
        return 'sandbox_mode = "read-only"'
    return None


def _toml_basic_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _toml_string(s: str) -> str:
    if "\n" not in s:
        return f'"{_toml_basic_escape(s)}"'
    return _toml_multiline_literal(s)


def _toml_multiline_literal(s: str) -> str:
    return f"'''\n{s}'''"


# ---------- diff + write ----------


def render_all(
    cc_list: list[CCSubagent], repo_root: Path, targets: frozenset[str]
) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for cc in cc_list:
        if "opencode" in targets:
            outputs[repo_root / ".opencode" / "agents" / f"{cc.name}.md"] = render_opencode(cc)
        if "codex" in targets:
            outputs[repo_root / ".codex" / "agents" / f"{cc.name}.toml"] = render_codex_agent(cc)
    return outputs


def compute_diff(outputs: dict[Path, str], repo_root: Path) -> str:
    parts: list[str] = []
    for path in sorted(outputs):
        new = outputs[path]
        rel = path.relative_to(repo_root).as_posix()
        if path.exists():
            old = path.read_text(encoding="utf-8")
            from_label = f"a/{rel}"
        else:
            old = ""
            from_label = "/dev/null"
        if old == new:
            continue
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        parts.extend(
            difflib.unified_diff(old_lines, new_lines, fromfile=from_label, tofile=f"b/{rel}")
        )
    return "".join(parts)


def write_outputs(outputs: dict[Path, str]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def report_stale(repo_root: Path, cc_list: list[CCSubagent], targets: frozenset[str]) -> None:
    """Warn only; provider-specific agents may intentionally lack a CC source."""
    current = {cc.name for cc in cc_list}
    for label, subdir, ext in (
        ("opencode", ".opencode/agents", ".md"),
        ("codex", ".codex/agents", ".toml"),
    ):
        if label not in targets:
            continue
        d = repo_root / subdir
        if not d.is_dir():
            continue
        for f in sorted(d.glob(f"*{ext}")):
            if f.stem not in current:
                rel = f.relative_to(repo_root)
                print(
                    f"warning: stale {label} agent {rel} (no matching CC subagent); "
                    "remove manually if intended",
                    file=sys.stderr,
                )


# ---------- CLI ----------


def find_repo_root(override: str | None) -> Path:
    if override:
        return Path(override).resolve()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True,
        )
        return Path(out.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd().resolve()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true",
                   help="exit 1 if any output would change; no writes, no prompt")
    g.add_argument("--dry-run", action="store_true",
                   help="print intended diff to stdout and exit 0")
    p.add_argument("--opencode", action="store_true",
                   help="include opencode targets (default: all if no target flags set)")
    p.add_argument("--codex", action="store_true",
                   help="include codex targets (default: all if no target flags set)")
    p.add_argument("--repo-root", help="repository root (default: git toplevel or CWD)")
    return p.parse_args(argv)


def selected_targets(args: argparse.Namespace) -> frozenset[str]:
    selected = {t for t in ALL_TARGETS if getattr(args, t)}
    return frozenset(selected) if selected else ALL_TARGETS


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = find_repo_root(args.repo_root)
    cc_dir = repo_root / ".claude" / "agents"
    if not cc_dir.is_dir():
        print(f"warning: no .claude/agents/ directory at {cc_dir}", file=sys.stderr)
        return 0
    cc_files = sorted(cc_dir.glob("*.md"))
    if not cc_files:
        print(f"warning: no agents found in {cc_dir}", file=sys.stderr)
        return 0

    targets = selected_targets(args)
    cc_list = [parse_cc_subagent(p) for p in cc_files]
    outputs = render_all(cc_list, repo_root, targets)
    report_stale(repo_root, cc_list, targets)

    diff = compute_diff(outputs, repo_root)
    if not diff:
        print("no changes")
        return 0

    if args.check:
        sys.stdout.write(diff)
        return 1
    if args.dry_run:
        sys.stdout.write(diff)
        return 0

    sys.stderr.write(diff)
    sys.stderr.write("\nApply these changes? [y/N] ")
    sys.stderr.flush()
    try:
        answer = input().strip().lower()
    except EOFError:
        answer = ""
    if answer != "y":
        print("aborted; no files written", file=sys.stderr)
        return 0
    write_outputs(outputs)
    print(f"wrote {len(outputs)} file(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
