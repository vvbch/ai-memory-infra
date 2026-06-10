# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (Cursor user-rule handoff COEs + print-first script).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **ADR 036 is complete** on every targeted
surface. **ADR 037 closed.** Build track next: ADR 028 `source` metadata.

**Curated bank (`user_id=chandrav`):** ~21 facts; extension auto-capture off by
policy; MCP primary write surface.

## Current phase

**Infra phases 0–4 live; ADR 036 + ADR 037 closed.** Phases 5–8 stubs — **active
build track**.

## Done this session (2026-06-10)

- **Global vs workspace rule conflict** — `AGENTS.md` park + conflict protocol;
  `docs/coe/2026-06-10-global-workspace-rule-conflict.md`; `cursor_user_rules.py`.
- **Three follow-up COEs** (operator caught agent mistakes):
  - `2026-06-10-hallucinated-cursor-rule-name.md` — `committing-changes-with-git`
    is a prompt tag, not a Settings label.
  - `2026-06-10-clipboard-over-print-delegation.md` — print in chat, not clipboard.
  - `2026-06-10-cursor-user-rules-not-on-disk.md` — User rules are cloud-synced;
    not found on local filesystem; `cursor_dialog` MCP not exposed.
- **`cursor_user_rules.py`** — fixed parser; **show** (print) is default handoff.

## Last decisions

- Workspace `AGENTS.md` + hooks = enforceable layer; Cursor User rules = best-effort
  cloud alignment only.
- Never cite internal prompt tags as Settings UI paths.
- Long text handoffs: print in chat; clipboard only on operator request.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Top: ADR 028 `source` tagging; MCP droplet
redeploy for ADR 037 tools.

## Open blockers / risks

- **Cursor User rule alignment (operator):** Settings → Rules → **User rules** —
  if empty, **Add rule** and paste text from
  `python scripts/cursor_user_rules.py show commit` (printed in next chat). If
  section is empty, commit restriction may be Cursor server default, not a local
  file — workspace rules still win here via `AGENTS.md`.
- **MCP droplet behind git** — ADR 037 delete/update tools until redeploy.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` param for paths with
  spaces/parens.

## Next action

> **RESUME HERE — finish Cursor User rule handoff, then ADR 028:**
> 1. New chat: run `python scripts/cursor_user_rules.py show commit`; operator
>    adds/edits **Settings → Rules → User rules** (not a named `committing-changes-*`
>    entry — that tag is internal only).
> 2. Then ADR 028: audit `metadata.source` on extension + MCP proxy + OpenClaw
>    adapter; patch + tests.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
