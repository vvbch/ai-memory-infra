#!/usr/bin/env python3
"""Render the operating contract from its structured single-source (ADR 033).

WHY THIS EXISTS
---------------
Adherence to the operating contract *varies by model*: it is delivered as ~900
lines of prose in ``AGENTS.md`` + ``docs/tenets.md`` that the model must read and
*choose* to follow (a weak, model-dependent interface). ADR 033 makes the
contract a **structured single-source** (``contract/*.yaml``) that both (a)
renders the human-readable prose sections and (b) is the registry the
deterministic gates check against, with an ``enforcement.status`` per rule so the
model-dependent surface is *measured*, not hidden.

WHAT THIS DOES
--------------
* **render** (default): regenerates the fenced sections of ``AGENTS.md`` and
  ``docs/tenets.md`` from ``contract/*.yaml`` and writes
  ``docs/reports/contract-coverage.md``.
* **--check**: fails (exit 1) if any generated section is stale vs the YAML — so
  drift between the structured source and the prose is impossible by construction
  (closes the ADR 018 / pointer-drift class for these sections). Wired into
  pre-commit + CI.

The YAML carries each rule's prose **verbatim** (a faithful lift — byte-equal to
the prior hand-authored prose) plus structured metadata (stable id, severity,
``enforcement``). Only the *enumerable* sections are templated (tenets, practices,
DoD trigger table); teaching/concierge narrative stays hand-authored prose
outside the fences (ADR 033 "Out of scope").

CROSS-PLATFORM (tenet 3): pure Python + PyYAML; no shell-isms, LF newlines.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# --------------------------------------------------------------------------- #
# Layout
# --------------------------------------------------------------------------- #


def _repo_root() -> Path:
    # <repo>/scripts/render_contract.py
    return Path(__file__).resolve().parents[1]


CONTRACT_DIRNAME = "contract"
COVERAGE_RELPATH = "docs/reports/contract-coverage.md"

VALID_STATUSES = ("enforced", "tested", "prose")


@dataclass(frozen=True)
class Region:
    """One generated, fenced region inside a markdown file."""

    relpath: str  # file, relative to repo root
    marker: str  # <!-- generated:<marker> start/end -->
    kind: str  # which render_* function produces its content


REGIONS: tuple[Region, ...] = (
    Region("AGENTS.md", "agents-tenets", "agents_tenets"),
    Region("AGENTS.md", "agents-practices", "practices"),
    Region("AGENTS.md", "agents-dod", "dod"),
    Region("docs/tenets.md", "tenets-full", "full_tenets"),
)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


def load_contract(contract_dir: Path) -> dict[str, Any]:
    """Load every contract/*.yaml into a dict keyed by stem (tenets/practices/dod...)."""
    contract: dict[str, Any] = {}
    for path in sorted(contract_dir.glob("*.yaml")):
        contract[path.stem] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return contract


# --------------------------------------------------------------------------- #
# Rendering — each returns the EXACT content that belongs between the fences
# (no leading/trailing newline; the fence writer adds those).
# --------------------------------------------------------------------------- #


def render_agents_tenets(contract: dict[str, Any]) -> str:
    """AGENTS.md numbered tenet summary (tight list, items joined by a single \\n)."""
    rules = contract["tenets"]["rules"]
    return "\n".join(r["agents_md"] for r in rules)


def render_full_tenets(contract: dict[str, Any]) -> str:
    """docs/tenets.md full tenets (## headings, blank-line separated)."""
    rules = contract["tenets"]["rules"]
    return "\n\n".join(r["tenets_md"] for r in rules)


def render_practices(contract: dict[str, Any]) -> str:
    """AGENTS.md engineering practices: intro paragraph + bullet list."""
    section = contract["practices"]
    bullets = "\n".join(r["agents_md"] for r in section["rules"])
    return f"{section['preamble']}\n\n{bullets}"


def render_dod(contract: dict[str, Any]) -> str:
    """AGENTS.md Definition-of-Done: intro + table header + rows + 'Done means' footer."""
    section = contract["dod"]
    rows = "\n".join(r["agents_md"] for r in section["rules"])
    return f"{section['preamble']}\n{rows}\n\n{section['postamble']}"


RENDERERS = {
    "agents_tenets": render_agents_tenets,
    "full_tenets": render_full_tenets,
    "practices": render_practices,
    "dod": render_dod,
}


# --------------------------------------------------------------------------- #
# Fence handling
# --------------------------------------------------------------------------- #


def _markers(marker: str) -> tuple[str, str]:
    return (
        f"<!-- generated:{marker} start -->",
        f"<!-- generated:{marker} end -->",
    )


def extract_fenced(text: str, marker: str) -> str:
    """Return the current content between the fences (one surrounding newline stripped)."""
    start, end = _markers(marker)
    si = text.find(start)
    ei = text.find(end)
    if si == -1 or ei == -1 or ei < si:
        raise ValueError(f"fence '{marker}' not found (or malformed) in target file")
    inner = text[si + len(start) : ei]
    # inner is "\n" + content + "\n"; strip exactly one newline each side.
    if inner.startswith("\n"):
        inner = inner[1:]
    if inner.endswith("\n"):
        inner = inner[:-1]
    return inner


def replace_fenced(text: str, marker: str, content: str) -> str:
    """Replace the content between the fences with ``content`` (newline-padded)."""
    start, end = _markers(marker)
    si = text.find(start)
    ei = text.find(end)
    if si == -1 or ei == -1 or ei < si:
        raise ValueError(f"fence '{marker}' not found (or malformed) in target file")
    return f"{text[: si + len(start)]}\n{content}\n{text[ei:]}"


# --------------------------------------------------------------------------- #
# Coverage report
# --------------------------------------------------------------------------- #

COVERAGE_HEADER = """# Contract enforcement coverage

> **GENERATED by `scripts/render_contract.py` from `contract/*.yaml` — do not edit by hand.**
> Run `python scripts/render_contract.py` to regenerate; `--check` fails pre-commit + CI on drift.
> Honesty model mirrors `docs/interfaces.md`: **enforced** (a deterministic gate
> fails on violation, model-independent) · **tested** (covered by tests, no gate) ·
> **prose** (relies on the agent reading and honoring it — the model-dependent
> surface ADR 033 exists to shrink).
"""


def _all_rules(contract: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Flatten to (section_label, rule) pairs in render order."""
    out: list[tuple[str, dict[str, Any]]] = []
    labels = {
        "tenets": "Tenets",
        "practices": "Engineering practices",
        "dod": "Definition of Done (triggers)",
    }
    for stem in ("tenets", "practices", "dod"):
        section = contract.get(stem)
        if not section:
            continue
        for rule in section["rules"]:
            out.append((labels[stem], rule))
    return out


def _coverage_row(rule: dict[str, Any]) -> str:
    enf = rule.get("enforcement", {})
    status = enf.get("status", "prose")
    mechanism = enf.get("mechanism") or "—"
    title = rule.get("title") or rule.get("id", "")
    severity = rule.get("severity", "normal")
    return f"| `{rule['id']}` | {title} | {severity} | **{status}** | {mechanism} |"


_TABLE_HEAD = "| id | rule | severity | enforcement | mechanism |\n|---|---|---|---|---|"


def render_coverage(contract: dict[str, Any]) -> str:
    rules = _all_rules(contract)
    counts = {s: 0 for s in VALID_STATUSES}
    for _, rule in rules:
        status = rule.get("enforcement", {}).get("status", "prose")
        counts[status] = counts.get(status, 0) + 1

    summary = (
        f"**Summary:** {len(rules)} rules — "
        f"{counts['enforced']} enforced · {counts['tested']} tested · {counts['prose']} prose."
    )

    # Build one block per section (heading + table header + rows, no blank lines
    # inside the table — a blank between header and separator breaks markdown).
    blocks: dict[str, list[str]] = {}
    order: list[str] = []
    for label, rule in rules:
        if label not in blocks:
            blocks[label] = [f"## {label}", _TABLE_HEAD]
            order.append(label)
        blocks[label].append(_coverage_row(rule))

    parts = [COVERAGE_HEADER.rstrip("\n"), summary]
    parts.extend("\n".join(blocks[label]) for label in order)
    return "\n\n".join(parts) + "\n"


# --------------------------------------------------------------------------- #
# Top-level render / check
# --------------------------------------------------------------------------- #


def render_region(contract: dict[str, Any], region: Region) -> str:
    return RENDERERS[region.kind](contract)


def planned_outputs(repo_root: Path, contract: dict[str, Any]) -> dict[Path, str]:
    """Compute the desired full text of every generated file (fenced + coverage)."""
    outputs: dict[Path, str] = {}

    # Fenced regions, grouped per file so multiple regions in one file compose.
    by_file: dict[str, list[Region]] = {}
    for region in REGIONS:
        by_file.setdefault(region.relpath, []).append(region)

    for relpath, regions in by_file.items():
        path = repo_root / relpath
        text = outputs.get(path, path.read_text(encoding="utf-8"))
        for region in regions:
            text = replace_fenced(text, region.marker, render_region(contract, region))
        outputs[path] = text

    outputs[repo_root / COVERAGE_RELPATH] = render_coverage(contract)
    return outputs


def write_outputs(outputs: dict[Path, str]) -> list[Path]:
    """Write files whose content changed; return the list of changed paths."""
    changed: list[Path] = []
    for path, content in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            changed.append(path)
    return changed


def check_outputs(outputs: dict[Path, str]) -> list[str]:
    """Return human-readable violations where on-disk content differs from rendered."""
    violations: list[str] = []
    for path, content in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            violations.append(path.as_posix())
    return violations


def validate_contract(contract: dict[str, Any]) -> list[str]:
    """Structural sanity checks on the YAML itself (ids unique, status valid)."""
    problems: list[str] = []
    seen: set[str] = set()
    for _, rule in _all_rules(contract):
        rid = rule.get("id")
        if not rid:
            problems.append("a rule is missing an 'id'")
            continue
        if rid in seen:
            problems.append(f"duplicate rule id: {rid}")
        seen.add(rid)
        status = rule.get("enforcement", {}).get("status")
        if status not in VALID_STATUSES:
            problems.append(f"{rid}: enforcement.status '{status}' not in {VALID_STATUSES}")
    return problems


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail (exit 1) if any generated file is stale vs contract/*.yaml (CI/pre-commit)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repo root (default: inferred from this script's location)",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root or _repo_root()
    contract_dir = repo_root / CONTRACT_DIRNAME
    if not contract_dir.is_dir():
        print(f"CONTRACT RENDER: FAIL — {contract_dir} not found.")
        return 1

    contract = load_contract(contract_dir)
    problems = validate_contract(contract)
    if problems:
        print("CONTRACT RENDER: FAIL — contract/*.yaml is invalid:")
        for p in problems:
            print(f"  - {p}")
        return 1

    outputs = planned_outputs(repo_root, contract)

    if args.check:
        stale = check_outputs(outputs)
        if stale:
            print("CONTRACT RENDER GATE: FAIL — generated docs are stale vs contract/*.yaml:")
            for s in stale:
                print(f"  - {s}")
            print(
                "\nFix: run `python scripts/render_contract.py` and commit the result. "
                "The contract/*.yaml is the single source; the prose is generated (ADR 033)."
            )
            return 1
        print("CONTRACT RENDER GATE: OK — generated docs match contract/*.yaml (ADR 033).")
        return 0

    changed = write_outputs(outputs)
    if changed:
        print("CONTRACT RENDER: wrote")
        for c in sorted(changed):
            print(f"  - {c.as_posix()}")
    else:
        print("CONTRACT RENDER: OK — already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
