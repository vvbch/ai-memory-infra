#!/usr/bin/env python3
"""Workspace substitute for Cursor's cursor_dialog MCP (user rules).

Cursor's built-in cursor_dialog tool is gated behind the cursor_skill_enabled
feature flag and is not listed in cursor-app-control MCP offerings — agents
cannot call it from this harness. User rules also live in Cursor's cloud
KnowledgeBase API, not in a local git-tracked file.

This script is the control-plane workaround: copy canonical replacement text to
the clipboard and print a one-step operator action so Chandra can paste into
Cursor Settings → Rules.

Spec: docs/coe/2026-06-10-global-workspace-rule-conflict.md § Global rule replacement
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_COE = _REPO_ROOT / "docs/coe/2026-06-10-global-workspace-rule-conflict.md"


def _extract_block(coe_text: str, start_heading: str, end_heading: str | None) -> str:
    heading_match = re.search(re.escape(start_heading), coe_text)
    if not heading_match:
        raise SystemExit(f"Could not find heading {start_heading!r} in {_COE}")
    fence = re.search(r"\n---\s*\n", coe_text[heading_match.end() :])
    if not fence:
        raise SystemExit(f"Could not find --- fence after {start_heading!r} in {_COE}")
    start = heading_match.end() + fence.end()
    if end_heading:
        end_match = re.search(re.escape(end_heading), coe_text[start:])
        if not end_match:
            raise SystemExit(f"Could not find end heading {end_heading!r} in {_COE}")
        return coe_text[start : start + end_match.start()].strip()
    return coe_text[start:].strip()


def commit_rule_text() -> str:
    coe = _COE.read_text(encoding="utf-8")
    return _extract_block(
        coe,
        "## Global rule replacement",
        "In **`creating-pull-requests`**",
    )


def pr_rule_exception_text() -> str:
    coe = _COE.read_text(encoding="utf-8")
    marker = "In **`creating-pull-requests`**"
    idx = coe.find(marker)
    if idx == -1:
        raise SystemExit(f"Could not find {marker!r} in {_COE}")
    block = coe[idx + len(marker) :].strip()
    # Take only the blockquote paragraph (skip the intro line above it).
    lines: list[str] = []
    for line in block.splitlines():
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
    for cmd in (
        ["pbcopy"],
        ["xclip", "-selection", "clipboard"],
        ["wl-copy"],
    ):
        try:
            subprocess.run(cmd, input=text, text=True, check=True)
            return
        except FileNotFoundError:
            continue
    raise SystemExit("No clipboard command found (clip/pbcopy/xclip/wl-copy).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Print replacement texts")
    show.add_argument(
        "which",
        choices=("commit", "pr-exception", "all"),
        nargs="?",
        default="all",
    )

    copy = sub.add_parser("copy", help="Copy replacement text to clipboard")
    copy.add_argument(
        "which",
        choices=("commit", "pr-exception"),
    )

    sub.add_parser(
        "why-unavailable",
        help="Explain why cursor_dialog MCP is not exposed here",
    )

    args = parser.parse_args()

    if args.command == "why-unavailable":
        print(
            "cursor_dialog is implemented in Cursor's built-in cursor-app-control MCP "
            "but is NOT listed in listOfferings() — only move_agent_to_root, "
            "create_project, rename_chat, etc. are advertised to agents.\n"
            "The handler exists behind feature gate cursor_skill_enabled; this harness "
            "does not expose it as a callable tool.\n"
            "Global user rules are stored in Cursor's cloud KnowledgeBase API, not in "
            "this repo. Workaround: python scripts/cursor_user_rules.py copy commit "
            "then paste into Cursor Settings → Rules."
        )
        return 0

    if args.command == "show":
        if args.which in ("commit", "all"):
            print("=== committing-changes-with-git replacement ===\n")
            print(commit_rule_text())
        if args.which in ("pr-exception", "all"):
            if args.which == "all":
                print("\n=== creating-pull-requests exception line ===\n")
            print(pr_rule_exception_text())
        return 0

    text = commit_rule_text() if args.which == "commit" else pr_rule_exception_text()
    copy_to_clipboard(text)
    label = "commit rule" if args.which == "commit" else "PR-rule exception"
    print(f"Copied {label} replacement to clipboard ({len(text)} chars).")
    print("Paste into Cursor Settings > Rules, then save.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
