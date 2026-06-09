#!/usr/bin/env python3
"""Install IDE startup/handoff hook adapters at the workspace root.

WHY THIS EXISTS
---------------
Cursor (and Claude Code) load *project* hooks from ``<workspace root>/.cursor/``
(resp. ``.claude/``) — the root that is actually open. This project's open root
is the parent ``ai-memory`` workspace, **not** the ``ai-memory-infra`` repo. A
``hooks.json`` placed inside ``ai-memory-infra/.cursor/`` is therefore never
loaded. And the parent workspace is not a git repo, so files written there are
not versioned and do not survive a re-clone.

The project's answer (same model as ADR 015 for git hooks): keep the canonical
logic versioned in ``ai-memory-infra`` (``scripts/session_bootstrap.py`` and
``.cursor/hooks/completion_gate.py``), and keep a *versioned installer* that
(re)writes the thin per-IDE adapter files at the workspace root. The adapters
carry no logic — they only invoke the versioned scripts — so this is consistent
with tenet 2 (editor-agnostic; editor files are thin pointers) and tenet 1
(everything important is versioned + reproducible).

Run after any re-clone or when adding an IDE:
    python ai-memory-infra/scripts/install_ide_hooks.py

CROSS-PLATFORM (tenet 3): pure Python stdlib.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
INFRA_ROOT = _HERE.parents[1]
WORKSPACE_ROOT = _HERE.parents[2]

# Paths are written relative to the WORKSPACE ROOT, because each IDE runs project
# hooks from that root. Forward slashes work on Windows for these tools and keep
# the generated JSON identical cross-platform (tenet 3).
_BOOTSTRAP = "ai-memory-infra/scripts/session_bootstrap.py"
_COMPLETION_GATE = "ai-memory-infra/scripts/completion_gate.py"

# Single source of truth for the hook wiring. Each IDE adapter is generated from
# this so the two surfaces can never drift (tenet 10).
HOOKS = {
    # sessionStart -> inject the compact bootstrap (control plane + Next action)
    # so the agent does not re-read all of STATUS.md to resume (token cost).
    "sessionStart": f'python "{_BOOTSTRAP}" --cursor',
    # stop -> deterministic completion gate (commit/push every touched repo).
    "stop": f'python "{_COMPLETION_GATE}"',
}


def _cursor_hooks_json() -> dict:
    return {
        "version": 1,
        "hooks": {
            "sessionStart": [{"command": HOOKS["sessionStart"]}],
            "stop": [{"command": HOOKS["stop"], "loop_limit": 4}],
        },
    }


def _claude_settings_json() -> dict:
    # Claude Code maps SessionStart/Stop onto the same lifecycle; Cursor also reads
    # .claude/settings.json (third-party hooks). One file therefore covers Claude
    # Code natively and is a redundant backstop under Cursor.
    def _cmd(c: str) -> dict:
        return {"hooks": [{"type": "command", "command": c}]}

    return {
        "hooks": {
            "SessionStart": [_cmd(HOOKS["sessionStart"].replace("--cursor", ""))],
            "Stop": [_cmd(HOOKS["stop"])],
        }
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {path}")


def main() -> int:
    print(f"workspace root : {WORKSPACE_ROOT}")
    print(f"control plane  : {INFRA_ROOT}")
    print("installing IDE startup/handoff adapters (thin pointers to")
    print(f"  {_BOOTSTRAP} / {_COMPLETION_GATE}):")

    _write(WORKSPACE_ROOT / ".cursor" / "hooks.json", _cursor_hooks_json())
    _write(WORKSPACE_ROOT / ".claude" / "settings.json", _claude_settings_json())

    print("")
    print("Done. Cursor reloads hooks.json on save (else restart Cursor); verify")
    print("in Settings -> Hooks or the Hooks output channel.")
    print("VS Code: no native session hook - add the bootstrap as a folder-open")
    print("task. See ai-memory-infra/docs/setup.md (IDE startup hooks).")
    print("Re-run after any re-clone (the parent workspace is not versioned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
