# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-11 (public repo sanitization + Phases 6–8).
Repo-health pending final verify; committing+pushing both repos.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract locked;
acceptance probe PASS.

**Build track:** Phases **6–8 core code** landed. **Public/private boundary** scrubbed
(ADR 038): personal/venture content moved to `ai-memory-infra-private`. **Phase 5 live
data load** scheduled (operator). Phase 9 polish and production wiring remain.

## Current phase

**Post-sanitization handoff.** Public repo is stranger-safe at HEAD. Git history still
contains personal data — **operator chose option 3 (accept history, rely on HEAD).**
No filter-repo or repo recreate unless that decision is reversed explicitly.

## Done this session (2026-06-11)

- **ADR 038:** public/private content boundary; synthetic LifeGraph/eval fixtures
- **Private:** `OPERATOR.md`, `ventures.md`, `setup-prompt.md`, interview automation prompt
- **Public:** `AGENTS.md` rewrite; `primary-user` / `example.com` defaults; docs/skills scrub
- **Extension:** aligned `DEFAULT_USER_ID` and default server URL with public contract

## Last decisions

- Public repo carries engineering context only; operator profile + ventures are private.
- Canonical public `user_id` is `primary-user`; live deploy overrides via env (private doc).
- Git history: **option 3 accepted** — no rewrite; strangers reading HEAD only are safe.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest; Phase 3 premise test;
Phase 9 README/eval CI workflow/Grafana deploy.

## Open blockers / risks

- **Git history** — personal content remains in old commits; accepted (option 3). Cloners who dig history may see it.
- **Live deploy env** — operator must set `AI_MEMORY_USER_ID` / URLs to match existing bank.
- **Phase 5 data load** — export JSON + `bulk_seed_importer` with approval.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.

## Next action

> **RESUME HERE — operator env alignment + Phase 5 load:**
> Confirm private `OPERATOR.md` env overrides match the live bank (`user_id`, base URL).
> Then migration CLI `--output facts.json`, dry-run with `--use-bank`, operator approves,
> `bulk_seed_importer.py` live load.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action.
```
