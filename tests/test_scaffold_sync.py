"""Tests for `tools/scaffold-sync.py push`. See specs/sync.md."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "scaffold-sync.py"

MANIFEST = """\
managed:
  - managed.md
stub:
  - path: stub.md
"""

# Keeps the throwaway repositories independent of the developer's git configuration.
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
}


@pytest.fixture(scope="module")
def sync() -> ModuleType:
    spec = importlib.util.spec_from_file_location("scaffold_sync", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # The script's dataclasses resolve their annotations through sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def init_repo(path: Path) -> Path:
    path.mkdir()
    git(path, "init", "--initial-branch=main")
    return path


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "--all")
    git(repo, "commit", "--message", message)


@pytest.fixture
def repos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sync: ModuleType
) -> tuple[Path, Path]:
    """A scaffold with one managed file and one stub, pushed into a client that committed the result."""
    for name, value in GIT_ENV.items():
        monkeypatch.setenv(name, value)

    scaffold = init_repo(tmp_path / "scaffold")
    (scaffold / "manifest.yaml").write_text(MANIFEST, encoding="utf-8")
    (scaffold / "managed.md").write_text("scaffold managed v1\n", encoding="utf-8")
    (scaffold / "stub.md").write_text("scaffold seed v1\n", encoding="utf-8")
    commit_all(scaffold, "scaffold v1")

    client = init_repo(tmp_path / "client")
    sync.push(scaffold, client)
    commit_all(client, "install scaffold")
    return scaffold, client


def test_push_keeps_existing_stub(repos: tuple[Path, Path], sync: ModuleType) -> None:
    scaffold, client = repos
    (scaffold / "managed.md").write_text("scaffold managed v2\n", encoding="utf-8")
    (scaffold / "stub.md").write_text("scaffold seed v2\n", encoding="utf-8")
    commit_all(scaffold, "scaffold v2")
    (client / "stub.md").write_text("client edit, uncommitted\n", encoding="utf-8")

    sync.push(scaffold, client)

    assert (client / "stub.md").read_text(encoding="utf-8") == "client edit, uncommitted\n"
    # The managed file proves the push ran, so the stub was skipped and not merely unreached.
    assert (client / "managed.md").read_text(encoding="utf-8") == "scaffold managed v2\n"


def test_push_refuses_uncommitted_managed_edit(
    repos: tuple[Path, Path], sync: ModuleType
) -> None:
    scaffold, client = repos
    (client / "managed.md").write_text("client edit, uncommitted\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        sync.push(scaffold, client)

    assert (client / "managed.md").read_text(encoding="utf-8") == "client edit, uncommitted\n"
