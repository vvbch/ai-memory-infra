#!/usr/bin/env python3
"""Deterministic STATUS.md snapshot-shape gate (COE 2026-06-10-status-snapshot-log-drift).

WHY THIS EXISTS
---------------
``docs/planning/STATUS.md`` is contractually a **resumable snapshot, overwritten
each session** (its own header; tenet 16; AGENTS.md DoD "End of any working
session" row says *overwrite*). The append-only history journal is the private
``BUILD-LOG.md``. But "overwrite" lived only as prose, executed by LLM judgment
— so sessions *prepended* instead of overwriting, and STATUS accreted ~25
"Prior update" blocks and a dozen dated "Last decisions" sections (~1,340
lines), becoming a second, drifting log (tenet 10 violation).

Same lesson as ``completion_gate.py`` (ADR 027): a rule that matters must be a
mechanism, not a hope. This script validates the *shape* of STATUS.md and fails
loudly when it is turning back into a journal. It checks SHAPE only — it never
judges or rewrites content (the agent owns content; this is the tripwire).

CONTRACT (what makes STATUS a snapshot)
---------------------------------------
1. No ``**Prior update:**`` blocks — superseded narrative is BUILD-LOG material.
2. Exactly one ``**Last updated:**`` line.
3. At most one ``## Done this session`` and one ``## Last decisions`` section —
   the *current* session's; older ones live in BUILD-LOG / docs/decisions/.
4. Total length under a hard cap (default 400 lines) — a snapshot you cannot
   read in one sitting is not a snapshot.

Wired as pre-commit gate 3 (this repo) and a CI step. Exit 0 = snapshot-shaped;
exit 1 = log drift detected, with one actionable line per violation.

CROSS-PLATFORM (tenet 3): pure Python stdlib.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_MAX_LINES = 400

# Markers whose *presence at all* means history is accreting in the snapshot.
FORBIDDEN_MARKERS = ("**Prior update:**",)

# Section headings allowed at most once (the current session's instance).
SINGLETON_HEADINGS = ("## Done this session", "## Last decisions")

REQUIRED_ONCE = "**Last updated:**"


def _default_status_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "planning" / "STATUS.md"


def check_status(text: str, max_lines: int = DEFAULT_MAX_LINES) -> list[str]:
    """Return a list of violations (empty = STATUS.md is snapshot-shaped)."""
    violations: list[str] = []
    lines = text.splitlines()

    for marker in FORBIDDEN_MARKERS:
        count = sum(1 for line in lines if marker in line)
        if count:
            violations.append(
                f"{count} '{marker}' block(s) found — superseded narrative belongs in the "
                "private BUILD-LOG.md, not STATUS.md (overwrite, don't prepend)."
            )

    updated_count = sum(1 for line in lines if REQUIRED_ONCE in line)
    if updated_count != 1:
        violations.append(
            f"expected exactly one '{REQUIRED_ONCE}' line, found {updated_count}."
        )

    for heading in SINGLETON_HEADINGS:
        count = sum(1 for line in lines if line.startswith(heading))
        if count > 1:
            violations.append(
                f"{count} '{heading}' sections found — keep only the current session's; "
                "move older ones to BUILD-LOG.md / docs/decisions/."
            )

    if len(lines) > max_lines:
        violations.append(
            f"{len(lines)} lines exceeds the {max_lines}-line snapshot cap — STATUS.md is "
            "accreting history; trim to the current snapshot (history is already in "
            "BUILD-LOG.md and git)."
        )

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="STATUS.md to check (default: docs/planning/STATUS.md relative to this repo)",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=DEFAULT_MAX_LINES,
        help=f"hard line cap (default {DEFAULT_MAX_LINES})",
    )
    args = parser.parse_args(argv)

    path = args.path or _default_status_path()
    if not path.is_file():
        print(f"STATUS SNAPSHOT GATE: FAIL — {path} not found.")
        return 1

    violations = check_status(path.read_text(encoding="utf-8"), max_lines=args.max_lines)
    if violations:
        print(f"STATUS SNAPSHOT GATE: FAIL — {path} is drifting from snapshot to log:")
        for v in violations:
            print(f"  - {v}")
        print(
            "\nFix: STATUS.md is OVERWRITTEN each session (tenet 16). Append history to the "
            "private BUILD-LOG.md instead. See docs/coe/2026-06-10-status-snapshot-log-drift.md."
        )
        return 1

    n_lines = len(path.read_text(encoding="utf-8").splitlines())
    print(f"STATUS SNAPSHOT GATE: OK — {path} is snapshot-shaped ({n_lines} lines).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
