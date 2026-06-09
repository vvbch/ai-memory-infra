# Backlog — prioritized, deferred work

> Parked-but-valuable work, ranked. Captured so nothing is lost and nothing
> silently displaces the current goal (tenet 13). `STATUS.md` "Next action" is what
> we're doing *now*; this is what we've consciously chosen to do *later*.
>
> **Priorities:** **P1** = do at the next natural opportunity (security / soon-blocking).
> **P2** = governance/quality hardening, fold into the relevant phase. **P3** =
> valuable but non-blocking / personal.

## Active pre-build gate — do before any more build work

- ✅ **`[product-design]` Define agent/persona definitions before skills/tools — DONE
  (2026-06-09).** See `docs/agent-personas.md`. This
  is the next resume point even though it is not a numbered infra build phase.
  Before implementing more skills, define the small set of agents/personas that
  will use the memory layer, their boundaries, what each is allowed to
  store/retrieve, and success criteria. Then skills/tools can be attached under
  those agents. Reason: skills without agent definitions become a bag of commands
  with no owner or success criteria. Set by operator 2026-06-09 after Cursor MCP
  visibility was proven.

- **`[skills]` Build the first agent-owned skills.** Start with the COE-driven
  mechanics in `docs/agent-personas.md`: Build Agent session checkpoint, Build
  Agent repo handoff verifier, and Operator Assistant concierge action formatter.
  These directly address the repeated handoff/operator-action failures before
  adding broader research or memory-hygiene skills.
  - ✅ **DONE (2026-06-09):** Build Agent repo handoff verifier =
    `scripts/completion_gate.py` (ADR 027/030).
  - ✅ **DONE (2026-06-09):** Build Agent session checkpoint =
    `scripts/session_checkpoint.py` (spec
    `docs/skills/build-agent-session-checkpoint.md`).
  - ✅ **DONE (2026-06-09):** Operator Assistant concierge action formatter =
    `scripts/operator_action.py` (spec
    `docs/skills/operator-assistant-concierge-action.md`).
  - ✅ **DONE (2026-06-10):** decision capture absorbed into the Memory Daily
    Driver conversational practice (spec
    `docs/skills/operator-assistant-memory-daily-driver.md`); Memory Steward
    hygiene checks remain deferred behind real utility.

## P1 — discovered drift / verification

- **`[docs-drift]` Architecture docs claim a "Mem0 auto-managed graph" in Neo4j —
  source says the deployed stack has none (found 2026-06-10, tenet 8/10).**
  Verified from upstream source at our pinned ref (`MEM0_REF=3669459…`) and the
  mem0ai 2.0.4 PyPI wheel: the `server/` REST app never reads `NEO4J_*` and never
  configures a `graph_store`, and the 2.0.4 library ships **zero** graph-memory
  code (no `graph` extra exists — `pip install "mem0ai[graph]"` in
  `infra/mem0-server.Dockerfile` installs plain mem0ai with a warning). So the
  compose `NEO4J_URI/USERNAME/PASSWORD` env vars into the mem0 container are dead
  config, and Neo4j currently serves only the **future LifeGraph** (Phase 6) —
  it is running, backed up, but not written to by Mem0. Actions: (1) confirm on
  the droplet that the live Neo4j has no Mem0-written nodes; (2) fix the drift in
  `docs/architecture.md` + `AGENTS.md` ("dual namespace" claim) + the Dockerfile
  comment; (3) decide in an ADR whether graph memory comes from LifeGraph only
  (current plan) or a Mem0 version/extra that actually ships it. Until then,
  decision-supersession history lives in the Mem0 SQLite history table + the
  Daily Driver supersession convention, not in Neo4j.

## P1 — do at the start of Phase-1 CI work

- **`[governance]` Final all-repo handoff verifier — PROMOTED from P2 after
  repeat handoff COEs (2026-06-09).** Before final response, enumerate every
  touched workspace repo and fail/report if any repo is dirty, ahead, behind, or
  not pushed to `origin/main`; also check that `STATUS.md`/logs are checkpointed
  before a resume prompt is emitted. Cheapest version: a documented final
  checklist in `STATUS.md`; better version: a script that checks
  `ai-memory-infra`, `ai-memory-infra-private`, `ai-memory-extension`, and any
  future package repos, then prints the latest pushed commit per touched repo.
  Ties: `docs/coe/2026-06-08-atomic-handoff-failure.md`,
  `docs/coe/2026-06-09-session-handoff-omission.md`,
  `docs/coe/2026-06-09-concierge-handoff-regression.md`.
- **`[security]` Strip the plaintext secrets block from `infra/.env` (post-burn-in
  cleanup).** The generated dash/graph admin password (and copy-to-Bitwarden reminder)
  live as a comment block at the top of `infra/.env` — both locally and, after deploy, on
  the droplet (`/opt/ai-memory-infra/infra/.env`). The values are already safe in
  Bitwarden, so delete the block from both copies; nothing plaintext should sit at rest.
  **Deferred to the post-burn-in cleanup pass (tenet 18):** the operator is keeping the
  admin-UI login note handy through ~1 week of full real-world usage, then this gets swept.
  Trigger: **after ~1 week of full usage (~2026-06-15)**. Safe to hold because `.env` is
  gitignored *and* the new gitleaks pre-commit gate stops it ever reaching git (the active
  risk — secrets in history — is already closed). Consciously deferred 2026-06-07,
  re-deferred with a trigger 2026-06-08. Ties: AGENTS.md secrets rule, ADR 017, tenets
  14 & 18.
- ✅ **`[security]` Secret-scan pre-commit (gitleaks) — DONE (2026-06-08).** "No secrets
  in git" is now a *deterministic gate*. Added **gitleaks v8.30.1** as a second pre-commit
  gate in `scripts/hooks/pre-commit` (after the Tenet-11 repo-health gate): it runs
  `gitleaks git --staged` against a versioned `.gitleaks.toml` (extends the upstream default
  ruleset; narrow allowlist for `.env.example` placeholders) and **blocks the commit** on any
  finding — or if gitleaks is missing (a silent no-op would defeat the gate).
  `scripts/install-hooks.ps1` now also **ensures gitleaks is installed** (auto-installs via
  winget when missing) so the gate is reliably present after a re-clone. Verified both ways:
  a staged fake AWS key was blocked (exit 1); the real changeset passed ("no leaks found").
  Ties: AGENTS.md secrets rule, tenet 14 (Detect layer), tenet 1 (versioned config).

- ✅ **`[deploy]` Make the deploy reproducible end-to-end — DONE (2026-06-08).** Rebuilt
  `mem0-api-server:local` on the droplet from `infra/mem0-server.Dockerfile` (ADR 021 baked
  in), proved it survives `compose up --force-recreate` (round-trip persisted, user_id
  `diag-rebuild-20260608`), and folded the clone-pinned-src (`MEM0_REF`) + `docker build` into
  `scripts/bootstrap.sh`. `compose pull` now names only the external images so the local-only
  Mem0 image + profiled-off dashboard don't break it. `setup.md` Step 6 updated. Chose
  build-on-droplet over GHCR (tenet 7); revisit GHCR only if we go multi-node.

- ✅ **`[deploy]` Document the OpenAI project model-access requirement in `setup.md` — DONE
  (2026-06-08).** `setup.md` Prereq 6 + Step 7 now call out that the OpenAI project must allow
  **both** `gpt-5-mini` and `text-embedding-3-small` (or "Allow all models"), and that a `200`
  with 0 memories is the silent symptom of this. Tie: ADR 013/011, tenet 10.

> **Resolved / moved out of backlog:** "Stand up admin/API-key + confirm model
> config" is **no longer deferred** — the admin key is done (built-in
> `ADMIN_API_KEY`, **not** `make bootstrap`; see **ADR 020**, locked) and the
> model-config + `POST /memories` round-trip are the active `STATUS.md` "Next
> action" (steps 3–4). Do not re-add `make bootstrap` here — it would stand up a
> conflicting second DB stack (ADR 020).

## P2 — memory model implementation (ADR 028 / 029)

- **`[memory]` Enforce `source` into Mem0 *and* Neo4j graph metadata (ADR 028).** Writes must carry a
  mandatory `source` (and `agent_id` where present) that lands in *both* pgvector and the graph, so
  origin is queryable in either store and prototype/disposable writes stay filterable, editable, and
  removable by `source`. Includes: confirm the Mem0 write path propagates `metadata.source` to Neo4j
  nodes/edges (patch if not); add the OpenClaw adapter check (`serenichron/openclaw-memory-mem0`) —
  patch the adapter if it drops the fields, never fork `user_id`. Verify with a `source="openclaw"`
  probe visible via `/search` metadata **and** on the Neo4j node. Tie: ADR 028 (supersedes 026),
  ADR 003.
- **`[memory]` Temporal tagging — `type` + timestamps on every write (ADR 029).** Tag each memory
  `type` (`fact` | `decision` | `open_item`); carry `created_at` (Mem0) + optional `occurred_at`
  when event time ≠ capture time. Model `decision` as `:Decision` LifeGraph nodes (ADR 005) with
  supersession edges. Tie: ADR 029, ADR 005.
- **`[memory]` Open-item lifecycle + revisit loop (ADR 029).** Add the `:OpenItem` node type with
  `status` (`open`/`in_progress`/`done`/`dropped`), optional `due_at`/`revisit_at`, and on closure
  `resolution` + `closed_at`. Build the **revisit pass** (Operator Assistant / Memory Steward,
  `docs/agent-personas.md`) that surfaces open items whose `revisit_at`/`due_at` has passed (or that
  are stale) and records progress / closes with a resolution / re-schedules — so "check back what
  happened" is a mechanism, not memory. Tie: ADR 029, tenet 14.
- **`[product]` Todo app as a thin projection over open items (ADR 029).** A REST/MCP client that
  renders, filters, and updates `open_item` memories + `:OpenItem` LifeGraph nodes — **no new
  datastore** (tenets 4/7). Depends on the three items above. Tie: ADR 029, ADR 028.

## P2 — governance & quality hardening (fold into CI / eval phases)

- **`[backup]` ⬆ PROMOTED into active Phase 2 (2026-06-08) — no longer parked.** Automating
  backups + adding a restore drill was re-scoped *into* Phase 2 (it isn't done until backups
  are scheduled, self-monitoring, and drilled). Design is locked in **ADR 023**; it is the
  current `STATUS.md` "Next action" for the next session. Scope: daily **systemd timer**
  (`Persistent=true`), **dead-man's-switch** failure alerting (vendor = an open operator
  decision, tenet 12), **data-loss hardening** (server-side lifecycle/versioning instead of a
  client-side delete-prune; a least-privilege backup key; a pre-restore safety snapshot), and a
  recurring **restore drill**. Tie: tenets 4 (graceful degradation), 17 (effect-vs-code),
  ADR 022 + ADR 023. **Progress (2026-06-08):** ✅ §1 daily timer + ✅ §2 dead-man's-switch
  (healthchecks.io, green) + ✅ §3 data-loss hardening — (a) server-side versioning + 30 d/14 d
  lifecycle, (b) least-privilege bucket-scoped backup key (verified), (c) pre-restore snapshot.
  ⬜ **Only §4 restore drill remains** before Phase 2 is done.
- **`[deploy]` Build & re-enable the Mem0 dashboard.** No published `mem0/mem0-dashboard`
  image exists; it's gated behind the compose `dashboard` profile and deferred. Build it
  from the mem0 repo's `server/dashboard` context (Next.js, needs a node build), then
  `docker compose --profile dashboard up -d` and confirm `dash.chandrav.dev` works
  (the Caddy route + DNS already exist). The `/setup` wizard lives here too.
- **`[extension]` Fix the ChatGPT inline composer modal placement.** The OpenMemory icon is visible
  inside the ChatGPT composer and the modal appears to be created, but in the current ChatGPT layout
  it opens off-screen/mostly invisible. A local viewport-clamp attempt in
  `src/chatgpt/content.ts` built green but did not fix the visible behavior after extension reload,
  so the ineffective code change was not retained.
  Nonblocking: automatic ChatGPT save, live `/search`, and sidebar Recent Memories are proven, and
  seamless memory should not depend on a manual modal click. Fold this into a later extension polish
  pass if inline manual injection becomes useful.
- **`[cosmetic]` Silence the bcrypt Compose warning.** `BASIC_AUTH_HASH` (bcrypt, full of
  `$`) makes Compose log `"…" variable is not set`. Harmless (Caddy gets the right hash via
  `env_file`); escape `$`→`$$` in `infra/.env` to quiet it. Also: apex `chandrav.dev` TLS
  didn't verify from a Windows client — confirm Caddy issued the apex cert.

- **Policy-as-code for pointer files (ADR 018 enforcement).** Either *generate*
  `.cursor/rules/*` + `CLAUDE.md` from `AGENTS.md` (propagation by definition →
  drift impossible by construction), and/or a **pointer-lint** that fails if a
  pointer file carries tenet/rule content. Closes the COE detection gap
  (`docs/coe/2026-06-07-cursor-rule-drift.md`).
- **Behavioural tenets as eval/CI checks** where feasible — codify rules that have
  teeth as tests that block on regression (tenet 14).
- **`[finops]` Context-budget / session-cost signal (tenet 16 Detect layer).** Detection
  for the credit-exhaustion COE (`docs/coe/2026-06-08-cursor-credit-exhaustion.md`): a
  proactive "this session is getting expensive → checkpoint & restart" cue, rather than
  finding out via a depleted Cursor balance. Cheapest version: operator watches the usage
  meter + a periodic context-size check-in; richer version: an automated context-budget
  alert. Closes the COE's human-catch detection gap.
- ✅ **`[governance]` Final all-repo handoff verifier — PROMOTED to P1
  (2026-06-09).** Repeat human-caught handoff failures made this soon-blocking; see P1.

## P3 — valuable, non-blocking / personal

- **Bitwarden full family rollout.** Families plan already paid (2026-06-07).
  Remaining: invite the (up to 6) members, migrate passwords off Gmail/WhatsApp
  into shared collections, set per-member access (ADR 017 / `financial-decisions.md`).
- **KeePassXC offline vault backup** (`.kdbx` in a safe / will) as a
  vendor-independent fallback (ADR 017 "secondary backup").
