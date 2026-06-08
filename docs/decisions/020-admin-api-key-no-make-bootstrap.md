# ADR 020: Use the built-in `ADMIN_API_KEY`, not `make bootstrap`

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** Chandra

### Context

The Mem0 server's auth is on (`AUTH_DISABLED=false`, PR #4837). To make the API
*usable* we need a working admin credential. An earlier deploy-time note suggested
running mem0's `make bootstrap` (or its seed CLI) to "stand up an admin + API key."

On investigation that note is **wrong for our deployment**, verified against the
mem0 source/docs (`mem0ai/mem0`, PR #4837 + the server `Makefile`/`docker-compose`):

- `make bootstrap` = `docker compose up` against **mem0's own bundled compose**
  (its own Postgres + stack) plus a seed CLI. It assumes you run mem0's reference
  stack, not a custom one.
- **Our stack is custom** and runs from `/opt/ai-memory-infra/infra` with our own
  `docker-compose.yml` + `docker-compose.prod.yml` (Caddy + the from-source
  `mem0-api-server:local` + Postgres/pgvector + Neo4j). Running `make bootstrap`
  on the droplet would spin up a **second, conflicting Postgres/stack** — exactly
  the kind of duplicated moving part tenets 7 (fewer moving parts) and 4 forbid.

Separately, the server already had a usable credential: a 43-char `ADMIN_API_KEY`
was generated into the droplet `.env` at deploy time (legacy admin mode). It was
**verified working 2026-06-08**: `GET /memories?user_id=diag` returns **401
without** the key and **200 with** the `X-API-Key` header.

### Decision

**Authenticate via the built-in legacy `ADMIN_API_KEY` (sent as the `X-API-Key`
header). Do NOT run `make bootstrap` / mem0's seed CLI, and do NOT stand up the
dashboard / `/setup` wizard, on this deployment.** This keeps the API usable with
**zero** extra moving parts (tenet 7) and no duplicate database stack.

This decision is **locked** — it should not be re-litigated in future sessions.
The `make bootstrap` path is a known dead end for our topology, not an unexplored
option.

### Consequences / what stays available (reversible — tenet 12)

- Per-user `m0sk_`-prefixed keys and the interactive `/setup` wizard remain
  available **if** we later build and enable the Mem0 dashboard (parked in
  `BACKLOG.md` P2). Adopting them is additive; it does not require `make bootstrap`.
- Custody (tenet / ADR 017): the `ADMIN_API_KEY` lives in the droplet `.env`
  (safe at rest on the server) and must also be stored in the Bitwarden
  `ai-memory-infra` folder — the custody gate is the only open item from this work.

*(Sources: `github.com/mem0ai/mem0` — server `Makefile`/`docker-compose`, PR #4837
auth; verified on the running droplet 2026-06-08.)*

---
