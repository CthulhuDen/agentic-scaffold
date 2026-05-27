#!/usr/bin/env -S uv run --cache-dir .tmp/uv-cache --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""Sync the agentic scaffold between this repo and a client project.

Subcommands:
    push <client>  Write managed files into <client>; seed stubs only if absent;
                   install the scaffold .gitignore block; stamp
                   <client>/.agentic-scaffold-revision with the scaffold's HEAD SHA;
                   remember this scaffold's absolute path under <client>/.tmp/.
    pull <client>  Apply the client's managed-file edits according to specs/sync.md.
                   With --no-commit, copy managed files into the working tree and stop,
                   leaving an uncommitted result for the maintainer to curate by hand.

See specs/sync.md for preconditions. Review the result with `git diff` (push)
or `git log` (pull).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import NoReturn

import yaml

GITIGNORE_BEGIN = "# >>> agentic-scaffold begin <<<"
GITIGNORE_END = "# >>> agentic-scaffold end <<<"
GITIGNORE_BLOCK = """\
# >>> agentic-scaffold begin <<<
# Managed by the agentic scaffold installer. Do not edit between markers.
/.tmp/
__pycache__/
*.py[cod]
/.claude/*
!/.claude/agents/
!/.claude/skills
/.opencode/*
!/.opencode/plugin/
/.codex/*
!/.codex/hooks.json
!/.codex/session-start.sh
!/.codex/environments/
# >>> agentic-scaffold end <<<
"""

REVISION_FILE = ".agentic-scaffold-revision"
LAST_SCAFFOLD_PATH_FILE = ".tmp/agentic-scaffold-path"
MANIFEST_FILE = "manifest.yaml"
MAIN_BRANCH = "main"


@dataclass(frozen=True)
class FileEntry:
    path: str
    cls: str
    source: str | None = None
    indexes: str | None = None

    @property
    def source_path(self) -> str:
        return self.source or self.path


@dataclass(frozen=True)
class SymlinkEntry:
    path: str
    target: str


def die(msg: str) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def require_mapping(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        die(f"{label} must be a mapping")
    return value


def require_list(value: object, label: str) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        die(f"{label} must be a list")
    return value


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str):
        die(f"{label} must be a string")
    return value


def require_relative_manifest_path(
    value: object, label: str, *, directory: bool = False
) -> str:
    path = PurePosixPath(require_string(value, label))
    if path.is_absolute() or not path.parts or ".." in path.parts:
        die(f"{label} must be a relative path within the repository")
    normalized = path.as_posix()
    if directory:
        return normalized.rstrip("/") + "/"
    return normalized


def git_visible_files(repo: Path, pathspec: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            pathspec,
        ],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        die(f"git ls-files failed in {repo}: {result.stderr.strip()}")
    return result.stdout.splitlines()


def expand_managed_dir(
    scaffold_root: Path, managed_dir: str, stub_paths: set[str]
) -> list[FileEntry]:
    file_paths = set(git_visible_files(scaffold_root, managed_dir))
    root = scaffold_root / managed_dir
    if not root.is_dir() and not file_paths:
        die(f"managed dir not found: {managed_dir}")

    return [
        FileEntry(path=path, cls="managed")
        for path in sorted(file_paths)
        if path not in stub_paths
    ]


def load_manifest(scaffold_root: Path) -> tuple[list[FileEntry], list[SymlinkEntry]]:
    manifest_path = scaffold_root / MANIFEST_FILE
    if not manifest_path.exists():
        die(f"manifest not found at {manifest_path}")
    try:
        parsed = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        die(f"failed to parse {MANIFEST_FILE}: {e}")
    data = require_mapping({} if parsed is None else parsed, MANIFEST_FILE)

    stubs = require_list(data.get("stub"), "stub")
    stub_paths = {
        require_relative_manifest_path(
            require_mapping(e, "stub entry").get("path"), "stub path"
        )
        for e in stubs
    }

    files: list[FileEntry] = []
    for managed_dir in require_list(data.get("managed-dirs"), "managed-dirs"):
        files.extend(
            expand_managed_dir(
                scaffold_root,
                require_relative_manifest_path(
                    managed_dir, "managed dir", directory=True
                ),
                stub_paths,
            )
        )
    for path in require_list(data.get("managed"), "managed"):
        managed_path = require_relative_manifest_path(path, "managed path")
        if managed_path not in stub_paths:
            files.append(FileEntry(path=managed_path, cls="managed"))
    for e in stubs:
        entry = require_mapping(e, "stub entry")
        files.append(
            FileEntry(
                path=require_relative_manifest_path(entry.get("path"), "stub path"),
                cls="stub",
                source=(
                    require_relative_manifest_path(entry["source"], "stub source")
                    if "source" in entry
                    else None
                ),
                indexes=(
                    require_relative_manifest_path(
                        entry["indexes"], "stub indexes", directory=True
                    )
                    if "indexes" in entry
                    else None
                ),
            )
        )

    symlinks: list[SymlinkEntry] = []
    for e in require_list(data.get("symlink"), "symlink"):
        entry = require_mapping(e, "symlink entry")
        symlinks.append(
            SymlinkEntry(
                path=require_relative_manifest_path(
                    entry.get("path"), "symlink path"
                ),
                target=require_string(entry.get("target"), "symlink target"),
            )
        )
    return files, symlinks


def git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        die(f"git {' '.join(args)} failed in {repo}: {result.stderr.strip()}")
    return result.stdout


def require_clean(repo: Path, paths: list[str], label: str) -> None:
    if not paths:
        return
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "--", *paths],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        die(f"{label}: git status failed: {result.stderr.strip()}")
    if result.stdout.strip():
        print(f"error: {label} has uncommitted changes in required paths:", file=sys.stderr)
        print(result.stdout, file=sys.stderr, end="")
        print("commit or stash before continuing.", file=sys.stderr)
        sys.exit(1)


def unique_paths(paths: list[str]) -> list[str]:
    return list(dict.fromkeys(paths))


def require_no_real_files_at_symlink_paths(
    client_root: Path, symlinks: list[SymlinkEntry]
) -> None:
    for s in symlinks:
        dst = client_root / s.path
        if dst.is_symlink() or not dst.exists():
            continue
        die(
            f"client has a regular file or directory at {s.path}; push would replace "
            f"it with a symlink to {s.target}. move its content into {s.target} (or "
            f"delete {s.path}) before re-running push."
        )


def head_sha(repo: Path) -> str:
    return git(repo, ["rev-parse", "HEAD"]).strip()


def resolve_commit(repo: Path, ref: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{ref}^{{commit}}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def commit_exists(repo: Path, sha: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
        capture_output=True, check=False,
    ).returncode == 0


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, descendant],
        capture_output=True, check=False,
    ).returncode == 0


def confirm(prompt: str) -> bool:
    print(prompt, file=sys.stderr, end="")
    sys.stderr.flush()
    try:
        return input().strip().lower() == "y"
    except EOFError:
        return False


def current_branch(repo: Path) -> str:
    return git(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()


def can_pull_directly_to_main(repo: Path, recorded: str) -> bool:
    main_sha = resolve_commit(repo, MAIN_BRANCH)
    upstream_sha = resolve_commit(repo, f"{MAIN_BRANCH}@{{upstream}}")
    if main_sha is None or upstream_sha is None:
        return False
    if recorded == main_sha and is_ancestor(repo, upstream_sha, main_sha):
        return True
    if recorded == upstream_sha and is_ancestor(repo, main_sha, upstream_sha):
        return True
    return False


def replace_block(text: str, begin: str, end: str, block: str) -> str:
    if begin not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        return text + block
    before, _, rest = text.partition(begin)
    _, _, after = rest.partition(end + "\n")
    return before + block + after


def install_gitignore_block(client_root: Path) -> None:
    gitignore = client_root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    new = replace_block(existing, GITIGNORE_BEGIN, GITIGNORE_END, GITIGNORE_BLOCK)
    if new != existing:
        gitignore.write_text(new, encoding="utf-8")


def write_last_scaffold_path(scaffold_root: Path, client_root: Path) -> None:
    pointer = client_root / LAST_SCAFFOLD_PATH_FILE
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(scaffold_root.resolve()) + "\n", encoding="utf-8")


def push(scaffold_root: Path, client_root: Path) -> None:
    files, symlinks = load_manifest(scaffold_root)
    managed_paths = [f.path for f in files if f.cls == "managed"]
    payload_source_paths = unique_paths(
        [MANIFEST_FILE, "tools/scaffold-sync.py", *[f.source_path for f in files]]
    )
    symlink_paths = [s.path for s in symlinks]
    require_clean(scaffold_root, payload_source_paths, "scaffold")
    require_clean(
        client_root,
        managed_paths + symlink_paths + [REVISION_FILE, ".gitignore"],
        "client",
    )
    require_no_real_files_at_symlink_paths(client_root, symlinks)

    scaffold_sha = head_sha(scaffold_root)
    rev_path = client_root / REVISION_FILE
    if rev_path.exists():
        recorded = rev_path.read_text(encoding="utf-8").strip()
        if recorded != scaffold_sha and not (
            commit_exists(scaffold_root, recorded)
            and is_ancestor(scaffold_root, recorded, scaffold_sha)
        ):
            print(
                f"warning: client recorded {recorded[:12]} is not an ancestor of scaffold "
                f"HEAD {scaffold_sha[:12]}.",
                file=sys.stderr,
            )
            print(
                "this typically means the client pushed edits the maintainer has not merged "
                "yet; pushing now would overwrite the unmerged work in the client's managed files.",
                file=sys.stderr,
            )
            if not confirm("continue? [y/N] "):
                die("aborted")

    additions_by_dir: defaultdict[str, list[str]] = defaultdict(list)

    for f in files:
        src = scaffold_root / f.source_path
        if not src.exists():
            die(f"scaffold missing source: {f.source_path}")
        dst = client_root / f.path
        if f.cls == "stub" and dst.exists():
            continue
        is_new_managed = f.cls == "managed" and not dst.exists()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if is_new_managed:
            parent = str(Path(f.path).parent).rstrip("/") + "/"
            additions_by_dir[parent].append(f.path)

    for s in symlinks:
        dst = client_root / s.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        dst.symlink_to(s.target)

    rev_path.write_text(scaffold_sha + "\n", encoding="utf-8")
    write_last_scaffold_path(scaffold_root, client_root)
    install_gitignore_block(client_root)

    for f in files:
        if f.cls != "stub" or not f.indexes:
            continue
        added = additions_by_dir.get(f.indexes, [])
        if added:
            print(f"notice: new managed files under {f.indexes}: {', '.join(added)}")
            print(f"        consider updating {f.path}")

    print(f"pushed scaffold@{scaffold_sha[:12]} to {client_root}")


def copy_managed_files(
    files: list[FileEntry], scaffold_root: Path, client_root: Path
) -> None:
    for f in files:
        if f.cls != "managed":
            continue
        src = client_root / f.path
        if not src.exists():
            print(f"warning: client missing managed file {f.path}; skipping", file=sys.stderr)
            continue
        dst = scaffold_root / f.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def commit_managed_files(
    scaffold_root: Path, client_root: Path, managed_paths: list[str], client_name: str
) -> str:
    git(scaffold_root, ["add", "--", *managed_paths])
    client_sha = head_sha(client_root)
    git(scaffold_root, ["commit", "-m", f"incoming from {client_name} @ {client_sha[:12]}"])
    return head_sha(scaffold_root)


def restore_managed_files(scaffold_root: Path, managed_paths: list[str]) -> None:
    if not managed_paths:
        return
    subprocess.run(
        ["git", "-C", str(scaffold_root), "checkout", "HEAD", "--", *managed_paths],
        capture_output=True, check=False,
    )


def pull_directly_to_main(
    scaffold_root: Path,
    client_root: Path,
    files: list[FileEntry],
    managed_paths: list[str],
    rev_path: Path,
    base_branch: str,
    client_name: str,
    recorded: str,
) -> None:
    main_sha_before = resolve_commit(scaffold_root, MAIN_BRANCH)
    git(scaffold_root, ["checkout", MAIN_BRANCH])

    try:
        if main_sha_before is not None and main_sha_before != recorded:
            git(scaffold_root, ["merge", "--ff-only", recorded])

        copy_managed_files(files, scaffold_root, client_root)

        status = git(scaffold_root, ["status", "--porcelain"])
        if not status.strip():
            print(f"no changes from {client_name}; {MAIN_BRANCH} unchanged")
            if base_branch != MAIN_BRANCH:
                git(scaffold_root, ["checkout", base_branch])
            return

        new_sha = commit_managed_files(
            scaffold_root, client_root, managed_paths, client_name
        )
        rev_path.write_text(new_sha + "\n", encoding="utf-8")
    except BaseException:
        current_main = resolve_commit(scaffold_root, MAIN_BRANCH)
        if (
            main_sha_before is not None
            and current_main is not None
            and current_main != main_sha_before
        ):
            subprocess.run(
                ["git", "-C", str(scaffold_root), "reset", "--soft", main_sha_before],
                capture_output=True, check=False,
            )
        restore_managed_files(scaffold_root, managed_paths)
        if base_branch != MAIN_BRANCH:
            subprocess.run(
                ["git", "-C", str(scaffold_root), "checkout", base_branch],
                capture_output=True, check=False,
            )
        raise

    print(f"committed {new_sha[:12]} directly to {MAIN_BRANCH}")
    print(f"recorded {new_sha[:12]} in {REVISION_FILE} on the client side")


def pull(scaffold_root: Path, client_root: Path, *, no_commit: bool = False) -> None:
    files, _ = load_manifest(scaffold_root)
    managed_paths = [f.path for f in files if f.cls == "managed"]
    require_clean(scaffold_root, managed_paths, "scaffold")

    if no_commit:
        copy_managed_files(files, scaffold_root, client_root)
        print(f"copied managed files from {client_root.name} into the working tree; not committed")
        return

    require_clean(client_root, [REVISION_FILE], "client")

    rev_path = client_root / REVISION_FILE
    if not rev_path.exists():
        die(
            f"{rev_path} not found; run push from the scaffold to establish a "
            "merge base before pulling from this client"
        )
    recorded = rev_path.read_text(encoding="utf-8").strip()
    if not commit_exists(scaffold_root, recorded):
        die(
            f"recorded revision {recorded} is not in scaffold history; "
            f"resurrect the commit or set {REVISION_FILE} to a reachable base"
        )

    base_branch = current_branch(scaffold_root)
    client_name = client_root.name
    if can_pull_directly_to_main(scaffold_root, recorded):
        pull_directly_to_main(
            scaffold_root,
            client_root,
            files,
            managed_paths,
            rev_path,
            base_branch,
            client_name,
            recorded,
        )
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch = f"incoming/{client_name}-{timestamp}"
    git(scaffold_root, ["checkout", "-b", branch, recorded])

    try:
        copy_managed_files(files, scaffold_root, client_root)

        status = git(scaffold_root, ["status", "--porcelain"])
        if not status.strip():
            print(f"no changes from {client_name}; removing empty branch")
            git(scaffold_root, ["checkout", base_branch])
            git(scaffold_root, ["branch", "-D", branch])
            return

        new_sha = commit_managed_files(
            scaffold_root, client_root, managed_paths, client_name
        )
        rev_path.write_text(new_sha + "\n", encoding="utf-8")
    except BaseException:
        subprocess.run(
            ["git", "-C", str(scaffold_root), "checkout", base_branch],
            capture_output=True, check=False,
        )
        subprocess.run(
            ["git", "-C", str(scaffold_root), "branch", "-D", branch],
            capture_output=True, check=False,
        )
        raise

    print(f"created branch {branch} from {recorded[:12]}")
    print(f"recorded {new_sha[:12]} in {REVISION_FILE} on the client side")
    print(f"to merge:   git checkout {base_branch} && git merge {branch}")


def find_scaffold_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("push", "pull"):
        sp = sub.add_parser(name)
        sp.add_argument("client", help="path to the client project root")
        if name == "pull":
            sp.add_argument(
                "--no-commit",
                action="store_true",
                help="copy managed files into the working tree without committing",
            )
    args = parser.parse_args(argv)

    scaffold_root = find_scaffold_root()
    client_root = Path(args.client).resolve()
    for label, root in (("scaffold", scaffold_root), ("client", client_root)):
        if not (root / ".git").exists():
            die(f"{label} {root} is not a git repository")

    if args.cmd == "push":
        push(scaffold_root, client_root)
    else:
        pull(scaffold_root, client_root, no_commit=args.no_commit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
