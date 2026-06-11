# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-11 (acceptance probe green at scale; probe isolation fix).

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract **green** —
acceptance probe **3/3 PASS** with 249 ADR facts loaded (`chandrav` @
`memory.chandrav.dev`).

**Build track:** Phases **6–8 core code** landed. **Public/private boundary** scrubbed
(ADR 038). **Phase 5 bulk load** — **249 ADR facts live** in bank; all verified by
`external_id` search.

## Current phase

**Post–Phase 5 acceptance complete.** Memory contract validated at scale; Phase 9 polish
and ops follow-ups remain.

## Done this session (2026-06-11)

- **Acceptance probe isolation:** `search_with_contract` + probe queries scope to
  `probe:acceptance:` via `external_id_prefix` + rostered `external_ids` (exact
  `fetch_by_external_id` — `GET /memories` capped at 20). Live probe **3/3 PASS** with
  249-fact corpus; 6 probe memories cleaned up.
- **Phase 5 live load** (prior): 249 ADR facts in bank; verified via `find_by_external_id`.

## Last decisions

- Public repo carries engineering context only; operator profile + ventures are private.
- Canonical public `user_id` is `primary-user`; live deploy overrides via env (private doc).
- Git history: **option 3 accepted** — no rewrite; strangers reading HEAD only are safe.
- Probe isolation uses rostered `external_ids` + exact metadata filter (not list scan).

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest; Phase 3 premise test;
Phase 9 README/eval CI workflow/Grafana deploy.

## Open blockers / risks

- **Import cache refresh** — full `list_all_memories` after each write overloaded server
  on bulk run 1; idempotent re-run recovered; consider append-to-cache fix.
- **Phase 9 polish** — README/eval CI workflow/Grafana deploy remain.
- **`GET /memories` cap** — live API returns ~20 rows regardless of `limit`; prefix
  discovery must use exact `external_id` search filter (documented in retrieval layer).

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.
- Live env: `chandrav` @ `https://memory.chandrav.dev` (setx persisted 2026-06-11).
- Cursor shells may need env reload:
  `$env:AI_MEMORY_BASE_URL = [Environment]::GetEnvironmentVariable('AI_MEMORY_BASE_URL','User')`

## Next action

> **RESUME HERE — Phase 9 polish kickoff:**
> Pick one Phase 9 item from `BACKLOG.md` (README refresh, eval CI gate workflow, or
> Grafana deploy doc) and land a small, verifiable slice — or tackle import cache
> append-to-cache if bulk ingest is the priority.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action.
```
