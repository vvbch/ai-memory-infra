# Backlog — prioritized, deferred work

> Parked-but-valuable work, ranked. Captured so nothing is lost and nothing
> silently displaces the current goal (tenet 13). `STATUS.md` "Next action" is what
> we're doing *now*; this is what we've consciously chosen to do *later*.
>
> **Priorities:** **P1** = do at the next natural opportunity (security / soon-blocking).
> **P2** = governance/quality hardening, fold into the relevant phase. **P3** =
> valuable but non-blocking / personal.

## P1 — do at the start of Phase-1 CI work

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
- **`[governance]` Final all-repo handoff verifier.** Detection for the atomic-handoff
  COE (`docs/coe/2026-06-08-atomic-handoff-failure.md`): before final response, enumerate
  every touched workspace repo and fail/report if any repo is dirty, ahead, behind, or not
  pushed to `origin/main`. Cheapest version: a documented final checklist in `STATUS.md`;
  better version: a script that checks `ai-memory-infra`, `ai-memory-infra-private`,
  `ai-memory-extension`, and any future package repos, then prints the latest pushed commit
  per touched repo.

## P3 — valuable, non-blocking / personal

- **Bitwarden full family rollout.** Families plan already paid (2026-06-07).
  Remaining: invite the (up to 6) members, migrate passwords off Gmail/WhatsApp
  into shared collections, set per-member access (ADR 017 / `financial-decisions.md`).
- **KeePassXC offline vault backup** (`.kdbx` in a safe / will) as a
  vendor-independent fallback (ADR 017 "secondary backup").
