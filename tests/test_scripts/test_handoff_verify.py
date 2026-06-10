"""Tests for the final all-repo handoff verifier (scripts/handoff_verify.py).

BACKLOG P1 [governance] / ADR 033 enforcement-backlog #1: before the final
response, every touched repo must be clean + pushed and STATUS.md must be the
checkpoint of record (no work committed *after* the last STATUS update).
Ties: COE 2026-06-08-atomic-handoff-failure, 2026-06-09-session-handoff-omission.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess

import pytest

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "handoff_verify.py"
_spec = importlib.util.spec_from_file_location("handoff_verify", _SCRIPT)
assert _spec and _spec.loader
hv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hv)


def _git(repo: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return proc.stdout.strip()


@pytest.fixture()
def repo_pair(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """A local repo with an 'origin' bare remote, one pushed commit."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("a", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-u", "origin", "main")
    return repo, origin


def test_clean_pushed_repo_passes(repo_pair) -> None:
    repo, _ = repo_pair
    state = hv.verify_repo(repo, fetch=False)
    assert state["ok"], state
    assert state["dirty"] is False
    assert state["ahead"] == 0
    assert state["behind"] == 0
    assert state["pushed_commit"]  # sha + subject of the upstream tip


def test_dirty_repo_fails(repo_pair) -> None:
    repo, _ = repo_pair
    (repo / "b.txt").write_text("b", encoding="utf-8")
    state = hv.verify_repo(repo, fetch=False)
    assert not state["ok"]
    assert state["dirty"] is True


def test_unpushed_commit_fails(repo_pair) -> None:
    repo, _ = repo_pair
    (repo / "c.txt").write_text("c", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "local only")
    state = hv.verify_repo(repo, fetch=False)
    assert not state["ok"]
    assert state["ahead"] == 1


def test_no_upstream_fails(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "lonely"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("a", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")
    state = hv.verify_repo(repo, fetch=False)
    assert not state["ok"]
    assert state["no_upstream"] is True


def test_status_stale_when_work_committed_after_status(repo_pair) -> None:
    repo, _ = repo_pair
    status = repo / "docs" / "planning" / "STATUS.md"
    status.parent.mkdir(parents=True)
    status.write_text("# STATUS", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "checkpoint")
    (repo / "work.txt").write_text("w", encoding="utf-8")
    _git(repo, "add", ".")
    # Force a strictly newer commit timestamp for the post-checkpoint work.
    import os

    env = dict(os.environ)
    env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = "2099-01-01T00:00:00"
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "work after checkpoint"],
        check=True,
        capture_output=True,
        env=env,
    )
    _git(repo, "push")
    assert hv.status_is_checkpoint(repo) is False


def test_status_fresh_when_last_commit_touches_status(repo_pair) -> None:
    repo, _ = repo_pair
    status = repo / "docs" / "planning" / "STATUS.md"
    status.parent.mkdir(parents=True)
    status.write_text("# STATUS", encoding="utf-8")
    (repo / "work.txt").write_text("w", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "work + checkpoint together")
    _git(repo, "push")
    assert hv.status_is_checkpoint(repo) is True


def test_status_check_skipped_when_no_status_file(repo_pair) -> None:
    repo, _ = repo_pair
    assert hv.status_is_checkpoint(repo) is True  # not a control-plane repo
