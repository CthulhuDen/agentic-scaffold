#!/usr/bin/env python3
"""Install repository git hooks."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import NoReturn


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
                        help="print the symlink operation without changing files")
    parser.add_argument("--force", action="store_true",
                        help="replace an existing post-checkout hook")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    common_git_dir = git_path("rev-parse", "--path-format=absolute", "--git-common-dir")
    source = main_checkout_root(common_git_dir) / ".githooks" / "post-checkout"
    destination = git_path("rev-parse", "--path-format=absolute", "--git-path", "hooks/post-checkout")

    if not source.is_file():
        die(f"missing post-checkout hook source in main checkout: {source}")
    if destination.exists() or destination.is_symlink():
        if same_symlink_target(destination, source):
            print(f"post-checkout hook already installed: {destination}")
            return 0
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
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(link_target)
    print(f"installed post-checkout hook: {destination} -> {link_target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
