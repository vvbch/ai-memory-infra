# ADR 030: Portable IDE startup/handoff hooks + session bootstrap

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** the operator (operator), Cursor agent
**Related:** Tenets 1, 2, 3, 16; ADR 015 (git-hook installer model); ADR 018
(editor pointer files carry zero canonical content); ADR 027 (deterministic
completion gate — this ADR corrects its *placement*); COE
`2026-06-09-ide-coupled-completion-gate.md`.

## Context

Two problems, one root cause.

1. **Token burn on every session start (tenet 16).** A fresh agent opens the
   parent `ai-memory` workspace and re-derives, every time, that the control plane
   is `ai-memory-infra`, then re-reads the large `AGENTS.md` + the ~1k-line
   `STATUS.md` just to learn the current phase and the single Next action. That
   discovery hop is paid in tokens on every session (context-window amplification).
   The operator asked for an **IDE startup hook** that injects the setup context
   instead.

2. **The completion-gate hook was Cursor-coupled and (worse) not even loading.**
   ADR 027 shipped the gate as `ai-memory-infra/.cursor/hooks/completion_gate.py`
   + `ai-memory-infra/.cursor/hooks.json`. But Cursor loads *project* hooks from
   the **workspace root** (`<root>/.cursor/hooks.json`), and this workspace's open
   root is the **parent `ai-memory`**, not the `ai-memory-infra` repo. So the hook
   sat in a directory Cursor never reads — the "hard layer" was almost certainly
   inert. It also coupled the guarantee to one editor, violating **tenet 2**
   (editor-agnostic; no tool lock-in), which ADR 027 self-documented merely as a
   "limitation."

The shared root cause: a *harness* startup/turn-end event is inherently
per-harness (there is no single cross-IDE event), so "put it in a hook" was
conflated with "put it in a Cursor file." The portable answer is the same one the
repo already uses for `.cursor/rules` (ADR 018) and git hooks (ADR 015):
**canonical logic is editor-agnostic and versioned; the editor-specific file is a
thin, generated adapter.**

Verified before building (tenet 8): Cursor's `sessionStart` hook supports
`additional_context` + `env`, but `additional_context` injection has a
Cursor-confirmed timing bug that can silently drop it; `env` is reliable. Cursor
also reads Claude Code `.claude/settings.json` hooks and maps `SessionStart`/`Stop`
onto its own events ([Cursor Hooks docs](https://cursor.com/docs/hooks),
[Third-party hooks](https://cursor.com/docs/reference/third-party-hooks),
[sessionStart additional_context bug](https://forum.cursor.com/t/sessionstart-hook-additional-context-is-never-injected-into-agents-initial-system-context/158452)).

## Decision

Adopt a **portable script + thin per-IDE adapter** pattern for all lifecycle
hooks, and apply it to two hooks:

- **Canonical, editor-agnostic logic in `scripts/` (versioned, tenet 1/2/3):**
  - `scripts/session_bootstrap.py` — reads `STATUS.md`, emits a compact bootstrap
    block (control plane, current phase, Next action). Modes: `--text` (humans /
    VS Code), `--cursor` (sessionStart JSON: `additional_context` + `env`), `--json`.
    Forces UTF-8 stdout so a Windows console can't crash a session. Fails open.
  - `scripts/completion_gate.py` — the ADR 027 gate, **moved out of `.cursor/`**.
- **Thin per-IDE adapters generated at the workspace root:**
  - `scripts/install_ide_hooks.py` (cross-platform Python) writes, from one
    declarative definition (no drift, tenet 10), one adapter per harness:
    `<root>/.cursor/hooks.json`, `.claude/settings.json`, `.codex/hooks.json`,
    `.gemini/settings.json`, and `.grok/settings.json`. The parent workspace is not
    a git repo, so — exactly like `.git/hooks` (ADR 015) — these generated files
    are **not** versioned; the installer + the versioned scripts are what survive a
    re-clone. **Re-run after any re-clone.**
  - **VS Code** has no native agent session hook; document wiring the bootstrap as
    a folder-open task (`docs/setup.md`). Same canonical script.

### Per-harness contracts are not identical — one script mode per contract
The session-start and turn-end *output* shapes differ by harness (verified,
tenet 8), so the canonical scripts expose one mode per contract and the adapters
select the right flag (the logic stays single-sourced):
- **sessionStart context:** Cursor wants `{additional_context, env}`
  (`--cursor`); the Claude-derived family — Claude Code, Codex, Gemini, Grok —
  uses `hookSpecificOutput.additionalContext` (`--hookspecific`; Claude Code also
  accepts plain stdout, which is what its adapter uses).
- **turn-end gate:** Cursor/Claude use `followup_message` (default mode, capped by
  `loop_limit`); Codex/Grok `Stop` uses `{"decision":"block","reason":…}`
  (`--decision`). Codex has no follow-up cap, so the gate reads `stop_hook_active`
  and allows the stop after a single nudge to avoid an infinite loop.
- **Gemini has no blocking per-turn stop** (`SessionEnd` is advisory-only), so the
  gate is deliberately *not* wired for Gemini; the bootstrap still is.
- **Grok is best-effort:** its CLI ecosystem spans several incompatible config
  schemas; the installer writes the common nested Claude-style `.grok/settings.json`
  and `docs/setup.md` tells the operator to confirm with `grok inspect`.

### Why not rely on `additional_context` alone
The Cursor injection bug means the bootstrap can't *depend* on context injection.
So `session_bootstrap.py` also exports `env` (stable) and prints the block to the
Hooks output channel; the operator verifies injection in Settings → Hooks. The
structural token win (a small Next-action excerpt instead of the whole STATUS.md)
holds regardless.

## Consequences

- **Editor-agnostic (tenet 2 restored).** No load-bearing logic in any `.cursor/`
  dir. Swapping Cursor → VS Code/Claude Code is re-running the installer, not a
  rewrite. `ai-memory-infra/.cursor/hooks.json` + `.cursor/hooks/` are deleted;
  `.cursor/rules/*` (legit thin pointers, ADR 018) stay.
- **The completion gate now actually fires** from the correct workspace root —
  fixing a latent ADR 027 defect.
- **Lower session-start token cost (tenet 16).**
- **Reversible (tenet 17).** Delete the generated adapters to disable; `git
  revert` removes the scripts/installer. Two-way door.

### Limitations / operating notes
- Generated adapters live at the unversioned parent root → re-run the installer
  per machine / re-clone (tracked the same way as ADR 015's git hooks).
- `additional_context` injection is best-effort under Cursor's current bug; `env`
  + output-channel print are the stable fallbacks.
- Requires `python` on PATH (Mac may expose `python3`; adjust the adapter command
  if the surface changes).
- Codex project (`.codex/`) hooks load only after the operator **trusts** them via
  `/hooks`; until then only user/system hooks run.
- Grok coverage is best-effort: the CLI ecosystem is fragmented across several
  incompatible hook schemas, so the generated `.grok/settings.json` may need to be
  re-pointed at the file/shape the installed Grok CLI actually reads.

## Alternatives considered
- **Keep hooks in `ai-memory-infra/.cursor/` (status quo).** Doesn't load at the
  parent root and couples to Cursor. Rejected (it's the bug).
- **User-global `~/.cursor/hooks.json`.** Not shared, not versioned, applies to all
  projects. Rejected.
- **Make `ai-memory` a git repo to version the adapters.** Larger structural
  change than warranted (tenet 7/13); the installer-regenerates model already
  solves survival. Parked.
- **Inject via a Cursor rule instead of a hook.** Rules are model-dependent prose
  (the exact non-determinism ADR 027 moved away from). Rejected for the gate; the
  bootstrap rule pointer stays as the soft complement.
