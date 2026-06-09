#!/usr/bin/env python3
"""Portable session-bootstrap context for any IDE/agent harness.

WHY THIS EXISTS
---------------
A fresh agent session opens the parent ``ai-memory`` workspace and then has to
*rediscover* every time that the control plane is ``ai-memory-infra`` and re-read
the large ``AGENTS.md`` + ``STATUS.md`` just to learn the current phase and the
single Next action. That discovery hop is paid in tokens on every session
(context-window amplification, tenet 16).

This script is the **canonical, editor-agnostic** "session setup command": it
emits a compact bootstrap block (where you are, what the control plane is, the
current phase, the Next action, and the repo-health reminder) so a startup hook
can inject it once instead of the agent re-deriving it.

PORTABILITY (tenet 2)
---------------------
This file is the single source of truth. Each IDE only needs a *thin adapter*
that runs it at session start:
  * Cursor / Claude Code  -> ``sessionStart`` hook  (``--cursor`` JSON mode)
  * VS Code / others      -> a task or shell profile (default text mode)
The adapters carry no logic; they just invoke this script. Generate them with
``scripts/install_ide_hooks.py``.

CROSS-PLATFORM (tenet 3): pure Python stdlib, no shell-isms, Mac/Windows alike.

USAGE
-----
  python scripts/session_bootstrap.py            # human/plain-text block
  python scripts/session_bootstrap.py --cursor   # Cursor sessionStart JSON
  python scripts/session_bootstrap.py --json      # raw fields as JSON

The script never raises into the harness: on any failure it degrades to a
minimal pointer so a session can always start.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# This file lives at <workspace>/ai-memory-infra/scripts/session_bootstrap.py
#   parents[0] = scripts/  parents[1] = ai-memory-infra/  parents[2] = <workspace>
_HERE = Path(__file__).resolve()
INFRA_ROOT = _HERE.parents[1]
WORKSPACE_ROOT = _HERE.parents[2]
STATUS = INFRA_ROOT / "docs" / "planning" / "STATUS.md"

# Keep the injected block small — the whole point is to spend *fewer* tokens
# than re-reading STATUS.md (currently ~1k lines). Caps are generous but bounded.
_MAX_PHASE_CHARS = 600
_MAX_NEXT_CHARS = 1600


def _section(md: str, heading: str) -> str:
    """Return the body under a ``## heading`` up to the next ``## `` heading."""
    # Match the heading line, then capture until the next H2 (or EOF).
    pat = re.compile(
        r"^#{2}\s+" + re.escape(heading) + r"\s*$(.*?)(?=^#{2}\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pat.search(md)
    return m.group(1).strip() if m else ""


def _strip_blockquote(text: str) -> str:
    """Drop leading '> ' markers so a blockquoted Next action reads cleanly."""
    lines = [re.sub(r"^\s*>\s?", "", ln) for ln in text.splitlines()]
    return "\n".join(lines).strip()


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + " …(truncated — see STATUS.md)"


def gather() -> dict:
    """Collect bootstrap fields. Always returns a usable dict (never raises)."""
    data = {
        "workspace_root": str(WORKSPACE_ROOT),
        "control_plane": str(INFRA_ROOT),
        "status_file": str(STATUS),
        "phase": "",
        "next_action": "",
    }
    try:
        md = STATUS.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return data

    phase = _section(md, "Current phase")
    if phase:
        # First paragraph of the phase section is the headline.
        first_para = phase.split("\n\n", 1)[0].strip()
        data["phase"] = _clip(first_para, _MAX_PHASE_CHARS)

    nxt = _section(md, "Next action")
    if nxt:
        data["next_action"] = _clip(_strip_blockquote(nxt), _MAX_NEXT_CHARS)

    return data


def render_text(d: dict) -> str:
    parts = [
        "AI-MEMORY SESSION BOOTSTRAP (auto-injected at session start)",
        "",
        "You are in the parent `ai-memory` workspace. The CONTROL PLANE is "
        "`ai-memory-infra` — all planning, rules, ADRs, and STATUS live there.",
        f"  workspace root : {d['workspace_root']}",
        f"  control plane  : {d['control_plane']}",
        "",
        "Before working: read `ai-memory-infra/AGENTS.md` (tenets + working "
        "model) and run repo-health (`scripts/check-repo-health.*`). Full state "
        f"is in `{d['status_file']}` — but the resume essentials are below, so you "
        "do not need to re-read all of STATUS.md just to start.",
    ]
    if d["phase"]:
        parts += ["", "CURRENT PHASE:", d["phase"]]
    if d["next_action"]:
        parts += ["", "NEXT ACTION (from STATUS.md):", d["next_action"]]
    return "\n".join(parts)


def main(argv: list[str]) -> int:
    # Windows consoles default to cp1252; STATUS.md / our text contain non-ASCII
    # (em dashes, check marks). Force UTF-8 so text mode never crashes a session.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        d = gather()
    except Exception:
        # Absolute last-resort fallback: a session must always be able to start.
        d = {
            "workspace_root": str(WORKSPACE_ROOT),
            "control_plane": str(INFRA_ROOT),
            "status_file": str(STATUS),
            "phase": "",
            "next_action": "",
        }

    mode = argv[1] if len(argv) > 1 else "--text"

    if mode == "--cursor":
        # Cursor sessionStart contract: stdout JSON may carry `additional_context`
        # (best-effort — a known Cursor timing bug can drop it) and `env` (stable,
        # passed to later hooks). We set both so the bootstrap survives the bug:
        # the env vars are always available even if the context injection is lost.
        sys.stdout.write(json.dumps({
            "additional_context": render_text(d),
            "env": {
                "AI_MEMORY_CONTROL_PLANE": d["control_plane"],
                "AI_MEMORY_STATUS_FILE": d["status_file"],
            },
        }))
    elif mode == "--json":
        sys.stdout.write(json.dumps(d, indent=2))
    else:
        sys.stdout.write(render_text(d))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
