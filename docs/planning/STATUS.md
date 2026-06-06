# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). Read this first to
> resume. Full reasoning lives in `docs/decisions/` and the private
> `interview_packet.md`.

**Last updated:** 2026-06-06 (single Cursor session — control + build unified)

## Current phase

**Phase 1 — Infrastructure as Code.** All Phase-1 infra files are drafted
(`infra/terraform/*`, `infra/docker-compose.yml` + `.prod.yml`, `infra/Caddyfile`,
`infra/.env.example`, `scripts/bootstrap.sh`, `infra/Makefile`). Not yet applied
to a real VPS (needs cloud creds + a registered domain — operator-run). This
session landed planning/decisions + doc upkeep; implementation resumes **in this
same Cursor session** at `infra/terraform/variables.tf`.

## Last decisions (this session, 2026-06-06)

- **Extraction model → `gpt-5-mini`** (was `gpt-4.1-nano`). ADR 013's "nano = Mem0
  default" rationale was **stale**: Mem0's current default is `gpt-5-mini`
  (verified vs `mem0ai/mem0` + SDK changelog). Cost ~₹90/mo (~2–3× nano, still
  trivial); chosen for **structured-output reliability** (JSON + venture
  categorization), not cost. Embeddings stay `text-embedding-3-small`. ADR 013
  updated; propagated to AGENTS, architecture, README, setup, `.env.example`.
- **Tooling consolidated on a single Cursor session.** Planning *and* execution
  now run in one Cursor session against the repo (no separate CONTROL/BUILD
  split; Claude.ai surface retired). Safeguard = the DoD verification gate, not a
  second tool. (AGENTS.md "Working model".)
- **Gemini RAG mitigations are mostly native to Mem0** (verified): hybrid search
  (vector+BM25+entity) on by default → build nothing; reranker = a flag, left OFF,
  enable only if Phase-7 precision@5 < 0.7; "lost-in-the-middle" misapplied (we do
  short-input extraction, not synthesis). Recorded as an ADR 007 note.
- **Bounded shift-left telemetry ratified → ADR 014.** Phase 1 adds a `/metrics`
  endpoint + per-extraction log (input/output/model id/tokens/ts); dashboards,
  drift baselines, cross-LLM cost-vs-quality deferred to Phases 7/8.
- **Drive-synced repo risk accepted + instrumented → Tenet 11 + ADR 015.** Repos
  (incl. `.git/`) live under Drive Mirror; GitHub is truth; commit+push every
  session; `check-repo-health` at session-start/pre-commit/daily; re-clone (not
  repair) on red. Runbook "Drive-sync integrity" section added.
- **Private interview packet regenerated** from `_inbox/` single source (inbox
  copy deleted); §2 model+cost, §3 four new dated entries, §4 dashboard RESOLVED.
- **ADR 002** reframed (superseded note now points to `gpt-5-mini`).
- Earlier (2026-06-05, unchanged): single-provider OpenAI; embeddings
  `text-embedding-3-small` (ADR 011); DNS zone at DigitalOcean (ADR 012, domain
  still TBD); tenets 6–10; documentation-discipline DoD.

## Open blockers / risks

- **Exec/shell backend down this session** — could not run `git`, `terraform
  fmt`, `terraform validate`, or delete the empty dir. Git commits + the
  `docs/landingzone/` delete are **handed to the operator as commands** (see
  handoff in chat). Commit+push BOTH repos this session (Tenet 11 — never batch).
- **Empty `docs/landingzone/` not yet deleted** (shell down) — operator command
  pending; confirm `git status` clean after.
- **Domain name + registrar still TBD** — blocks Terraform DNS + Caddyfile
  (not `variables.tf`). Placeholder in `terraform.tfvars.example` / `.env`.
- **Repo-health firing model CONFIRMED** (all 3): Windows Task Scheduler (daily,
  unattended, full) + git pre-commit hook (fast subset, `make install-hooks`) +
  AGENTS.md soft line (already in AGENTS.md). Ready to build the scripts.
- **Verify at deploy:** pinned Mem0 image bundles `psycopg`/`langchain-neo4j`
  (else patch Dockerfile); `mem0-dashboard` published tag exists (else build from
  repo); `gpt-5-mini` works as a per-component Mem0 LLM config on the pinned
  server version; **GHCR package visibility** set + verified per image after
  `docker-build.yml` first pushes (separate from repo visibility).

## Next action

1. **[operator]** Commit + push BOTH repos (commands handed in chat); delete
   empty `docs/landingzone/`; confirm `git status` clean.
2. **Firing model CONFIRMED = all three layers** (Task Scheduler daily + git
   pre-commit hook via `make install-hooks` + AGENTS.md soft line). Wire
   `scripts/check-repo-health.*` + `make install-hooks` + the Task Scheduler
   register script in this session (Tenet 11 instrumentation — see BUILD TASK).
3. **Resume Phase 1 in this session** at `infra/terraform/variables.tf`; once a
   shell is live, `make tf-fmt` + `terraform validate`.
4. Then follow `docs/setup.md` → "Phase 1 — deploy to the VPS" (operator-run:
   `tfvars`/`.env` → `make tf-init` → `tf-plan` → **`tf-apply`** → set registrar
   NS to DO → `bootstrap.sh` on droplet → health-check
   `https://memory.<domain>/docs`).

Prereqs to gather first: DO API token, DO Spaces key pair, SSH keypair,
registered domain, OpenAI API key.
