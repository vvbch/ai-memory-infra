#!/usr/bin/env python3
"""Pointer-file purity gate (ADR 018 enforcement; ADR 033 backlog #3).

WHY THIS EXISTS
---------------
Tenet 2 + ADR 018: an editor pointer file (an ``alwaysApply`` Cursor rule,
``CLAUDE.md``) must carry **zero canonical content** — only the editor's
frontmatter/mechanics plus "read ``AGENTS.md``". ADR 018 fixed the *spec* after
``.cursor/rules/00-project.mdc`` had grown a summarized copy of the tenets (COE
2026-06-07-cursor-rule-drift), but explicitly **parked the automated guard**:
"a lint/CI check that fails if a pointer file exceeds N lines or contains
tenet/rule keywords." This is that guard — a stated principle is not a control
until it has teeth (tenet 14).

SCOPE (deliberate)
------------------
Only files that are *contractually* pure pointers:
  * ``.cursor/rules/*.mdc`` with ``alwaysApply: true`` (always-on context), and
  * ``CLAUDE.md`` (Claude Code / VS Code auto-load).
Narrowly **glob-scoped** helper rules (``globs:`` frontmatter) are intentionally
out of scope here — whether they may carry conventions at all is a separate
decision (parked in BACKLOG), not silently enforced/deleted by this gate
(tenet 17: don't unilaterally rewrite curated content).

WHAT IT CHECKS (per pure-pointer file)
--------------------------------------
1. It points: the body references ``AGENTS.md``.
2. It is thin: non-blank body lines <= cap (default 14).
3. It carries no canonical content: no numbered tenet enumeration
   (``1. **...**``), no DoD-style table (``|---``), no ``##`` section headings.

Exit 0 = every pure pointer is thin; exit 1 = a pointer is drifting into content.

CROSS-PLATFORM (tenet 3): pure Python stdlib.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_MAX_BODY_LINES = 14

_NUMBERED_RULE = re.compile(r"^\s*\d+\.\s+\*\*")  # "1. **Everything versioned.**"
_TABLE_SEP = re.compile(r"\|-{2,}")  # "|---|" DoD trigger table
_H2_PLUS = re.compile(r"^#{2,}\s")  # "## Section" canonical-content heading


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter, body). frontmatter is None when there is no ``---`` block."""
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    return None, text  # malformed (no closing fence) -> treat all as body


def is_always_applied(frontmatter: str | None) -> bool:
    if not frontmatter:
        return False
    return bool(re.search(r"^\s*alwaysApply:\s*true\s*$", frontmatter, re.MULTILINE))


def check_pointer(name: str, text: str, max_lines: int = DEFAULT_MAX_BODY_LINES) -> list[str]:
    """Return violations for a single pure-pointer file."""
    violations: list[str] = []
    _, body = split_frontmatter(text)

    if "AGENTS.md" not in body:
        violations.append(f"{name}: a pointer must reference AGENTS.md (it points nowhere).")

    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    if len(body_lines) > max_lines:
        violations.append(
            f"{name}: {len(body_lines)} non-blank body lines exceeds the {max_lines}-line "
            "pointer cap — a pointer restates nothing; move content to AGENTS.md (ADR 018)."
        )

    for ln in body.splitlines():
        if _NUMBERED_RULE.match(ln):
            violations.append(
                f"{name}: contains a numbered rule/tenet enumeration "
                f"({ln.strip()[:48]!r}) — canonical content belongs in AGENTS.md (ADR 018)."
            )
            break
    if any(_TABLE_SEP.search(ln) for ln in body.splitlines()):
        violations.append(
            f"{name}: contains a markdown table (DoD-style) — "
            "pointer files carry no tables (ADR 018)."
        )
    for ln in body.splitlines():
        if _H2_PLUS.match(ln):
            violations.append(
                f"{name}: contains a '##' section heading ({ln.strip()[:48]!r}) — "
                "pointer files have no content sections (ADR 018)."
            )
            break

    return violations


def pure_pointer_files(repo: Path) -> list[Path]:
    """Discover the files that are contractually pure pointers in this repo."""
    files: list[Path] = []
    rules_dir = repo / ".cursor" / "rules"
    if rules_dir.is_dir():
        for mdc in sorted(rules_dir.glob("*.mdc")):
            fm, _ = split_frontmatter(mdc.read_text(encoding="utf-8"))
            if is_always_applied(fm):
                files.append(mdc)
    claude = repo / "CLAUDE.md"
    if claude.is_file():
        files.append(claude)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_BODY_LINES)
    args = parser.parse_args(argv)

    repo = args.repo_root or _repo_root()
    files = pure_pointer_files(repo)
    all_violations: list[str] = []
    for path in files:
        rel = path.relative_to(repo).as_posix()
        all_violations += check_pointer(rel, path.read_text(encoding="utf-8"), args.max_lines)

    if all_violations:
        print("POINTER PURITY GATE: FAIL — an editor pointer file is drifting into content:")
        for v in all_violations:
            print(f"  - {v}")
        print(
            "\nFix: strip the pointer back to frontmatter + 'read AGENTS.md'. Canonical "
            "content lives only in AGENTS.md (tenet 2/10, ADR 018)."
        )
        return 1

    n = len(files)
    print(
        f"POINTER PURITY GATE: OK — {n} pure pointer file(s) carry no canonical "
        "content (ADR 018)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
