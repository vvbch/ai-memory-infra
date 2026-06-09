"""Tests for the STATUS.md snapshot-shape gate (scripts/check_status_snapshot.py).

COE 2026-06-10-status-snapshot-log-drift: STATUS.md is a snapshot overwritten
each session, not a journal. These tests pin the shape contract.
"""

from __future__ import annotations

import importlib.util
import pathlib

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "check_status_snapshot.py"
_spec = importlib.util.spec_from_file_location("check_status_snapshot", _SCRIPT)
assert _spec and _spec.loader
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


GOOD = """# STATUS — resumable session snapshot

**Last updated:** 2026-06-10 (summary of the current state)

## Plain English — where we are (resume here)

Things are fine.

## Current phase

Phase N.

## Done this session

- one thing

## Last decisions

- a decision

## Next action

> Do the thing.
"""


def test_clean_snapshot_passes() -> None:
    assert gate.check_status(GOOD) == []


def test_prior_update_block_fails() -> None:
    text = GOOD + "\n**Prior update:** 2026-06-09 (older narrative)\n"
    violations = gate.check_status(text)
    assert any("Prior update" in v for v in violations)


def test_missing_last_updated_fails() -> None:
    text = GOOD.replace("**Last updated:**", "**Updated:**")
    violations = gate.check_status(text)
    assert any("Last updated" in v for v in violations)


def test_duplicate_last_updated_fails() -> None:
    text = GOOD + "\n**Last updated:** 2026-06-09 (a second one)\n"
    violations = gate.check_status(text)
    assert any("exactly one" in v for v in violations)


def test_duplicate_session_sections_fail() -> None:
    text = GOOD + "\n## Done this session (2026-06-07)\n\n- old\n"
    text += "\n## Last decisions (2026-06-08)\n\n- old\n"
    violations = gate.check_status(text)
    assert any("'## Done this session'" in v for v in violations)
    assert any("'## Last decisions'" in v for v in violations)


def test_line_cap_fails() -> None:
    text = GOOD + ("filler\n" * 500)
    violations = gate.check_status(text)
    assert any("snapshot cap" in v for v in violations)


def test_line_cap_is_configurable() -> None:
    assert gate.check_status(GOOD, max_lines=5) != []
    assert gate.check_status(GOOD, max_lines=10_000) == []


def test_main_exit_codes(tmp_path: pathlib.Path) -> None:
    good = tmp_path / "STATUS.md"
    good.write_text(GOOD, encoding="utf-8")
    assert gate.main([str(good)]) == 0

    bad = tmp_path / "STATUS_bad.md"
    bad.write_text(GOOD + "\n**Prior update:** old stuff\n", encoding="utf-8")
    assert gate.main([str(bad)]) == 1


def test_main_missing_file(tmp_path: pathlib.Path) -> None:
    assert gate.main([str(tmp_path / "nope.md")]) == 1
