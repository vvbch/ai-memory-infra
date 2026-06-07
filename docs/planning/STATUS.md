# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). **Read this first to
> resume.** Full reasoning lives in `docs/decisions/` and the private
> `interview_packet.md`. Working model + teaching prefs: `AGENTS.md`.

**Last updated:** 2026-06-07 (session wrap, ~90 min. Bitwarden vault + nominee set up;
`chandrav.dev` registered (10-yr prepay, redaction verified); **4 of 5 secrets
gathered** (DO token, CF token, Spaces key, SSH key — all in Bitwarden). New this
session: tenet 15, ADR 019 (compute provider), credential-custody DoD gate, BUILD-LOG
mechanism. **Next: OpenAI billing+key (5th secret), then assemble tfvars/.env + deploy.**)

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

## Last decisions (2026-06-07, session-resume)

- **Tenet 15 added — fixed, capped cost beats variable, even at a mild premium.**
  Predictability over marginal on-demand savings; hard spend caps + billing alerts on
  any usage-based service. In `tenets.md` + `AGENTS.md`. **Applications to do:**
  (a) set a **DigitalOcean billing alert** (billing now active); (b) set a **hard
  monthly usage limit + alerts on OpenAI** when that key is created (step 3); DO
  droplet/Spaces and the domain are already flat-rate (compliant).
- **Credential custody codified as a DoD gate** (ADR 017 generalized): every
  account/token/key lands in the Bitwarden `ai-memory-infra` individual-vault folder
  as created; SSO logins get a note for the nominee.
- **Compute provider documented (ADR 019) — closes a tenet-12 gap.** DigitalOcean
  was never written up vs hyperscalers. Verified: DO BLR1 $24/mo is at the floor for
  mainstream India-region flat-rate (ties Vultr/Linode; Lightsail egress is the
  variable trap; Hetzner ~60% cheaper but no India DC / no SLA). Single-node by design
  (HA out of scope — tenet 4 covers outages); best India latency; clean exit (plain
  Compose). Stay on DO for Phase 1; Hetzner/Alienware are documented revisit paths.

## Last clarification (2026-06-07, session-resume)

- **Bitwarden secrets must live in an individual-vault Folder, not a Families
  Collection (tenet-12 near-miss).** Verified Bitwarden Emergency Access — incl.
  Takeover — reaches only the grantor's *individual* vault, never org/Families
  collections ([bitwarden.com/help/emergency-access](https://bitwarden.com/help/emergency-access/)).
  The docs said "vault group," which would have led to a Collection and silently
  broken the nominee handoff. Clarified ADR 017 §Decision-1, `decommission.md` §0,
  and the next-action below. Root cause = ambiguous "group" in the spec; Families
  is still required (it's what unlocks Emergency Access).

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

> **RESUME HERE — gather secrets, then deploy.**

0. ✅ Cloudflare password rotated. ✅ Bitwarden account + **Families** plan taken.
1. ✅ **Bitwarden setup done:** Folder `ai-memory-infra` in the **individual vault**;
   Cloudflare login stored; elder son (`rkrishv14@gmail.com`) invited as **Takeover**
   contact (7-day wait). **Follow-ups:** (a) son must *accept* the invite, then YOU
   *confirm* him (Invited→Accepted→Confirmed) — not live until then; (b) secondary
   pass: add **wife** as a 2nd Takeover contact (8-yo can't — Bitwarden is 13+).
2. ✅ **`chandrav.dev` registered** at Cloudflare 2026-06-07 — **Active**, expiry
   2036-06-07, auto-renew ON, **10-yr prepay** ($122.20, eyes-open; see
   `financial-decisions.md`). Personal registrant + WHOIS redaction (on by default).
   ✅ **Public WHOIS verified redacted** (no name/email/phone/street — only State+Country).
3. **[gather secrets] — 4 of 5 done**, all in the Bitwarden `ai-memory-infra` folder:
   ✅ DO API token (`terraform-ai-memory`, Full Access) · ✅ Cloudflare API token
   (`terraform-ai-memory-dns`, zone-scoped to chandrav.dev) · ✅ DO Spaces key
   (`ai-memory-spaces`, Full access) · ✅ SSH keypair (`~/.ssh/id_ed25519`(.pub),
   passphrase in Bitwarden). **← NEXT: OpenAI (the 5th).** Account exists, **no
   billing yet**: (a) add card + **$10 prepaid credits, auto-recharge OFF** (tenet 15
   hard cap); (b) set a usage-limit email alert; (c) create an API key → Bitwarden.
4. **[assemble config]** Fill `infra/terraform/terraform.tfvars` (do_token,
   cloudflare_api_token, spaces access id/secret, ssh_public_key from
   `~/.ssh/id_ed25519.pub`, domain_name=`chandrav.dev`, backup_bucket_name) and
   `infra/.env` (secrets + OPENAI_API_KEY + DOMAIN/ACME_EMAIL) — both **gitignored**,
   values pulled from Bitwarden. Then `docs/setup.md` Steps 1–7: `tf-init` →
   `tf-plan` → **`tf-apply`** → `bootstrap.sh` → health-check `memory.chandrav.dev/docs`.
   (Mind the income-change risk above when picking deploy timing.)
