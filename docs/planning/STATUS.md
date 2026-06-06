# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). **Read this first to
> resume.** Full reasoning lives in `docs/decisions/` and the private
> `interview_packet.md`. Working model + teaching prefs: `AGENTS.md`.

**Last updated:** 2026-06-06 (single Cursor session — control + build unified)

## Current phase

**Phase 1 — Infrastructure as Code.** All Phase-1 infra files are written and
look correct (`infra/terraform/*` — `main.tf`/`variables.tf`/`outputs.tf`/
`backend.tf` + `terraform.tfvars.example`; `infra/docker-compose.yml` +
`.prod.yml`; `infra/Caddyfile`; `infra/.env.example`; `scripts/bootstrap.sh`;
`infra/Makefile`). **Not yet `terraform validate`'d or applied** — Terraform/
Docker aren't installed on this machine yet (see blockers). Tenet 11 repo-health
instrumentation is **built, committed, and verified** (see below).

## Done this session (2026-06-06)

- **Tenet 11 repo-health instrumentation — built + live-verified, all 3 layers:**
  - `scripts/check-repo-health.ps1` (git fsck + `.git` conflicted-copy scan +
    stale `index.lock` + ahead/behind; `-Fast` subset; repo list via
    `AI_MEMORY_REPOS` env or `-RepoList`; logs + non-zero exit on failure).
    Verified healthy AND failure-path (injected conflict+lock → exit 1 + log).
  - `scripts/hooks/pre-commit` + `scripts/install-hooks.ps1` — **installed in both
    repos** (copy, not symlink — tenet 3). Hook fired + passed on commit `e86e809`.
  - `scripts/register-repo-health-task.ps1` — Windows Task Scheduler task
    **"AI-Memory Repo Health"** registered, daily 09:00, Interactive logon (no
    admin); ran clean (result 0). Failure logs → `%LOCALAPPDATA%\ai-memory-repo-health\logs`.
  - `infra/Makefile` targets (`repo-health`, `repo-health-fast`, `install-hooks`,
    `register-health-task` — Unix/WSL); `.gitignore` `.repo-health-logs/`;
    runbook "Drive-sync integrity" commands aligned. `AI_MEMORY_REPOS` User env set.
- **Pushed:** public `010420c → af293e7 → e86e809`; private `4471473 → 8d06673`.
  Both repos clean, `0 ahead / 0 behind origin/main`.
- Empty `docs/landingzone/` **deleted**; inbox fully drained (old packet + recovery
  copy reconciled into private packet, then deleted).

## Last decisions (2026-06-06)

- **Extraction model → `gpt-5-mini`** (was `gpt-4.1-nano`; ADR 013's "nano = Mem0
  default" was stale — current default is `gpt-5-mini`, verified vs `mem0ai/mem0`).
  ~₹90/mo (~2–3× nano); chosen for structured-output reliability, not cost.
  Embeddings stay `text-embedding-3-small`. Propagated everywhere.
- **Single Cursor session** for planning + execution (CONTROL/BUILD split and the
  Claude.ai surface retired). Safeguard = the DoD verification gate.
- **Mem0 hybrid retrieval is native/on**; reranker = a flag left OFF, gated on
  Phase-7 precision@5 < 0.7 (ADR 007 note).
- **Bounded shift-left telemetry → ADR 014**; **Drive risk → Tenet 11 + ADR 015**.
- **ADR 002** superseded note reframed to `gpt-5-mini`.
- Earlier (2026-06-05): single-provider OpenAI; `text-embedding-3-small` (ADR 011);
  DNS zone @ DigitalOcean (ADR 012, domain TBD); tenets 6–10; documentation DoD.

## Open blockers / risks

- **Local tooling missing — the gating blocker.** `terraform`, `docker`, and
  `make` are **not installed** on this machine. So `terraform fmt/validate/plan/
  apply`, the local Compose stack, and `make` targets can't run here yet. Install
  Terraform + Docker Desktop (winget) — or validate via CI. (git + PowerShell 5.1
  work fine; the shell backend that was flaky earlier has recovered.)
- **Domain name + registrar still TBD** — the only *decision* blocking forward
  progress; blocks Terraform DNS (`domain_name` has no default) + Caddyfile.
- **Verify at deploy:** pinned Mem0 image bundles `psycopg`/`langchain-neo4j`
  (else patch Dockerfile); `mem0-dashboard` published tag exists (else build from
  repo); `gpt-5-mini` works as a per-component Mem0 LLM config on the pinned
  server version; **GHCR package visibility** set per image after the first
  `docker-build.yml` push (separate from repo visibility).
- **Operator-gated deploy** (guardrail): `terraform apply`, `ssh`, `bootstrap.sh`
  on the droplet are operator-run; needs DO API token, DO Spaces keys, SSH
  keypair, registered domain, OpenAI key.

## Environment notes (for the resuming session)

- **Shell works.** Use the `working_directory` parameter, **not** `cd "long Drive
  path"` (spaces + parens in `My Drive (…)` break raw `cd`). git push auth is
  cached (credential.helper=manager) — commits + pushes work directly.
- **No PowerShell 7** — Windows PowerShell 5.1 only. Invoke scripts as
  `powershell -ExecutionPolicy Bypass -File …`. The repo-health scripts are 5.1-safe.
- Repos: `github.com/vvbch/ai-memory-infra(-private)` over HTTPS. Identity:
  `Chandra V <vvbchandrasekhar@gmail.com>`.

## Next action

1. **[operator] Unblock the toolchain:** install **Terraform** + **Docker
   Desktop** (e.g. `winget install Hashicorp.Terraform`, `winget install
   Docker.DockerDesktop`). Optional: `make`.
2. **[operator] Pick the domain + registrar**, buy it, set it in
   `terraform.tfvars`, and delegate NS to `ns1/ns2/ns3.digitalocean.com`.
3. **[this session] Validate the IaC:** `make tf-fmt` + `terraform validate`
   (once Terraform is installed); fix anything that surfaces.
4. Then `docs/setup.md` → "Phase 1 — deploy to the VPS" (operator-run): fill
   `terraform.tfvars` + `infra/.env` → `make tf-init` → `tf-plan` → **`tf-apply`**
   → registrar NS → `bootstrap.sh` on droplet → health-check
   `https://memory.<domain>/docs`. Two-step remote-state bootstrap per `backend.tf`.

Prereqs to gather: DO API token, DO Spaces key pair, SSH keypair, registered
domain, OpenAI API key.
