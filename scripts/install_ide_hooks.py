#!/usr/bin/env python3
"""Install IDE startup/handoff hook adapters at the workspace root.

WHY THIS EXISTS
---------------
Every coding-agent harness loads *project* hooks from the **open workspace root**
(Cursor from ``.cursor/``, Claude Code from ``.claude/``, Codex from ``.codex/``,
Gemini CLI from ``.gemini/``, Grok from ``.grok/``). This project's open root is
the parent ``ai-memory`` workspace, **not** the ``ai-memory-infra`` repo — and that
parent is not a git repo, so files written there are not versioned and do not
survive a re-clone.

The project's answer (same model as ADR 015 for git hooks, ADR 030 for these):
keep the canonical logic versioned in ``ai-memory-infra`` (``scripts/
session_bootstrap.py`` and ``scripts/completion_gate.py``), and keep a *versioned
installer* that (re)writes the thin per-IDE adapter files at the workspace root.
The adapters carry no logic — they only invoke the versioned scripts with the
right per-harness flag — so this stays consistent with tenet 2 (editor-agnostic;
editor files are thin pointers) and tenet 1 (everything important is versioned +
reproducible).

PER-HARNESS CONTRACTS (verified, tenet 8)
-----------------------------------------
The session-start and turn-end *output contracts* differ by harness, so the
adapters point each event at the matching script mode (one source of truth, no
drift — tenet 10):
  * Cursor       sessionStart ``--cursor`` (additional_context + env)
                 stop         default      (followup_message), loop_limit 4
  * Claude Code  SessionStart plain text   (stdout injected as context)
                 Stop         default      (followup_message)
  * Codex        SessionStart ``--hookspecific`` (hookSpecificOutput.additionalContext)
                 Stop         ``--decision``     (decision: block + reason)
  * Gemini CLI   SessionStart ``--hookspecific``
                 (no blocking per-turn stop — SessionEnd is advisory-only; the
                  gate is intentionally NOT wired for Gemini. ADR 030.)
  * Grok         SessionStart ``--hookspecific``
                 Stop         ``--decision``
                 (best-effort: the Grok CLI ecosystem is fragmented across
                  several incompatible config schemas; this writes the common
                  nested Claude-style ``.grok/settings.json``. Verify with
                  ``grok inspect`` / ``/hooks`` and adjust if your CLI differs.)

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


def _py(script: str, *flags: str) -> str:
    """A `python "<script>" <flags...>` command string for an adapter."""
    tail = (" " + " ".join(flags)) if flags else ""
    return f'python "{script}"{tail}'


# Single source of truth for the canonical commands. Each adapter is generated
# from these so the surfaces can never drift (tenet 10).
BOOT_CURSOR = _py(_BOOTSTRAP, "--cursor")
BOOT_PLAIN = _py(_BOOTSTRAP)
BOOT_HOOKSPEC = _py(_BOOTSTRAP, "--hookspecific")
GATE_CURSOR = _py(_COMPLETION_GATE)
GATE_DECISION = _py(_COMPLETION_GATE, "--decision")


# ---- per-IDE adapter builders ---------------------------------------------
# Each returns (relative_path, json_payload). The schema is the harness's own.

def _cursor() -> tuple[str, dict]:
    return ".cursor/hooks.json", {
        "version": 1,
        "hooks": {
            "sessionStart": [{"command": BOOT_CURSOR}],
            "stop": [{"command": GATE_CURSOR, "loop_limit": 4}],
        },
    }


def _claude() -> tuple[str, dict]:
    # Claude Code maps SessionStart/Stop onto its lifecycle; Cursor also reads
    # .claude/settings.json (third-party hooks), so this one file covers Claude
    # Code natively and is a redundant backstop under Cursor.
    def _cmd(c: str) -> dict:
        return {"hooks": [{"type": "command", "command": c}]}

    return ".claude/settings.json", {
        "hooks": {
            "SessionStart": [_cmd(BOOT_PLAIN)],
            "Stop": [_cmd(GATE_CURSOR)],
        }
    }


def _codex() -> tuple[str, dict]:
    # Codex discovers `.codex/hooks.json` next to a trusted project config layer.
    # SessionStart matcher fires on fresh start + resume; Stop uses the
    # decision/block continuation contract.
    return ".codex/hooks.json", {
        "hooks": {
            "SessionStart": [{
                "matcher": "startup|resume",
                "hooks": [{
                    "type": "command",
                    "command": BOOT_HOOKSPEC,
                    "statusMessage": "Loading ai-memory session bootstrap",
                }],
            }],
            "Stop": [{
                "hooks": [{
                    "type": "command",
                    "command": GATE_DECISION,
                    "timeout": 30,
                }],
            }],
        }
    }


def _gemini() -> tuple[str, dict]:
    # Gemini CLI hooks live in `.gemini/settings.json`. SessionStart injects
    # context via hookSpecificOutput.additionalContext. Gemini has no blocking
    # per-turn stop (SessionEnd is advisory-only), so the gate is not wired here.
    return ".gemini/settings.json", {
        "hooks": {
            "SessionStart": [{
                "matcher": "startup",
                "hooks": [{
                    "name": "ai-memory-bootstrap",
                    "type": "command",
                    "command": BOOT_HOOKSPEC,
                    "description": "Inject the ai-memory session bootstrap block",
                }],
            }],
        }
    }


def _grok() -> tuple[str, dict]:
    # Best-effort: the common nested Claude-style schema. The Grok CLI ecosystem
    # is fragmented (xAI Grok Build `.grok/hooks.json` + `~/.grok/config.toml`,
    # `grok-dev` `~/.grok/user-settings.json`, superagent `.grok/settings.json`).
    # We write the project-scoped nested form; verify with `grok inspect`.
    def _cmd(c: str) -> dict:
        return {"hooks": [{"type": "command", "command": c}]}

    return ".grok/settings.json", {
        "hooks": {
            "SessionStart": [{"matcher": "startup|resume", **_cmd(BOOT_HOOKSPEC)}],
            "Stop": [_cmd(GATE_DECISION)],
        }
    }


ADAPTERS = (_cursor, _claude, _codex, _gemini, _grok)


# ---- slash commands ---------------------------------------------------------
# /resume — the canonical session-resume prompt as a one-word command. The
# prompt string is the SAME thin pointer documented in STATUS.md ("How to talk
# to the next agent"); this just saves pasting it into every fresh chat. The
# content is versioned HERE (single source of truth, tenet 10) and installed to
# each harness's command folder at the workspace root, like the hook adapters.

RESUME_PROMPT = (
    "Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + "
    "Next action) and AGENTS.md, run repo-health, then do the Next action. "
    "Concierge mode: one step at a time, plain English."
)

RESUME_COMMAND_MD = (
    "---\n"
    "description: Resume ai-memory-infra from STATUS.md (concierge mode)\n"
    "---\n\n"
    f"{RESUME_PROMPT}\n"
)

# Cursor and Claude Code both read project commands from <root>/<dir>/commands.
COMMAND_FILES = (
    ".cursor/commands/resume.md",
    ".claude/commands/resume.md",
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {path}")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  wrote {path}")


def main() -> int:
    print(f"workspace root : {WORKSPACE_ROOT}")
    print(f"control plane  : {INFRA_ROOT}")
    print("installing IDE startup/handoff adapters (thin pointers to")
    print(f"  {_BOOTSTRAP} / {_COMPLETION_GATE}):")

    for build in ADAPTERS:
        rel, payload = build()
        _write(WORKSPACE_ROOT / rel, payload)

    print("installing slash commands (/resume):")
    for rel in COMMAND_FILES:
        _write_text(WORKSPACE_ROOT / rel, RESUME_COMMAND_MD)

    print("")
    print("Done. Verify in each IDE that's installed:")
    print("  Cursor  : Settings -> Hooks (reloads hooks.json on save / restart)")
    print("  Claude  : .claude/settings.json SessionStart/Stop")
    print("  Codex   : `/hooks` to review + trust (project hooks need trust)")
    print("  Gemini  : `/hooks` panel (SessionStart only; no blocking stop)")
    print("  Grok    : `grok inspect` / `/hooks` (schema varies by CLI - see header)")
    print("VS Code   : no native session hook - add the bootstrap as a folder-open")
    print("            task. See ai-memory-infra/docs/setup.md (IDE startup hooks).")
    print("Re-run after any re-clone (the parent workspace is not versioned).")
    print("")
    print("!! VERIFY IT ACTUALLY FIRES - 'configured' is NOT 'firing'.")
    print("   A hook listed as configured only means the file parsed; it is INERT")
    print("   until an execution is recorded. Fire one real turn, then confirm")
    print("   Cursor Settings -> Hooks shows a `stop` EXECUTION entry (not just a")
    print("   configured one). Zero executions = the gate is not protecting you.")
    print("   (COE 2026-06-09-ide-coupled-completion-gate.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
