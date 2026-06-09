#!/usr/bin/env python3
"""Operator Assistant concierge-action formatter — canonical, editor-agnostic.

WHY THIS EXISTS
---------------
When the agent hits a step it genuinely cannot do itself (a console click, a
secret the operator must paste, a paid/one-way-door decision), it must hand
Chandra **exactly one** action in the concierge format that AGENTS.md mandates
("Operator-delegated action format"):

  1. ELI5 purpose                          — why this matters, in plain English
  2. exact UI path or command              — the precise thing to click/type/run
  3. visible success condition             — what he'll see that proves it worked
  4. "tell me what you see"                 — the wait point; one step, then stop

AGENTS.md is explicit: "If any of those four are unknown, verify first; do not
hand him a vague 'confirm it' instruction." And "No resume prompt while waiting
on Chandra." Those rules were prose the LLM had to remember — and a model
forgot them, producing a vague "confirm it" instruction and a premature resume
prompt (COE 2026-06-09-concierge-handoff-regression.md). This skill turns that
prose into a deterministic mechanism: it validates the four parts (rejecting
empty *and* vague values), enforces ONE step (no multi-step dumps), and renders
a clean operator block — so a delegated action can't silently drop a part or
balloon into a checklist.

This is the Operator Assistant counterpart to the Build Agent's
``session_checkpoint.py`` / ``completion_gate.py``: same shape (format + a
``--check`` gate + ``--json``), aimed at operator-facing handoffs instead of
repo handoffs.

SKILL CONTRACT (docs/agent-personas.md)
---------------------------------------
* Owner persona  : Operator Assistant.
* Pain removed   : vague "confirm it" delegations; missing success criteria;
                   multi-step dumps; a resume prompt printed mid-flow.
* May store/write: the rendered operator action block (purpose, action,
                   success, wait) and the date.
* Must never write: secrets, API keys, recovery codes, passwords, or any copied
                   vault value. The action text must POINT at where a secret
                   lives (Bitwarden folder), never contain it.
* Success cond.  : ``--check`` passes — all four parts present, none vague, and
                   the action is a single step — so the block is safe to show.
* Canonical truth: AGENTS.md "How to teach / collaborate" + docs/agent-personas
                   .md Operator Assistant success criteria.

PORTABILITY (tenet 2) / CROSS-PLATFORM (tenet 3)
------------------------------------------------
Pure Python stdlib; no shell-isms; UTF-8 forced so Windows consoles never crash
on em dashes / check marks. No editor coupling — any harness or a human runs it.

USAGE
-----
  # Validate before showing the operator anything (exit 1 if not concierge-safe):
  python scripts/operator_action.py --check \
      --purpose "..." --action "..." --success "..."

  # Render the single operator action block:
  python scripts/operator_action.py \
      --purpose "Save the master API key off the server so it's never lost" \
      --action  "Open Bitwarden, unlock, open the 'ai-memory-infra' folder" \
      --success "You see an item named 'ADMIN_API_KEY' with a 43-character value" \
      --wait    "Tell me what you see and we'll continue."

  # Machine-readable:
  python scripts/operator_action.py --json --purpose ... --action ... --success ...
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import json
import re
import sys

# The four parts AGENTS.md requires. ``wait`` has a safe default, so only the
# first three are operator-supplied requirements.
REQUIRED_PARTS = ("purpose", "action", "success")
DEFAULT_WAIT = "Tell me what you see and we'll continue."

# Phrases that make a delegated action non-actionable. AGENTS.md bans the vague
# "confirm it" class outright; these catch the common offenders in the *action*
# and *success* fields (matched as whole phrases, case-insensitively).
VAGUE_PHRASES = (
    "confirm it",
    "confirm that",
    "verify it",
    "verify that",
    "check it",
    "check that it",
    "make sure",
    "ensure it",
    "as needed",
    "if necessary",
    "etc.",
    "and so on",
    "do the needful",
    "set it up",
    "configure it",
    "handle it",
    "take care of",
    "somewhere",
    "the usual",
)

# Signals that a single "action" is really several steps. One step at a time is
# the core concierge rule, so these fail the gate (the agent should split them).
MULTISTEP_PATTERNS = (
    r"\bthen\b",
    r"\bafter that\b",
    r"\bnext,",
    r"\bfollowed by\b",
    r"^\s*\d+[.)]\s",        # a numbered list ("1. ...")
    r"\n\s*\d+[.)]\s",       # a numbered list mid-string
    r"\n\s*[-*]\s",          # a bulleted list
    r";\s*\S",               # semicolon-chained imperatives
)


# --------------------------------------------------------------------------- #
# Validation — the concierge contract.
# --------------------------------------------------------------------------- #
def _find_vague(text: str) -> list[str]:
    low = text.lower()
    return [p for p in VAGUE_PHRASES if p in low]


def _is_multistep(text: str) -> bool:
    flags = re.IGNORECASE | re.MULTILINE
    return any(re.search(pat, text, flags=flags) for pat in MULTISTEP_PATTERNS)


def validate(parts: dict) -> list[str]:
    """Return concierge-contract violations (empty == safe to show the operator)."""
    problems: list[str] = []

    for part in REQUIRED_PARTS:
        value = (parts.get(part) or "").strip()
        if not value:
            problems.append(f"missing required part: --{part}")
            continue
        vague = _find_vague(value)
        if vague:
            problems.append(
                f"--{part} is vague (rephrase to a concrete instruction): "
                f"contains {', '.join(repr(v) for v in vague)}"
            )

    action = (parts.get("action") or "").strip()
    if action and _is_multistep(action):
        problems.append(
            "--action looks like more than one step; concierge mode is one step at a "
            "time — give a single action and wait, then issue the next"
        )

    return problems


# --------------------------------------------------------------------------- #
# Rendering.
# --------------------------------------------------------------------------- #
def _today() -> str:
    return _dt.date.today().isoformat()


def render(parts: dict) -> str:
    """Render the single operator-action block (concierge format)."""
    wait = (parts.get("wait") or "").strip() or DEFAULT_WAIT
    out = [
        f"OPERATOR ACTION (one step) — {_today()}",
        "",
        f"Why (ELI5): {parts.get('purpose', '').strip()}",
        "",
        "Do exactly this:",
        f"  {parts.get('action', '').strip()}",
        "",
        "You'll know it worked when:",
        f"  {parts.get('success', '').strip()}",
        "",
        f"Then: {wait}",
    ]
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def _parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="operator_action",
        description="Operator Assistant concierge-action formatter "
        "(purpose + exact action + visible success + wait point).",
    )
    p.add_argument("--purpose", default="", help="ELI5 why this step matters")
    p.add_argument("--action", default="", help="the exact single UI path or command")
    p.add_argument("--success", default="", help="the visible success condition")
    p.add_argument(
        "--wait",
        default="",
        help=f"the wait-point prompt (default: {DEFAULT_WAIT!r})",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="only validate the concierge contract; exit 1 if not concierge-safe",
    )
    p.add_argument("--json", action="store_true", help="machine-readable output")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

    args = _parse(argv)
    parts = {
        "purpose": args.purpose,
        "action": args.action,
        "success": args.success,
        "wait": args.wait,
    }
    problems = validate(parts)

    if args.check:
        if not problems:
            print("operator-action: concierge contract PASS — safe to show the operator.")
            return 0
        print("operator-action: concierge contract FAIL:")
        for prob in problems:
            print(f"  - {prob}")
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "date": _today(),
                    "parts": {**parts, "wait": (parts["wait"].strip() or DEFAULT_WAIT)},
                    "contract_ok": not problems,
                    "problems": problems,
                    "rendered": render(parts) if not problems else None,
                },
                indent=2,
            )
        )
        return 0 if not problems else 1

    if problems:
        print("operator-action: NOT concierge-safe — fix before showing the operator:")
        for prob in problems:
            print(f"  - {prob}")
        return 1

    print(render(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
