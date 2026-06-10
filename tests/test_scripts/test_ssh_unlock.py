"""Tests for scripts/ssh_unlock.py — no real clipboard or ssh-agent."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "ssh_unlock", _REPO / "scripts" / "ssh_unlock.py"
)
assert _SPEC and _SPEC.loader
hv = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = hv
_SPEC.loader.exec_module(hv)


def test_clipboard_ready_rejects_empty() -> None:
    assert hv._clipboard_ready("") is False
    assert hv._clipboard_ready("   ") is False


def test_clipboard_ready_accepts_reasonable_passphrase() -> None:
    assert hv._clipboard_ready("my-passphrase") is True


def test_check_dry_run_ok(tmp_path: Path) -> None:
    key = tmp_path / "id_ed25519"
    key.write_text("fake-key\n", encoding="utf-8")
    with patch.object(hv, "_read_clipboard", return_value="secret\n"):
        result = hv.unlock(key_path=str(key), probe_host=None, dry_run=True)
    assert result.ok is True
    assert result.clipboard_ready is True
    assert result.key_loaded is False


def test_unlock_fails_when_clipboard_empty(tmp_path: Path) -> None:
    key = tmp_path / "id_ed25519"
    key.write_text("fake-key\n", encoding="utf-8")
    with patch.object(hv, "_read_clipboard", return_value=""):
        result = hv.unlock(key_path=str(key), probe_host=None)
    assert result.ok is False
    assert "clipboard" in result.messages[-1].lower()


def test_unlock_success_clears_clipboard_and_probes(tmp_path: Path) -> None:
    key = tmp_path / "id_ed25519"
    key.write_text("fake-key\n", encoding="utf-8")
    with (
        patch.object(hv, "_read_clipboard", return_value="secret\n"),
        patch.object(hv, "_ensure_ssh_agent", return_value=True),
        patch.object(hv, "_ssh_add", return_value=True),
        patch.object(hv, "_clear_clipboard") as clear,
        patch.object(hv, "_probe_ssh", return_value=True),
    ):
        result = hv.unlock(key_path=str(key), probe_host="root@example.com")
    assert result.ok is True
    assert result.probe_ok is True
    clear.assert_called_once()


def test_main_check_exit_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key = tmp_path / "id_ed25519"
    key.write_text("fake-key\n", encoding="utf-8")
    monkeypatch.setattr(
        hv,
        "unlock",
        lambda **_: hv.UnlockResult(
            ok=True,
            clipboard_ready=True,
            agent_running=False,
            key_loaded=False,
            probe_ok=None,
            key_path=str(key),
            messages=["clipboard ready (dry-run / --check only)"],
        ),
    )
    assert hv.main(["--check"]) == 0
