# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (MCP droplet redeploy ✅; ADR 037 tools live).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **Remote MCP** at `https://mcp.chandrav.dev`
now ships **five tools** incl. `delete_memory` / `update_memory` (ADR 037).
Production add → update → delete verified on droplet.

**Curated bank (`user_id=chandrav`):** extension auto-capture off by policy; MCP
primary write surface.

**Active build track:** Phase 5 migration pipeline (phases 5–8 stubs).

## Current phase

**Infra phases 0–4 live.** Phase 5 migration — **start design + TDD**.

## Done this session (2026-06-11)

- **MCP droplet redeploy** — `git pull` to `7ea9d6e`, rebuilt `mcp-proxy` image,
  container recreated; `https://mcp.chandrav.dev/health` OK.
- **ADR 037 production verify** — throwaway add → update → delete round-trip on
  droplet Mem0 API (`scripts/deploy_probe_roundtrip.sh`).
- **Market world model** — architecture debate prompt written; **parked** (see
  BACKLOG); resume after operator runs frontier-model review.

## Last decisions

- MCP redeploy closes the ADR 037 production gap; no connector re-consent needed
  (`mcp_oauth_state` volume preserved).
- Market-analysis world-build stays **out of scope** until explicitly unparked —
  parallel private repo, not a blocker for Phase 5.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Top active: **Phase 5 migration TDD**.
Parked: market world model debate; OpenClaw adapter gate.

## Open blockers / risks

- **OpenClaw adapter** — not in workspace; conformance audit blocked on checkout.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` param for paths with
  spaces/parens.

## Next action

> **RESUME HERE — Phase 5 migration (TDD start):**
> Write `docs/design/migration-pipeline.md` (short), then add the first failing
> test `tests/test_migration/test_import_md.py` for `.md` heading-split parsing;
> implement `src/migration/import_md.py` to pass. Follow setup-prompt Phase 5
> order: tests first, then code.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
