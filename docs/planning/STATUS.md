# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). Read this first to
> resume. Full reasoning lives in `docs/decisions/` and `docs/interview_packet.md`.

**Last updated:** 2026-06-05

## Current phase

**Phase 1 — Infrastructure as Code.** All Phase-1 infra files are drafted
(`infra/terraform/*`, `infra/docker-compose.yml` + `.prod.yml`, `infra/Caddyfile`,
`infra/.env.example`, `scripts/bootstrap.sh`, `infra/Makefile`). Not yet applied
to a real VPS (needs cloud creds + a registered domain — operator-run).

## Last decisions

- **Single-provider OpenAI** for both stages: `gpt-4.1-nano` (extraction) +
  `text-embedding-3-small` (embeddings). ADR 013 **supersedes** ADR 002
  (DeepSeek). DeepSeek/Qwen kept as documented, swappable alternatives.
- **Embeddings = `text-embedding-3-small`** (ADR 011); embedder swaps require a
  re-embed migration (dim change), not a hot flip.
- **DNS zone at DigitalOcean** (ADR 012); Terraform owns all records; domain name
  still **TBD** (placeholder in `terraform.tfvars.example`).
- **Tenets 6–10** promoted (cost, simplicity, verify-tier, single-provider,
  single-source-of-truth).
- **Documentation discipline** established: `interview_packet.md`, this file,
  AGENTS.md Definition-of-Done trigger table, PR checklist, `.cursor` rule.
- Verified vs the actual mem0 repo: server compose **ships** `mem0-dashboard`
  (kept `dash.`) and **has** built-in JWT auth (`AUTH_DISABLED=false`).

## Open blockers / risks

- **Exec/shell backend intermittently down** this session — could not run `git`,
  `terraform fmt`, or `terraform validate`. Commits handed to operator as commands.
- **Deploy needs operator action** (guardrail): DO API token, Spaces key pair,
  SSH keypair, registered domain. `terraform apply` / `ssh` / `doctl` are
  operator-run.
- **Verify at deploy:** mem0 API image tag bundles `psycopg`/`langchain-neo4j`
  (else patch Dockerfile); `mem0-dashboard` published image tag exists (else build
  from repo); `gpt-4.1-nano` + `text-embedding-3-small` both served by the single
  `OPENAI_API_KEY`.

## Next action

**Follow `docs/setup.md` → "Phase 1 — deploy to the VPS"** (full step-by-step,
operator-run). In short: fill `terraform.tfvars` + `.env` → `make tf-init` →
`make tf-plan` → **`make tf-apply` [operator]** → set registrar NS to DO →
`bootstrap.sh` on the droplet **[operator]** → health-check
`https://memory.<domain>/docs`. Then close Phase 1 (health script + CI green +
merge) and move to Phase 2 (backup/restore).

Prereqs to gather first: DO API token, DO Spaces key pair, SSH keypair,
registered domain, OpenAI API key.
