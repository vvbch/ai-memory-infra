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
  mandatory discriminator (pgvector live — probed 2026-06-11; graph when LifeGraph
  writes Neo4j); `type` ∈
  `fact | decision | open_item`; `created_at` always (capture time); **`event_date`**
  when event time ≠ capture time (dual-write `occurred_at` for ADR 029 compat);
  optional `source_doc_id`, `namespace` (`public` \| `sensitive`, default `public`),
  `external_id` on bulk/probe paths; entity names qualified inline in fact text;
  authored writes use `infer=False`.
- **Schema lives in:** `ai-memory-extension/src/types/api.ts`
  (`DEFAULT_USER_ID='chandrav'`, `LEGACY_DEFAULT_USER_ID`, `source` + `namespace`
  in metadata), `src/memory/contract.py`, `src/mcp_proxy/client.py`,
  `scripts/memory.py` (normalizing write path).
- **Producers:** Chrome extension, MCP proxy `add_memory`, `scripts/memory.py`,
  OpenClaw adapter (future, ADR 026/028 — must pass `source`/`agent_id` through).
- **Consumers:** Mem0 REST `/memories`, pgvector; future Neo4j/LifeGraph.
- **ADRs:** 028 (single user_id; source discriminator), 029 (type + lifecycle),
  037 §6 (fact metadata), 003 (soft separation), 031 (contracts).
- **Enforcement:** `scripts/check_memory_contract.py` (CI + can run pre-commit) —
  checks extension constants, a single normalizing write path, no direct
  `/memories` bypass, MCP proxy `DEFAULT_USER_ID`, and MCP `add_memory`
  `metadata.source="mcp"` tagging. Live pgvector probe:
  `scripts/verify_source_propagation.py` (ADR 028; Neo4j count expect 0 until
  LifeGraph).

### 2. Extension ↔ API identity contract — ENFORCED (cross-repo)

- **What:** the extension tags every write `metadata.source = "extension"` and uses
  `user_id = "chandrav"`; legacy `"chrome-extension-user"` ids are auto-healed.
- **Schema lives in:** `ai-memory-extension/src/types/api.ts`.
- **ADRs:** 028. **Ties:** COE 2026-06-09-extension-memory-identity-drift.
- **Enforcement:** `scripts/check_memory_contract.py` (extension-constants check).

### 3. MCP proxy tool surface — TESTED

- **What:** local stdio + remote OAuth HTTP MCP tools (ADR 034/035):
  `search_memories(query, top_k=5, user_id?)`, `add_memory(text, user_id?)`,
  `list_memories(user_id?)`, `delete_memory(memory_id)`,
  `update_memory(memory_id, text, metadata_json?)`.
- **Schema lives in:** `src/mcp_proxy/server.py` (`@mcp.tool()`), backed by
  `src/mcp_proxy/client.py`.
- **ADRs:** 025 (local MCP proxy), 037 (delete/update required for incident cleanup
  and idempotent write hygiene).
- **Enforcement:** `tests/test_mcp_proxy/`; no cross-repo gate (proxy is the only
  consumer today).

### 1b. Memory read contract — TESTED

- **What:** `/search` is similarity-ranked; recency uses **`max(event_date)`**, never
  `created_at`. Structured follow-ups use metadata filters (`type=open_item`,
  `status=open`). Entity-collision queries rerank by inline-qualifier overlap.
  Default reads filter `namespace=public`.
- **Schema lives in:** `src/memory/retrieval.py`, `scripts/acceptance_probe.py`.
- **ADR:** 037 §7.
- **Enforcement:** `tests/test_memory/test_retrieval.py`,
  `tests/test_scripts/test_acceptance_probe.py`; live gate
  `scripts/acceptance_probe.py` (probed 2026-06-11 PASS).

### 3b. Bulk write idempotency — TESTED

- **What:** scripted bulk seeds carry `metadata.external_id`, `event_date`, `source`,
  optional `source_doc_id` / `namespace`; existence check before write; timeout →
  verify-then-skip (never reword-retry). Shared helper:
  `src/mcp_proxy/idempotent_write.py`. Offline near-dupe clustering is review-first
  (`memory_compaction.py`).
- **Schema lives in:** `scripts/bulk_seed_importer.py`, `src/mcp_proxy/idempotent_write.py`,
  `scripts/memory_compaction.py`.
- **ADR:** 037.
- **Enforcement:** `tests/test_scripts/test_bulk_seed_importer.py`; compaction is
  operator-scheduled (PROSE).

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
  pre-commit hook runs repo-health + gitleaks + STATUS-shape + contract-render +
  pointer-purity + secrets-catalog-coverage gates.
- **Schema lives in:** `scripts/session_bootstrap.py`, `scripts/completion_gate.py`,
  `scripts/hooks/pre-commit`, generated per-IDE adapters under `<root>/.cursor`,
  `.claude`, `.codex`, etc. (from `scripts/install_ide_hooks.py`).
- **ADRs:** 027 (completion gate), 030 (portable startup hooks).
- **Enforcement:** ENFORCED by the harness/git — does not depend on the model.
  **This is the layer Workstream C (structured operating contract, ADR 033) extends
  to cover more of the operating contract.**

### 9. Operating contract (structured single-source) — ENFORCED

- **What:** the tenets / engineering-practices / DoD-trigger sections of `AGENTS.md`
  and the full `docs/tenets.md` are **generated** from `contract/*.yaml` (one record
  per rule: verbatim prose + `enforcement.status` + `mechanism` + `gate_id`). Prose
  is a *view*; the YAML is the source. A coverage report makes the model-dependent
  (prose-only) surface visible and shrinkable.
- **Schema lives in:** `contract/tenets.yaml`, `contract/practices.yaml`,
  `contract/dod.yaml`; renderer `scripts/render_contract.py`; report
  `docs/reports/contract-coverage.md`; fenced regions marked `<!-- generated:* -->`.
- **ADR:** 033 (supersedes hand-authored canonical prose for these sections);
  ties tenet 10 (no drift), ADR 018.
- **Enforcement:** `scripts/render_contract.py --check` (pre-commit gate 4 + CI) —
  fails if the prose drifts from the YAML; drift is impossible by construction.

### 10. Editor pointer-file purity — ENFORCED

- **What:** `alwaysApply` Cursor rules + `CLAUDE.md` must stay thin pointers
  ("read `AGENTS.md`") and carry zero canonical content (no tenets/rules/DoD table).
- **Schema lives in:** `scripts/check_pointer_purity.py`; the pointers themselves
  (`.cursor/rules/00-project.mdc`, `CLAUDE.md`).
- **ADRs:** 018 (boundary + deferred guard, now built); ties COE
  2026-06-07-cursor-rule-drift, tenet 2/10, ADR 033 §4 (#3).
- **Enforcement:** `scripts/check_pointer_purity.py` (pre-commit gate 5 + CI).
  Scoped to contractually-pure pointers; glob-scoped helper rules are out of scope.

### 11. Final handoff contract — TESTED

- **What:** before any final response / Resume prompt, every project repo must be
  clean, pushed, in sync with origin (not behind — Drive-synced clone risk,
  tenet 11), and `STATUS.md` must be the checkpoint of record (no work committed
  after the last STATUS update). The verifier prints the latest pushed commit per
  repo so the final answer cites push evidence instead of asserting it.
- **Schema lives in:** `scripts/handoff_verify.py` (`--json` for machines);
  floor enforced turn-end by `scripts/completion_gate.py` (contract 8).
- **ADRs/ties:** ADR 027/030/033 §4 (#1); COEs 2026-06-08-atomic-handoff-failure,
  2026-06-09-session-handoff-omission, 2026-06-09-concierge-handoff-regression.
- **Enforcement:** TESTED (`tests/test_scripts/test_handoff_verify.py`); invoked
  by the `session-checkpoint` agent skill before final responses. The turn-end
  completion gate remains the deterministic floor (dirty/unpushed); the
  behind-check + STATUS-freshness check are agent-run.

### 12. Agent skills (discoverable trigger pointers) — ENFORCED (by installer)

- **What:** the persona skills (`memory-daily-driver`, `session-checkpoint`,
  `operator-action`, `operator-credential-handoff`) are versioned in
  `ai-memory-infra/skills/*/SKILL.md` as thin
  trigger pointers to the canonical specs (`docs/skills/*`) + scripts; the
  installer copies them to the unversioned workspace root (`.cursor/skills/`,
  `.claude/skills/`) where Cursor/Claude Code auto-discover them (verified
  cursor.com/docs/skills, 2026-06-10). Root-level placement is deliberate:
  nested `.cursor/skills/` are auto-scoped to that directory's files, but the
  Operator Assistant skills must fire on pure conversation.
- **Schema lives in:** `skills/*/SKILL.md`; installer `scripts/install_ide_hooks.py`.
- **ADRs/ties:** ADR 030 (same install model as hooks); `docs/agent-personas.md`
  (owning personas); tenet 2 (canonical content stays in the repo).
- **Enforcement:** installer-generated (re-run after re-clone); skill bodies are
  pointers, so drift surface is minimal.

### 13. Remote MCP HTTP surface (`mcp.` subdomain) — TESTED / live

- **What:** Streamable HTTP MCP at `https://mcp.chandrav.dev/` for remote
  OAuth connector clients: claude.ai (incl. iPhone), Perplexity custom
  connectors (live 2026-06-10), and ChatGPT developer-mode apps (ADR 036 —
  all three consume the same OAuth 2.1 + DCR surface; the consent page names
  the requesting client). Same three tools as §3 (shared
  `src/mcp_proxy/server.py` tool code, `metadata.source=mcp` on writes, default
  `user_id=chandrav`). **Auth is self-hosted OAuth 2.1** (ADR 035 — the only
  model claude.ai custom connectors accept): discovery at
  `/.well-known/oauth-authorization-server` + `/.well-known/oauth-protected-resource`,
  DCR at `/register`, PKCE S256 `/authorize` → operator `/consent`
  (password = `MCP_CONNECTOR_BEARER_TOKEN`) → `/token` (access 1 h, refresh
  60 d rotated; opaque, SHA-256-hashed in `/data/oauth_state.json` on the
  `mcp_oauth_state` volume). The static `MCP_CONNECTOR_BEARER_TOKEN` (dedicated
  token, **not** `ADMIN_API_KEY`) remains valid as an access token for
  verification/API-path callers. Missing/wrong token ⇒ `401` +
  `WWW-Authenticate: Bearer ... resource_metadata=...`. `/health` and the OAuth
  endpoints are the only open routes. Transport keeps DNS-rebinding protection
  scoped to the subdomain; runs stateless (no session affinity behind Caddy).
- **Schema lives in:** `src/mcp_proxy/http_server.py` (app wiring),
  `src/mcp_proxy/oauth.py` (provider + state store + consent),
  `infra/mcp-proxy.Dockerfile`, `infra/docker-compose.yml` (`mcp-proxy` service),
  `infra/Caddyfile` (`mcp.{$DOMAIN}`), Terraform `subdomains`;
  design: `docs/design/remote-mcp-oauth.md`.
- **ADR:** 034 (endpoint) + 035 (OAuth auth model, supersedes 034 §2) +
  036 (ChatGPT/Perplexity clients).
- **Enforcement:** `tests/test_mcp_proxy/test_oauth.py` (full DCR→PKCE→consent→
  token→MCP flow + failure paths) and `test_http_server.py` (401/health/
  initialize); live-verified 2026-06-10. Caddy rate limiting stays in BACKLOG.

## Coverage at a glance

| Contract | Enforcement | Cross-repo? |
|---|---|---|
| 1. Memory write | ENFORCED | yes |
| 1b. Memory read | TESTED | no |
| 2. Extension identity | ENFORCED | yes |
| 3. MCP tool surface | TESTED | no |
| 4. Mem0 REST shape | EXTERNAL | n/a (upstream) |
| 5. API / admin auth | PROSE (partial) | no |
| 6. Backup artifact | TESTED / drilled | no |
| 7. Caddy routes | live | no |
| 8. Harness hooks/gates | ENFORCED | yes (all repos) |
| 9. Operating contract (structured) | ENFORCED | no |
| 10. Pointer-file purity | ENFORCED | no |
| 11. Final handoff | TESTED | yes (all repos) |
| 12. Agent skills | installer-generated | no |
| 13. Remote MCP HTTP | TESTED / live | no |

> The gap this registry makes visible: contracts 1, 2, 8, 9, and 10 are
> deterministically enforced; 5 (auth/guardrails) is the weakest and is tracked
> against the security-maturity reword + BACKLOG. New contracts should aim for
> ENFORCED or at least TESTED, not PROSE.
