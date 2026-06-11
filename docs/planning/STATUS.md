# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-11 (Phase 5 dry-run ready; env aligned).

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract locked;
acceptance probe PASS.

**Build track:** Phases **6–8 core code** landed. **Public/private boundary** scrubbed
(ADR 038). **Phase 5 bulk load** — ADR export dry-run complete (249 new facts vs 20
existing bank rows); awaiting operator approval for live write.

## Current phase

**Phase 5 live data load (operator gate).** Local env now matches private
`OPERATOR.md` (`AI_MEMORY_USER_ID=chandrav`, `AI_MEMORY_BASE_URL=https://memory.chandrav.dev`).
Migration CLI exports `data/migration-facts.json`; `bulk_seed_importer.py --dry-run`
reports **249 would_write**, **0 invalid**.

## Done this session (2026-06-11)

- **Env alignment:** persisted `AI_MEMORY_BASE_URL` + `AI_MEMORY_USER_ID` via `setx`
  (live bank probe: 20 memories under `chandrav`)
- **Migration CLI:** `--output` writes bulk_seed JSON; design doc updated
- **ADR 038:** fixed `Jordan` inline-qualifier in decision text (contract gate)
- **Dry-run:** `docs/decisions/` → 249 facts; bank dedup dropped 0; bulk importer clean

## Last decisions

- Public repo carries engineering context only; operator profile + ventures are private.
- Canonical public `user_id` is `primary-user`; live deploy overrides via env (private doc).
- Git history: **option 3 accepted** — no rewrite; strangers reading HEAD only are safe.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest; Phase 3 premise test;
Phase 9 README/eval CI workflow/Grafana deploy.

## Open blockers / risks

- **Live load approval** — 249 ADR chunks will be written to the live bank (one-way door).
- **Git history** — personal content remains in old commits; accepted (option 3).
- **Phase 9 polish** — README/eval CI workflow/Grafana deploy remain.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.
- Live env: `chandrav` @ `https://memory.chandrav.dev` (setx persisted 2026-06-11).

## Next action

> **RESUME HERE — operator approves live load:**
> Run `python scripts/bulk_seed_importer.py data/migration-facts.json` (no `--dry-run`),
> then `python scripts/acceptance_probe.py`. Re-export first if ADRs changed:
> `python -m migration import --source docs/decisions --dry-run --use-bank --output data/migration-facts.json`

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action.
```
