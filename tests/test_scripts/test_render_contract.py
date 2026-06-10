"""Tests for the structured operating-contract renderer (scripts/render_contract.py).

ADR 033: the operating contract is a structured single-source (contract/*.yaml)
that *renders* the prose sections of AGENTS.md / docs/tenets.md and emits a
coverage report; a --check gate fails on drift. These tests pin the render/join
semantics (so the byte-equal lift stays faithful), the fence round-trip, the
coverage shape, and the validation rules.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

_SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "render_contract.py"
_spec = importlib.util.spec_from_file_location("render_contract", _SCRIPT)
assert _spec and _spec.loader
rc = importlib.util.module_from_spec(_spec)
sys.modules["render_contract"] = rc  # so @dataclass can resolve its module
_spec.loader.exec_module(rc)


# --------------------------------------------------------------------------- #
# Fixtures: a tiny synthetic contract
# --------------------------------------------------------------------------- #


def _contract() -> dict:
    return {
        "tenets": {
            "rules": [
                {
                    "id": "tenet-1",
                    "number": 1,
                    "title": "First",
                    "severity": "critical",
                    "enforcement": {"status": "enforced", "mechanism": "gate.py", "gate_id": "g1"},
                    "agents_md": "1. **First.** Line one\n   line two",
                    "tenets_md": "## 1. First\nFull body one.",
                },
                {
                    "id": "tenet-2",
                    "number": 2,
                    "title": "Second",
                    "severity": "normal",
                    "enforcement": {"status": "prose", "mechanism": "convention", "gate_id": None},
                    "agents_md": "2. **Second.** Only line",
                    "tenets_md": "## 2. Second\nFull body two.",
                },
            ]
        },
        "practices": {
            "preamble": "Intro paragraph.\nSecond intro line.",
            "rules": [
                {
                    "id": "practice-tdd",
                    "title": "TDD",
                    "severity": "critical",
                    "enforcement": {
                        "status": "enforced",
                        "mechanism": "pytest",
                        "gate_id": "ci-tests",
                    },
                    "agents_md": "- **TDD** — tests first\n  continued",
                },
                {
                    "id": "practice-iac",
                    "title": "IaC",
                    "severity": "high",
                    "enforcement": {"status": "prose", "mechanism": "terraform", "gate_id": None},
                    "agents_md": "- **IaC** — terraform",
                },
            ],
        },
        "dod": {
            "preamble": "DoD intro.\n\n| When | Update |\n|---|---|",
            "postamble": "**Done means:** stuff.",
            "rules": [
                {
                    "id": "dod-01",
                    "title": "A thing",
                    "severity": "high",
                    "enforcement": {"status": "prose", "mechanism": "convention", "gate_id": None},
                    "agents_md": "| A thing | docs |",
                },
            ],
        },
    }


# --------------------------------------------------------------------------- #
# Render join-semantics
# --------------------------------------------------------------------------- #


def test_agents_tenets_join_single_newline() -> None:
    out = rc.render_agents_tenets(_contract())
    assert out == "1. **First.** Line one\n   line two\n2. **Second.** Only line"


def test_full_tenets_join_blank_line() -> None:
    out = rc.render_full_tenets(_contract())
    assert out == "## 1. First\nFull body one.\n\n## 2. Second\nFull body two."


def test_practices_preamble_then_bullets() -> None:
    out = rc.render_practices(_contract())
    assert out == (
        "Intro paragraph.\nSecond intro line.\n\n"
        "- **TDD** — tests first\n  continued\n- **IaC** — terraform"
    )


def test_dod_preamble_rows_postamble() -> None:
    out = rc.render_dod(_contract())
    assert out == (
        "DoD intro.\n\n| When | Update |\n|---|---|\n| A thing | docs |\n\n**Done means:** stuff."
    )


# --------------------------------------------------------------------------- #
# Fence round-trip
# --------------------------------------------------------------------------- #


def test_fence_replace_then_extract_roundtrip() -> None:
    text = "head\n\n<!-- generated:x start -->\nOLD\n<!-- generated:x end -->\n\ntail\n"
    replaced = rc.replace_fenced(text, "x", "NEW\nlines")
    assert "<!-- generated:x start -->\nNEW\nlines\n<!-- generated:x end -->" in replaced
    assert rc.extract_fenced(replaced, "x") == "NEW\nlines"
    # surrounding hand-authored text is preserved
    assert replaced.startswith("head\n\n")
    assert replaced.endswith("\n\ntail\n")


def test_fence_missing_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        rc.extract_fenced("no fences here", "x")


# --------------------------------------------------------------------------- #
# Coverage
# --------------------------------------------------------------------------- #


def test_coverage_counts_and_table_shape() -> None:
    out = rc.render_coverage(_contract())
    assert "**Summary:** 5 rules — 2 enforced · 0 tested · 3 prose." in out
    # table header is immediately followed by the separator (no blank line)
    assert "| id | rule | severity | enforcement | mechanism |\n|---|---|---|---|---|" in out
    assert "`tenet-1`" in out and "`dod-01`" in out
    assert out.endswith("\n")


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def test_validate_clean() -> None:
    assert rc.validate_contract(_contract()) == []


def test_validate_duplicate_id() -> None:
    c = _contract()
    c["practices"]["rules"][0]["id"] = "tenet-1"
    problems = rc.validate_contract(c)
    assert any("duplicate" in p for p in problems)


def test_validate_bad_status() -> None:
    c = _contract()
    c["tenets"]["rules"][0]["enforcement"]["status"] = "wishful"
    problems = rc.validate_contract(c)
    assert any("status" in p for p in problems)


# --------------------------------------------------------------------------- #
# End-to-end on a synthetic repo: render -> check passes -> mutate -> check fails
# --------------------------------------------------------------------------- #


def _write_synth_repo(root: pathlib.Path) -> None:
    import yaml

    contract = root / "contract"
    contract.mkdir(parents=True)
    c = _contract()
    (contract / "tenets.yaml").write_text(yaml.dump({"rules": c["tenets"]["rules"]}), "utf-8")
    (contract / "practices.yaml").write_text(yaml.dump(c["practices"]), "utf-8")
    (contract / "dod.yaml").write_text(yaml.dump(c["dod"]), "utf-8")

    def fence(name: str) -> str:
        return f"<!-- generated:{name} start -->\nPH\n<!-- generated:{name} end -->"

    agents = (
        f"# A\n\n## Tenets\n\n{fence('agents-tenets')}\n\n"
        f"## Practices\n\n{fence('agents-practices')}\n\n"
        f"## DoD\n\n{fence('agents-dod')}\n"
    )
    (root / "AGENTS.md").write_text(agents, "utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "tenets.md").write_text(
        f"# Tenets\n\n{fence('tenets-full')}\n", "utf-8"
    )


def test_main_render_then_check(tmp_path: pathlib.Path) -> None:
    _write_synth_repo(tmp_path)
    # first render fills the fences + writes coverage
    assert rc.main(["--repo-root", str(tmp_path)]) == 0
    # now check must pass (no drift)
    assert rc.main(["--check", "--repo-root", str(tmp_path)]) == 0
    # the coverage report exists
    assert (tmp_path / "docs" / "reports" / "contract-coverage.md").is_file()


def test_main_check_fails_on_drift(tmp_path: pathlib.Path) -> None:
    import yaml

    _write_synth_repo(tmp_path)
    assert rc.main(["--repo-root", str(tmp_path)]) == 0
    # mutate the YAML so the generated prose is now stale
    c = _contract()
    c["tenets"]["rules"][0]["agents_md"] = "1. **First.** CHANGED"
    (tmp_path / "contract" / "tenets.yaml").write_text(
        yaml.dump({"rules": c["tenets"]["rules"]}), "utf-8"
    )
    assert rc.main(["--check", "--repo-root", str(tmp_path)]) == 1


def test_main_missing_contract_dir(tmp_path: pathlib.Path) -> None:
    assert rc.main(["--repo-root", str(tmp_path)]) == 1


# --------------------------------------------------------------------------- #
# Integration: the REAL contract renders byte-equal to the committed prose
# (the no-op-diff guarantee that the lift is faithful — ADR 033 migration step 2)
# --------------------------------------------------------------------------- #


def test_real_contract_is_in_sync() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    if not (repo_root / "contract").is_dir():
        import pytest

        pytest.skip("contract/ not present")
    assert rc.main(["--check", "--repo-root", str(repo_root)]) == 0
