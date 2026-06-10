#!/usr/bin/env python3
"""Print canonical Cursor global user-rule replacement text (control plane).

Cursor user rules are cloud-synced (KnowledgeBase API), not local files.
`cursor_dialog` MCP is not exposed in this harness. Default: **print in chat**
so the operator can copy; optional `copy` subcommand if explicitly requested.

Spec: docs/coe/2026-06-10-global-workspace-rule-conflict.md
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_COE = _REPO_ROOT / "docs/coe/2026-06-10-global-workspace-rule-conflict.md"


def _between_fences(coe_text: str, after: str, before: str | None = None) -> str:
    start_idx = coe_text.find(after)
    if start_idx == -1:
        raise SystemExit(f"Marker not found in {_COE}: {after!r}")
    rest = coe_text[start_idx + len(after) :]
    fences = list(re.finditer(r"\n---\s*\n", rest))
    if not fences:
        raise SystemExit(f"No --- fence after {after!r} in {_COE}")
    body_start = fences[0].end()
    body_end = fences[1].start() if len(fences) > 1 else len(rest)
    if before:
        before_idx = rest.find(before, body_start)
        if before_idx == -1:
            raise SystemExit(f"End marker not found: {before!r}")
        body_end = before_idx
    return rest[body_start:body_end].strip()


def commit_rule_text() -> str:
    return _between_fences(
        _COE.read_text(encoding="utf-8"),
        "Replace that rule's full body with:",
        "If you have a separate user rule about **pull requests**",
    )


def pr_rule_exception_text() -> str:
    coe = _COE.read_text(encoding="utf-8")
    marker = "the commit rule above already covers push for ai-memory):"
    idx = coe.find(marker)
    if idx == -1:
        raise SystemExit(f"PR exception marker not found in {_COE}")
    lines: list[str] = []
    for line in coe[idx + len(marker) :].splitlines():
        if line.startswith("> "):
            lines.append(line[2:])
        elif line.startswith(">"):
            lines.append(line[1:].lstrip())
        elif lines:
            break
    return "\n".join(lines).strip()


def copy_to_clipboard(text: str) -> None:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return
    except Exception:
        pass
    if sys.platform == "win32":
        subprocess.run(["clip"], input=text, text=True, check=True, shell=True)
        return
    for cmd in (["pbcopy"], ["xclip", "-selection", "clipboard"], ["wl-copy"]):
        try:
            subprocess.run(cmd, input=text, text=True, check=True)
            return
        except FileNotFoundError:
            continue
    raise SystemExit("Clipboard unavailable — use printed text from `show` instead.")


def _ensure_utf8_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    _ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Print replacement text (default handoff)")
    show.add_argument(
        "which",
        choices=("commit", "pr-exception", "all"),
        nargs="?",
        default="commit",
    )

    copy = sub.add_parser(
        "copy",
        help="Try clipboard (unreliable from agent shell — prefer show)",
    )
    copy.add_argument("which", choices=("commit", "pr-exception"))

    sub.add_parser("why-unavailable", help="Why cursor_dialog / disk edit fails")

    args = parser.parse_args()

    if args.command == "why-unavailable":
        print(
            "Layers:\n"
            "  1. Workspace rules: AGENTS.md + .cursor/rules (git) — agents CAN fix.\n"
            "  2. Cursor User rules: cloud KnowledgeBase — NOT in local files here;\n"
            "     cursor_dialog MCP not exposed to this harness.\n"
            "  3. Prompt tags like committing-changes-with-git: internal XML names,\n"
            "     NOT Settings UI labels.\n"
            "\n"
            "Filesystem probe (2026-06-10): no 'only create commits' under\n"
            "%AppData%/Cursor or state.vscdb applicationUser blob.\n"
            "\n"
            "Handoff: python scripts/cursor_user_rules.py show commit\n"
            "Then: Settings > Rules > User rules > Add rule (if empty) or edit match."
        )
        return 0

    if args.command == "show":
        if args.which in ("commit", "all"):
            print("=== Suggested Cursor User rule (copy from chat) ===\n")
            print(commit_rule_text())
        if args.which in ("pr-exception", "all"):
            print("\n=== Optional PR-rule exception line ===\n")
            print(pr_rule_exception_text())
        return 0

    text = commit_rule_text() if args.which == "commit" else pr_rule_exception_text()
    try:
        copy_to_clipboard(text)
    except (SystemExit, subprocess.CalledProcessError, OSError) as exc:
        print(f"Clipboard failed ({exc}). Printed text instead:\n")
        print(text)
        return 1
    print(f"Copied to clipboard ({len(text)} chars). Verify with Ctrl+V before relying on it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
