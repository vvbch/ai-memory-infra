"""Tests for the cross-repo memory write contract gate (ADR 028/031)."""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "check_memory_contract.py"
_spec = importlib.util.spec_from_file_location("check_memory_contract", _SCRIPT)
assert _spec and _spec.loader
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def _write_server(repo: pathlib.Path, body: str) -> None:
    path = repo / "src" / "mcp_proxy" / "server.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _write_client(repo: pathlib.Path, body: str) -> None:
    path = repo / "src" / "mcp_proxy" / "client.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_live_mcp_proxy_conforms() -> None:
    root = gate._workspace_root()
    violations, _ = gate.check_mcp_proxy(root / "ai-memory-infra")
    assert violations == []


def test_live_extension_conforms() -> None:
    root = gate._workspace_root()
    violations, _ = gate.check_extension(root / "ai-memory-extension")
    assert violations == []


def test_mcp_server_passes_with_source_tag(tmp_path: pathlib.Path) -> None:
    _write_server(
        tmp_path,
        '''
def add_memory(text: str, user_id: str | None = None):
    metadata = {"source": "mcp"}
    return _client().add_memory(text, user_id=user_id, metadata=metadata)
''',
    )
    violations, _ = gate.check_mcp_proxy_server(tmp_path)
    assert violations == []


def test_mcp_server_fails_without_source_tag(tmp_path: pathlib.Path) -> None:
    _write_server(
        tmp_path,
        '''
def add_memory(text: str, user_id: str | None = None):
    return _client().add_memory(text, user_id=user_id)
''',
    )
    violations, _ = gate.check_mcp_proxy_server(tmp_path)
    assert any("metadata.source" in v for v in violations)


def test_mcp_client_passes_canonical_user_id(tmp_path: pathlib.Path) -> None:
    _write_client(tmp_path, 'DEFAULT_USER_ID = "chandrav"\n')
    violations, _ = gate.check_mcp_proxy_client(tmp_path)
    assert violations == []


def test_mcp_client_fails_legacy_user_id(tmp_path: pathlib.Path) -> None:
    _write_client(tmp_path, 'DEFAULT_USER_ID = "chrome-extension-user"\n')
    violations, _ = gate.check_mcp_proxy_client(tmp_path)
    assert any("legacy" in v for v in violations)
