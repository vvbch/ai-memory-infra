# Interface & Contract Registry

> The single index of the system's **contracts** — the shapes and rules that two or
> more components agree on. A cross-cutting decision is a *contract, not a document*
> (ADR 031): when a contract is consumed by more than one repo, a clean control
> plane with a violating consumer is **not done**. This registry says, for each
> contract: where its schema lives, who produces/consumes it, the governing ADR,
> and **how strongly it's enforced**.
>
> New or changed contract ⇒ update this file (DoD trigger in `AGENTS.md`) and, if
> cross-repo, add/extend a conformance check.

## Enforcement legend

- **ENFORCED** — a deterministic gate fails the build/commit on violation
  (model-independent).
- **TESTED** — unit/integration tests cover it, but no cross-repo gate.
- **PROSE** — documented/agreed only; relies on the implementer honoring it.
- **EXTERNAL** — an upstream dependency's contract we consume; pinned + verified at
  source (tenet 8), not ours to change.

## Registry

### 1. Memory write contract — ENFORCED (cross-repo)

- **What:** one `user_id` per person (`"chandrav"`); `metadata.source` is the
  mandatory discriminator (lands in pgvector and, in future, the graph); `type` ∈
  `fact | decision | open_item`; `created_at` always, `occurred_at` when event time
  ≠ capture time; authored writes use `infer=False`.
- **Schema lives in:** `ai-memory-extension/src/types/api.ts`
  (`DEFAULT_USER_ID='chandrav'`, `LEGACY_DEFAULT_USER_ID`, `source` in metadata),
  `src/mcp_proxy/client.py`, `scripts/memory.py` (normalizing write path).
- **Producers:** Chrome extension, MCP proxy `add_memory`, `scripts/memory.py`,
  OpenClaw adapter (future, ADR 026/028 — must pass `source`/`agent_id` through).
- **Consumers:** Mem0 REST `/memories`, pgvector; future Neo4j/LifeGraph.
- **ADRs:** 028 (single user_id; source discriminator), 029 (type + lifecycle),
  003 (soft separation), 031 (contracts).
- **Enforcement:** `scripts/check_memory_contract.py` (CI + can run pre-commit) —
  checks extension constants, a single normalizing write path, no direct
  `/memories` bypass, MCP proxy default user id.

### 2. Extension ↔ API identity contract — ENFORCED (cross-repo)

- **What:** the extension tags every write `metadata.source = "extension"` and uses
  `user_id = "chandrav"`; legacy `"chrome-extension-user"` ids are auto-healed.
- **Schema lives in:** `ai-memory-extension/src/types/api.ts`.
- **ADRs:** 028. **Ties:** COE 2026-06-09-extension-memory-identity-drift.
- **Enforcement:** `scripts/check_memory_contract.py` (extension-constants check).

### 3. MCP proxy tool surface — TESTED

- **What:** local stdio MCP tools exposed to Claude Code / Cursor / VS Code:
  `search_memories(query, top_k=5, user_id?)`, `add_memory(text, user_id?)`,
  `list_memories(user_id?)`.
- **Schema lives in:** `src/mcp_proxy/server.py` (`@mcp.tool()`), backed by
  `src/mcp_proxy/client.py`.
- **ADR:** 025 (local MCP proxy).
- **Enforcement:** `tests/test_mcp_proxy/`; no cross-repo gate (proxy is the only
  consumer today).

### 4. Mem0 self-hosted REST API shape — EXTERNAL (pinned)

- **What:** the OSS Mem0 server endpoints we depend on: `POST /memories`
  (`text`/`messages`, `user_id`, `metadata`), `POST /search` (`query`, `user_id`,
  server-side metadata filters), `GET|PUT|DELETE /memories/{id}` (PUT requires
  `text`). Top-level `source` is dropped — it must live in `metadata` (see §1).
- **Schema lives in:** upstream `mem0ai/mem0` `server/`, pinned via `MEM0_REF` in
  `scripts/bootstrap.sh` / `infra/mem0-server.Dockerfile`.
- **ADRs:** 001 (Mem0), 013 (single provider), 021 (gpt-5 patch).
- **Enforcement:** EXTERNAL — verify at source on version bumps (tenet 8); our
  `client.py` adapts to it. The GPT-5 reasoning patch asserts loudly if upstream
  restructures (`mem0-server.Dockerfile`).

### 5. API auth & admin-UI auth — PROSE / partially deployed

- **What:** Mem0 API uses JWT (`JWT_SECRET`) + a privileged `ADMIN_API_KEY`;
  `AUTH_DISABLED=false` in prod. Caddy basic auth (`BASIC_AUTH_*`) fronts `dash.`,
  `graph.`, `monitor.`. CORS allowlist on `memory.`.
- **Schema lives in:** `infra/docker-compose.yml` (mem0 env), `infra/Caddyfile`,
  `infra/.env(.example)`; secrets indexed in the private `docs/security/secrets-catalog.md`.
- **ADRs:** 009 (security guardrails), 020 (admin key, not `make bootstrap`).
- **Enforcement:** deployed config; the broader guardrail set (PII filter, rate
  limiting) is **partly aspirational** — see `AGENTS.md` security note + BACKLOG.

### 6. Backup artifact contract — TESTED / drilled

- **What:** nightly `pg_dump` + `neo4j dump` pushed to the DO Spaces bucket;
  server-side versioning + lifecycle (30 d / 14 d); least-privilege backup key;
  pre-restore safety snapshot; restore expects matching artifact names.
- **Schema lives in:** `scripts/backup.sh`, `scripts/restore.sh`,
  `scripts/restore-drill.sh`, `infra/systemd/` timers.
- **ADRs:** 022 (backup/restore design), 023 (automation + data-loss hardening).
- **Enforcement:** monthly restore drill (1st, watched by healthchecks.io); the
  drill canary `user_id=drill-canary` is planted.

### 7. Caddy route / subdomain contract — live

- **What:** `memory.` → Mem0 API (JWT + CORS); `dash.` → Mem0 dashboard (basic
  auth); `graph.` → Neo4j Browser (basic auth); `monitor.` → Grafana (basic auth,
  Phase 8 — DNS reserved, route lights up later). Only Caddy faces the internet.
- **Schema lives in:** `infra/Caddyfile`, Terraform `subdomains` (`variables.tf`).
- **ADRs:** 009 (network isolation), 016 (DNS/registrar).
- **Enforcement:** live deployment; `monitor.` is reserved, not yet serving.

### 8. Harness hook / gate I/O contract — ENFORCED (model-independent)

- **What:** the editor-agnostic control-plane hooks. `session_bootstrap.py`
  (`--cursor` / `--hookspecific` / `--json`) injects the resume block at session
  start; `completion_gate.py` emits the turn-end block/follow-up JSON; the
  pre-commit hook runs repo-health + gitleaks + STATUS-shape gates.
- **Schema lives in:** `scripts/session_bootstrap.py`, `scripts/completion_gate.py`,
  `scripts/hooks/pre-commit`, generated per-IDE adapters under `<root>/.cursor`,
  `.claude`, `.codex`, etc. (from `scripts/install_ide_hooks.py`).
- **ADRs:** 027 (completion gate), 030 (portable startup hooks).
- **Enforcement:** ENFORCED by the harness/git — does not depend on the model.
  **This is the layer Workstream C (structured operating contract, ADR 033) extends
  to cover more of the operating contract.**

## Coverage at a glance

| Contract | Enforcement | Cross-repo? |
|---|---|---|
| 1. Memory write | ENFORCED | yes |
| 2. Extension identity | ENFORCED | yes |
| 3. MCP tool surface | TESTED | no |
| 4. Mem0 REST shape | EXTERNAL | n/a (upstream) |
| 5. API / admin auth | PROSE (partial) | no |
| 6. Backup artifact | TESTED / drilled | no |
| 7. Caddy routes | live | no |
| 8. Harness hooks/gates | ENFORCED | yes (all repos) |

> The gap this registry makes visible: contracts 1, 2, and 8 are deterministically
> enforced; 5 (auth/guardrails) is the weakest and is tracked against the
> security-maturity reword + BACKLOG. New contracts should aim for ENFORCED or at
> least TESTED, not PROSE.
