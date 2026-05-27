#!/usr/bin/env python3
"""Install repository git hooks and seed the Codex environment file."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import NoReturn


# Codex provisions a workspace without firing git hooks, so the agent-file
# regeneration that post-checkout drives never runs there. This environment
# file makes Codex invoke the hook during setup; it is seeded once and then
# owned by the project.
CODEX_ENVIRONMENT = """\
version = 1
name = "{name}"

[setup]
script = '''
hook="$(git rev-parse --path-format=absolute --git-common-dir)/hooks/post-checkout"
"$hook" 0000000000000000000000000000000000000000 HEAD 1
'''
"""


def die(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def git_path(*args: str) -> Path:
    try:
        out = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        die(f"git {' '.join(args)} failed: {exc}")
    return Path(out.stdout.strip())


def same_symlink_target(link: Path, target: Path) -> bool:
    if not link.is_symlink():
        return False
    try:
        return link.resolve(strict=True) == target.resolve(strict=True)
    except FileNotFoundError:
        return False


def relative_target(source: Path, destination: Path) -> str:
    return os.path.relpath(source, destination.parent)


def main_checkout_root(common_git_dir: Path) -> Path:
    return common_git_dir.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="print both operations without changing files")
    parser.add_argument("--force", action="store_true",
                        help="replace an existing post-checkout hook")
    return parser.parse_args(argv)


def install_post_checkout_hook(root: Path, args: argparse.Namespace) -> None:
    source = root / ".githooks" / "post-checkout"
    destination = git_path("rev-parse", "--path-format=absolute", "--git-path", "hooks/post-checkout")

    if not source.is_file():
        die(f"missing post-checkout hook source in main checkout: {source}")
    if destination.exists() or destination.is_symlink():
        if same_symlink_target(destination, source):
            print(f"post-checkout hook already installed: {destination}")
            return
        if destination.is_dir():
            die(f"{destination} is a directory")
        if not args.force:
            die(f"{destination} already exists; rerun with --force to replace it")
        if args.dry_run:
            print(f"would replace {destination}")
        else:
            destination.unlink()

    link_target = relative_target(source, destination)
    if args.dry_run:
        print(f"would link {destination} -> {link_target}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(link_target)
    print(f"installed post-checkout hook: {destination} -> {link_target}")


def seed_codex_environment(root: Path, args: argparse.Namespace) -> None:
    destination = root / ".codex" / "environments" / "environment.toml"
    if destination.exists():
        print(f"codex environment already present: {destination}")
        return
    if args.dry_run:
        print(f"would seed codex environment: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(CODEX_ENVIRONMENT.format(name=root.name), encoding="utf-8")
    print(f"seeded codex environment: {destination}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    common_git_dir = git_path("rev-parse", "--path-format=absolute", "--git-common-dir")
    root = main_checkout_root(common_git_dir)
    install_post_checkout_hook(root, args)
    seed_codex_environment(root, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
