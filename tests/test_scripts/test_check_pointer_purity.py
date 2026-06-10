"""Tests for the pointer-file purity gate (scripts/check_pointer_purity.py).

ADR 018 / COE 2026-06-07-cursor-rule-drift: editor pointer files carry zero
canonical content. These tests pin the boundary the gate enforces.
"""

from __future__ import annotations

import importlib.util
import pathlib

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "check_pointer_purity.py"
_spec = importlib.util.spec_from_file_location("check_pointer_purity", _SCRIPT)
assert _spec and _spec.loader
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


PURE = """---
description: Project pointer
alwaysApply: true
---

Read **`AGENTS.md`** at the repo root before acting — it is the single source.

This file is a thin pointer (tenet 2, ADR 018). It holds no rules of its own.
"""

CLAUDE = """# CLAUDE.md

Canonical agent context lives in **[AGENTS.md](./AGENTS.md)** — read that.

This pointer exists because Claude Code auto-loads CLAUDE.md.
"""


def test_pure_pointer_passes() -> None:
    assert gate.check_pointer("00-project.mdc", PURE) == []


def test_claude_title_heading_is_allowed() -> None:
    assert gate.check_pointer("CLAUDE.md", CLAUDE) == []


def test_missing_agents_reference_fails() -> None:
    text = PURE.replace("AGENTS.md", "SOMETHING.md")
    assert any("reference AGENTS.md" in v for v in gate.check_pointer("p.mdc", text))


def test_numbered_tenet_fails() -> None:
    text = PURE + "\n1. **Everything versioned.** lives in source control.\n"
    assert any("numbered rule/tenet" in v for v in gate.check_pointer("p.mdc", text))


def test_table_fails() -> None:
    text = PURE + "\n| When | Update |\n|---|---|\n| x | y |\n"
    assert any("table" in v for v in gate.check_pointer("p.mdc", text))


def test_section_heading_fails() -> None:
    text = PURE + "\n## Tenets\n\nsome copied tenet\n"
    assert any("section heading" in v for v in gate.check_pointer("p.mdc", text))


def test_line_cap_fails() -> None:
    text = PURE + "\n" + "\n".join(f"extra content line {i} about AGENTS.md" for i in range(20))
    assert any("pointer cap" in v for v in gate.check_pointer("p.mdc", text, max_lines=14))


def test_frontmatter_split() -> None:
    fm, body = gate.split_frontmatter(PURE)
    assert fm is not None and "alwaysApply: true" in fm
    assert body.lstrip().startswith("Read")
    assert gate.is_always_applied(fm) is True


def test_globs_rule_is_not_always_applied() -> None:
    scoped = "---\ndescription: x\nglobs: src/**\n---\n\nsome convention\n"
    fm, _ = gate.split_frontmatter(scoped)
    assert gate.is_always_applied(fm) is False


def test_discovers_only_pure_pointers(tmp_path: pathlib.Path) -> None:
    rules = tmp_path / ".cursor" / "rules"
    rules.mkdir(parents=True)
    (rules / "00-always.mdc").write_text(PURE, "utf-8")
    (rules / "10-scoped.mdc").write_text(
        "---\ndescription: x\nglobs: src/**\n---\n\nconvention\n", "utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text(CLAUDE, "utf-8")
    found = {p.name for p in gate.pure_pointer_files(tmp_path)}
    assert found == {"00-always.mdc", "CLAUDE.md"}


def test_main_on_real_repo() -> None:
    repo = pathlib.Path(__file__).resolve().parents[2]
    assert gate.main(["--repo-root", str(repo)]) == 0
