# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). **Read this first to
> resume.** Full reasoning lives in `docs/decisions/` and the private
> `interview_packet.md`. Working model + teaching prefs: `AGENTS.md`.

**Last updated:** 2026-06-06 (single Cursor session — control + build unified)

## Current phase

**Phase 1 — Infrastructure as Code.** All Phase-1 infra files are written and
**now `terraform fmt`-clean + `terraform validate`-pass** (`infra/terraform/*` —
`main.tf`/`variables.tf`/`outputs.tf`/`backend.tf` + `terraform.tfvars.example`;
`infra/docker-compose.yml` + `.prod.yml`; `infra/Caddyfile`; `infra/.env.example`;
`scripts/bootstrap.sh`; `infra/Makefile`). **Not yet `plan`'d or applied** — that
needs the DO backend creds + a `domain_name` (no default) + secrets (see blockers).
Tenet 11 repo-health instrumentation is **built, committed, and verified** (below).

## Done this session (2026-06-06, governance + exit path)

- **Tenet 12 added — "Vendors are deliberated, documented, and reversible."** No
  provider adopted *suddenly*; weigh cost (incl. **exit cost**), portability,
  reliability, company viability, ecosystem in an ADR. (`docs/tenets.md` +
  `AGENTS.md` summary + `.cursor/rules/00-project.mdc`; fixed the stale "skip
  basics" line there → concierge mode.)
- **Decommission / rollback / estate runbook modeled** (`docs/decommission.md`):
  rollback a bad deploy · pause to stop the bill · full decommission closing all
  3 billable accounts (DO / registrar / OpenAI) — written for a non-engineer
  executor. Automated by **`scripts/teardown.py`** (cross-platform, confirmed
  wrapper around `terraform destroy`; `make teardown` / `make tf-plan-destroy`).
  Linked from `runbook.md` + `setup.md`.
- **Domain purchase PAUSED.** Porkbun was picked too fast (no tenet-12 analysis);
  reopened as a documented registrar + DNS-host decision — see blockers / Next action.

## Done this session (2026-06-06, validation pass)

- **Terraform installed** via `winget install Hashicorp.Terraform` → **v1.15.5**
  (binary under `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Hashicorp.Terraform_*`;
  PATH updated, new shells pick it up — current shells need a restart).
- **IaC validated:** `terraform -chdir=infra/terraform fmt -check -recursive` →
  clean; `init -backend=false` installed **digitalocean/digitalocean v2.87.0** and
  wrote `.terraform.lock.hcl`; `terraform validate` → **"Success! The configuration
  is valid."** No changes to the `.tf` files were needed.
- **Committed `infra/terraform/.terraform.lock.hcl`** (provider pin, tenet 1).
- Session-start repo-health check (Tenet 11): both repos OK, 0 ahead / 0 behind.
- **Still not installed:** Docker Desktop + `make` (not needed for `validate`;
  needed for the local Compose stack + `make` targets).

## Done earlier (2026-06-06)

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

- **Local tooling — partially unblocked.** `terraform` is now installed (v1.15.5)
  and `fmt`/`init`/`validate` work here. **`docker` + `make` are still not
  installed** → the local Compose stack and `make` targets can't run on this
  machine yet (install Docker Desktop via winget, or run the stack on the VPS).
  (git + PowerShell 5.1 work fine.)
- **Domain + registrar + DNS-host — the top *decision*, now a tenet-12 vendor
  call (not a snap pick).** DigitalOcean is *not* a registrar, so a registrar is
  unavoidable regardless of name. Live choice: (A) keep DNS at DO [ADR 012, already
  built/validated] + a custom-NS registrar (Porkbun/Namecheap), or (B) consolidate
  name+DNS at **Cloudflare** (tier-1 vendor, but rewrites the TF DNS block + revisits
  ADR 012). Name leaning `chandrav.dev` (`chandra.dev` taken). Blocks `plan/apply`
  (`domain_name` no default) + Caddyfile. **Awaiting operator decision** + an ADR.
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

1. ✅ **Terraform installed + IaC validated** (this session — see "Done"). Optional
   remaining toolchain: install **Docker Desktop** (`winget install
   Docker.DockerDesktop`, needs a reboot) + `make` only if you want to run the
   Compose stack / `make` targets *locally*; otherwise the stack runs on the VPS.
2. **[decision — the gate] Registrar + DNS-host vendor call (tenet 12).** Decide
   option A (DO DNS + custom-NS registrar) vs B (Cloudflare name+DNS); write the
   ADR; then buy the name (`chandrav.dev`), set `domain_name` in `terraform.tfvars`,
   and (option A) delegate NS to `ns1/ns2/ns3.digitalocean.com`. If B, update ADR
   012 + rewrite the `digitalocean_record` block to `cloudflare_record` + re-validate.
3. **[gather secrets]** DO API token, DO Spaces key pair, SSH keypair, OpenAI API
   key (+ Cloudflare API token if option B) → `terraform.tfvars` + `infra/.env`.
4. Then `docs/setup.md` → "Phase 1 — deploy to the VPS": `tf-init` (two-step
   remote-state bootstrap per `backend.tf`) → `tf-plan` → **`tf-apply`** →
   registrar NS → `bootstrap.sh` on droplet → health-check
   `https://memory.<domain>/docs`.
