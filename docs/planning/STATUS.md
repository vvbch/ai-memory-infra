# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). **Read this first to
> resume.** Full reasoning lives in `docs/decisions/` and the private
> `interview_packet.md`. Working model + teaching prefs: `AGENTS.md`.

**Last updated:** 2026-06-07 (session wrap / context-exhausted handoff. This
session: ADRs 016–018, tenets 13–14, COE practice + prioritized backlog, Bitwarden
**Families** taken. **Next: finish Bitwarden vault + buy `chandrav.dev`, then
secrets + deploy.**)

## Current phase

**Phase 1 — Infrastructure as Code.** IaC is written, **`terraform fmt`-clean +
`terraform validate`-pass** with **Cloudflare DNS** (ADR 016; supersedes ADR 012).
Providers: `digitalocean ~> 2.0` + `cloudflare ~> 5.0`. **Not yet `plan`'d or
applied** — needs domain registered at Cloudflare first, then DO/CF tokens +
secrets (see blockers). Tenet 11 repo-health instrumentation is live (below).

## Done this session (2026-06-07, Path B — Cloudflare registrar + DNS)

- **Chandra chose Path B** (Cloudflare = registrar + DNS; DO = compute only).
- **ADR 016** written (`docs/decisions/016-cloudflare-registrar-and-dns.md`);
  **ADR 012** marked superseded.
- **Terraform DNS block rewritten:** removed `digitalocean_domain` /
  `digitalocean_record`; added `cloudflare` provider, `data.cloudflare_zone`,
  `cloudflare_dns_record` (proxied=false for ACME). New var `cloudflare_api_token`;
  output `cloudflare_zone_id` replaces `registrar_nameservers`.
- **Docs updated (DoD):** `setup.md` (Step 0b register at CF; removed NS
  delegation step), `architecture.md`, `decommission.md`, `teardown.py`,
  `terraform.tfvars.example` (`chandrav.dev` placeholder).
- **Re-validated:** `terraform fmt` + `init -backend=false` + `validate` → **Success**
  (lock file updated with `cloudflare/cloudflare v5.19.1`).

## Done earlier (2026-06-06)

- Tenet 12, decommission runbook + `teardown.py`, repo-health (tenet 11), Terraform
  install + initial DO-only validate, extraction → `gpt-5-mini` (ADR 013), etc.
  See git history / prior STATUS sections.

## Last decisions (2026-06-07)

- **COE practice codified (tenet 14).** Blameless Correction-of-Errors with a
  template + index in `docs/coe/`; first COE = the cursor-rule drift. Fix control
  plane before data plane; depth ∝ blast radius. Deferred work moved to a
  prioritized `docs/planning/BACKLOG.md`. Interview packet now frames
  **Eng / Product / Program** dimensions + PM/PgM STARs.
- **Governance fix → editor pointer files carry zero canonical content (ADR 018).**
  `00-project.mdc` had drifted into a duplicated rules summary (violating tenets
  2 & 10). 5-whys → root cause: the spec defined "thin pointer" but never its
  *boundary* or *enforcement*, and pointer files weren't in the DoD. Fixed control
  plane (tenet 2 boundary + DoD row) then data plane (stripped the file to a pure
  pointer). Lessons in `interview_packet.md` §7. Automated lint **parked**.
- **Tenet 13 added — stay on the critical path; diverge deliberately** (caution →
  advise → rarely stop). In `tenets.md` + `AGENTS.md` + the cursor pointer.
- **Password manager → Bitwarden, Families plan (ADR 017).** Vault group
  `ai-memory-infra` holds all logins + SSH passphrase; **never** in a repo. Nominee
  handoff = Bitwarden **Emergency Access** (Takeover, time-delayed). Beat 1Password /
  Proton Pass / KeePassXC. **Took Families ($47.88/yr, ~₹330/mo)** over individual
  Premium — longer-term family call + front-loading before a possible end-June income
  change (private `financial-decisions.md`). `decommission.md` §0 has the exact steps.
- **Registrar + DNS → Cloudflare (ADR 016).** Domain name: **`chandrav.dev`**
  (not yet purchased). App URL: `memory.chandrav.dev`. DO remains compute-only.
  Rationale: tenet-12 tier-1 vendor profile (NET, ecosystem, at-cost registrar).

## Security follow-up (operator)

- ✅ **Cloudflare password rotated** 2026-06-07 (old one had been pasted in chat).
  Store the new one in Bitwarden once set up; never in chat/repo.

## Backlog (parked work)

Prioritized backlog lives in **`docs/planning/BACKLOG.md`** (P1/P2/P3) — single
source so it can't drift. Holds deferred-but-valuable work (P1 secret-scan
pre-commit; P2 policy-as-code pointer enforcement + eval/CI gates; P3 Bitwarden
family rollout + KeePassXC offline backup) so nothing is lost and nothing
displaces the Phase-1 deploy (tenet 13).

## Open blockers / risks

- **Domain not bought yet.** Register `chandrav.dev` at Cloudflare Registrar
  (setup Step 0b) before `terraform apply` — the zone must exist.
- **Local tooling:** `docker` + `make` still not installed (Compose stack runs on
  VPS; optional locally). `terraform` v1.15.5 works.
- **Secrets not gathered:** DO API token, DO Spaces keys, Cloudflare API token
  (Zone → DNS → Edit), SSH keypair, OpenAI key → `terraform.tfvars` + `infra/.env`.
- **Verify at deploy:** Mem0 image tags, `gpt-5-mini` on pinned server version,
  GHCR package visibility (unchanged from prior STATUS).
- **Operator income change risk (end-June 2026).** Possibly between jobs soon →
  once deployed, recurring spend (~₹2,920/mo) must stay **pause-able**. The pause
  path (`decommission.md` §2 → `teardown.py`) drops the ~₹2,000/mo droplet in one
  command. Factor into *deploy timing* (tenet 12 / `financial-decisions.md`).

## Environment notes

- Use `working_directory` param, not raw `cd` (Drive path has spaces/parens).
- Windows PowerShell 5.1 only; git push auth cached.
- Repos: `github.com/vvbch/ai-memory-infra(-private)`.

## Next action

> **RESUME HERE — finish Bitwarden, buy the domain, then secrets, then deploy.**

0. ✅ Cloudflare password rotated. ✅ Bitwarden account + **Families** plan taken.
1. **[YOU] Finish Bitwarden setup:** create vault group `ai-memory-infra`; store the
   **new Cloudflare login** there now (and DO/OpenAI/SSH secrets as you generate
   them); add the nominee as a **Takeover** emergency contact (`decommission.md` §0).
2. **[YOU — one click path] Register `chandrav.dev` at Cloudflare** — `docs/setup.md`
   Step 0b (Domain Registration → Register Domains → checkout). Confirm Active under
   Websites.
3. **[gather secrets]** DO API token, DO Spaces key pair, Cloudflare API token
   (Zone→DNS→Edit), SSH keypair, OpenAI API key → `terraform.tfvars` + `infra/.env`.
4. **`docs/setup.md` Steps 1–7:** `tf-init` → `tf-plan` → **`tf-apply`** →
   `bootstrap.sh` on droplet → health-check `https://memory.chandrav.dev/docs`.
   (Mind the income-change risk above when picking deploy timing.)
