"""Tests for the eval regression gate (scripts/run_eval_gate.py)."""

from __future__ import annotations

import importlib.util
import pathlib

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "run_eval_gate.py"
_spec = importlib.util.spec_from_file_location("run_eval_gate", _SCRIPT)
assert _spec and _spec.loader
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def test_main_passes_on_bundled_gold() -> None:
    assert gate.main([]) == 0


def test_main_writes_reports(tmp_path: pathlib.Path) -> None:
    md = tmp_path / "report.md"
    js = tmp_path / "report.json"
    assert gate.main(["--report-md", str(md), "--report-json", str(js)]) == 0
    assert md.exists()
    assert js.exists()
    assert "retrieval" in md.read_text(encoding="utf-8").lower()
