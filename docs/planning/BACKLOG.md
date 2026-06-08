# Backlog — prioritized, deferred work

> Parked-but-valuable work, ranked. Captured so nothing is lost and nothing
> silently displaces the current goal (tenet 13). `STATUS.md` "Next action" is what
> we're doing *now*; this is what we've consciously chosen to do *later*.
>
> **Priorities:** **P1** = do at the next natural opportunity (security / soon-blocking).
> **P2** = governance/quality hardening, fold into the relevant phase. **P3** =
> valuable but non-blocking / personal.

## P1 — do at the start of Phase-1 CI work

- **`[security]` Strip the plaintext secrets block from `infra/.env`.** The
  generated dash/graph admin password (and copy-to-Bitwarden reminder) currently
  live as a comment block at the top of `infra/.env` — both locally and, after
  deploy, on the droplet. The values are already safe in Bitwarden, so delete the
  block from both copies; nothing plaintext should sit at rest. Consciously
  deferred 2026-06-07. Ties: AGENTS.md secrets rule, ADR 017, tenet 14.
- **`[security]` Secret-scan pre-commit (e.g. gitleaks).** Make "no secrets in git" a
  *deterministic gate*, not just a prose rule — relevant now that we handle DO /
  Cloudflare / OpenAI tokens. Ties: AGENTS.md secrets rule, tenet 14 (Detect layer).

- **`[deploy]` Make the deploy reproducible end-to-end.** The Mem0 API image is built
  by hand this session (`infra/mem0-server.Dockerfile` against `/opt/mem0-src/server`,
  tagged `mem0-api-server:local`) because the published image is arm64-only. A fresh
  `bootstrap.sh` would fail at `docker compose pull` (can't pull a local-only image; the
  dashboard image 404s). Fix: fold `git clone mem0ai/mem0` + `docker build` into
  `bootstrap.sh` (or build + push `mem0-api-server` to GHCR and reference that), make the
  `pull` step tolerant, and **update `setup.md`** (prereqs + Step 6) to match (tenet 10).

- **`[deploy]` Document the OpenAI project model-access requirement in `setup.md`.** Step 4
  (round-trip) was blocked because the OpenAI project was scoped to only `gpt-5-mini`, so
  `text-embedding-3-small` returned 403 and every `add` failed. `setup.md` (Step 0/secrets +
  Step 7 "Done when") should call out: the OpenAI project must allow **both** `gpt-5-mini` and
  `text-embedding-3-small` (or "allow all models"); the project model allow-list UI is currently
  buggy (use "allow all", or the Admin API model-permissions endpoint). Tie: ADR 013/011, tenet
  10. Control-plane fix for the step-4 blocker (2026-06-08).

> **Resolved / moved out of backlog:** "Stand up admin/API-key + confirm model
> config" is **no longer deferred** — the admin key is done (built-in
> `ADMIN_API_KEY`, **not** `make bootstrap`; see **ADR 020**, locked) and the
> model-config + `POST /memories` round-trip are the active `STATUS.md` "Next
> action" (steps 3–4). Do not re-add `make bootstrap` here — it would stand up a
> conflicting second DB stack (ADR 020).

## P2 — governance & quality hardening (fold into CI / eval phases)

- **`[deploy]` Build & re-enable the Mem0 dashboard.** No published `mem0/mem0-dashboard`
  image exists; it's gated behind the compose `dashboard` profile and deferred. Build it
  from the mem0 repo's `server/dashboard` context (Next.js, needs a node build), then
  `docker compose --profile dashboard up -d` and confirm `dash.chandrav.dev` works
  (the Caddy route + DNS already exist). The `/setup` wizard lives here too.
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

## P3 — valuable, non-blocking / personal

- **Bitwarden full family rollout.** Families plan already paid (2026-06-07).
  Remaining: invite the (up to 6) members, migrate passwords off Gmail/WhatsApp
  into shared collections, set per-member access (ADR 017 / `financial-decisions.md`).
- **KeePassXC offline vault backup** (`.kdbx` in a safe / will) as a
  vendor-independent fallback (ADR 017 "secondary backup").
