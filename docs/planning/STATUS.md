# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). **Read this first to
> resume.** Full reasoning lives in `docs/decisions/` and the private
> `interview_packet.md`. Working model + teaching prefs: `AGENTS.md`.

**Last updated:** 2026-06-08 (control-plane session — **tenet 16: stateless, disposable
sessions**. Codified after a long-lived Cursor session burned a month's $60 plan credits in
half a day (context-window amplification, COE 2026-06-08): one task per chat, checkpoint
`STATUS.md` per step, end every response with a Resume prompt. No deploy state changed —
**Next action is unchanged** (create admin + API key). Prior header retained below.)

**Prior update:** 2026-06-07 (session-resume #3 — **PHASE 1 DEPLOYED**. `tf-apply`
created the droplet (BLR1, `168.144.145.29`) + firewall + Cloudflare DNS + Spaces
bucket; the droplet was bootstrapped and the Compose stack is **live and healthy over
HTTPS**: `memory.chandrav.dev/docs` → 200 w/ valid Let's Encrypt cert; Caddy basic-auth
active on `graph.`. Hit + fixed 4 deploy-time issues (Mem0 image is arm64-only → built
from source for amd64 w/ graph + psycopg[binary] deps; SQLite history volume; auth-DB
name; dashboard has no published image → deferred behind a compose profile). **Next:
create admin/API key + verify model config, then a `POST /memories` round-trip; commit
the uncommitted infra changes.**)

## Plain English — where we are (resume here)

**The server is up and the website works.** Open
[https://memory.chandrav.dev/docs](https://memory.chandrav.dev/docs) in a browser — you
should see the API documentation page. That means: cloud box running in Bangalore,
password-protected lock on the front door (HTTPS), and the memory app installed.

**What you pay for now:** ~₹2,600/mo for the cloud box (droplet). Full stack when
everything runs ≈ ₹3,800/mo landed. You can pause/stop the box anytime with
`scripts/teardown.py` if income gets tight.

**What's NOT done yet (next session):**
1. **Save our work to GitHub** — 5 files changed on your laptop but not committed yet.
2. **Create a login for the API** — the app has a lock on it; nobody can add memories
   until we create an admin account + API key on the server (one-time setup).
3. **Test it** — add one test memory, read it back, confirm it stuck.
4. **Make reinstall repeatable** — if we had to rebuild the server from scratch today,
   the install script would need a manual fix (we built the app image by hand this
   session). Parked in BACKLOG.

**How to talk to the next agent:** paste the line in the box below into a **new chat**.
Ask for **concierge mode** (one step at a time, plain English, no jargon).

```
Resume ai-memory-infra — read STATUS.md (Plain English section) and AGENTS.md, run repo-health, then Next action step 2: create admin + API key. Concierge mode, one step at a time.
```

**Your passwords:** all in Bitwarden folder `ai-memory-infra`. SSH into the server still
needs your key passphrase (also in Bitwarden). Never paste secrets in chat.

## Current phase

**Phase 1 — Infrastructure as Code → DEPLOYED.** `tf-init`/`plan`/`apply` all run:
9 resources created (droplet `s-2vcpu-4gb` BLR1 `168.144.145.29`, firewall 22/80/443,
5 Cloudflare A records, Spaces bucket `ai-memory-infra-backups-chandrav`). Droplet
bootstrapped (Docker + Compose + UFW). **Core stack live & healthy**: Caddy + Mem0
(built from source, `mem0-api-server:local`) + Postgres/pgvector + Neo4j. RAM ~1.6G/3.9G
used (headroom OK). `memory.chandrav.dev/docs` → 200 over HTTPS w/ valid cert. To
*use* the API still needs admin/API-key setup + model-config verification (blockers below).

## Done this session (2026-06-07, session-resume #3 — DEPLOY)

- **`tf-apply` succeeded** — 9 resources. Outputs: `droplet_ipv4 168.144.145.29`,
  `cloudflare_zone_id 1766c7ea…`, bucket `…-chandrav` (sgp1). Plan validated all creds.
- **Config assembled** from Bitwarden into `terraform.tfvars` + `infra/.env` (both
  gitignored; LF endings forced for the Linux box). `.env` secrets generated locally
  (Python `secrets` + bcrypt); stored in Bitwarden.
- **Droplet bootstrapped** via `ssh-add`-cached key (agent ran `scp` + `bootstrap.sh`).
- **4 deploy-time fixes (all were flagged "verify at deploy"):**
  1. **`mem0/mem0-api-server:latest` is arm64-only** (no amd64) → built from the
     `mem0ai/mem0` `server/` source for amd64 via new **`infra/mem0-server.Dockerfile`**,
     adding `psycopg[binary,pool]` (stock req omits libpq) + `mem0ai[graph]` +
     `langchain-neo4j` + `rank-bm25` (Neo4j graph deps the stock req omits).
  2. **Mem0 SQLite history** (`/app/history`, `HISTORY_DB_PATH`) → added named volume
     `mem0_history`.
  3. **Auth DB** (`db.py` `APP_DB_NAME`, default `mem0_app`, never created) →
     consolidated onto the `mem0` DB via `APP_DB_NAME=mem0` (tenet 7).
  4. **`mem0/mem0-dashboard` has no published image** → gated behind compose profile
     `dashboard`; deferred (build-from-source follow-up).
- **Verified:** API 200 over HTTPS w/ valid Let's Encrypt cert; `graph.` basic-auth
  returns 401 (bcrypt hash works; the `wdqOTNUqJsh` Compose warning is harmless noise).
- **Gmail filters** (3) set up for infra mail (DO/OpenAI/Bitwarden/LE visible+important;
  Cloudflare visible; GitHub auto-archived) under label `ai-memory-infra`.
- **Uncommitted** (review + commit): `infra/mem0-server.Dockerfile` (new),
  `infra/docker-compose.yml` (image→local, `APP_DB_NAME`, `mem0_history`, dashboard
  profile), `docs/planning/BACKLOG.md`, this `STATUS.md`.

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

## Last decisions (2026-06-07, session-resume #2)

- **OpenAI = 5th secret gathered.** $10 prepaid credits on Amex (after card-decline
  troubleshooting — enable international txns; Visa/MC credit > Amex > debit/RuPay on
  OpenAI's processor); **auto-recharge OFF** = the real tenet-15 hard cap (the dashboard
  "usage limit" is only advisory/late). Org budget set to $10 with 80%/100% email alerts.
  API key `ai-memory-prod` (project `ai-memory`) stored in Bitwarden. **All 5 secrets now
  in the vault** → the secrets deploy-blocker is cleared.
- **Landed-cost discipline codified (×1.3) — tenet-6 sharpening, tenet-14 control-plane
  fix.** The OpenAI buy exposed that all our `(~₹X/mo)` figures were *list/spot* and
  ignored **18% GST + ~4–6% forex**, making budgets ~30% optimistic. Codified **landed ≈
  list × 1.3** (canonical in private `financial-decisions.md`; tenet-6 note in `tenets.md`
  + `AGENTS.md`; depersonalized TCO footnote in public `architecture.md`). Re-baselined
  every line: **true steady-state ~₹3,800/mo landed** (was ₹2,920 list). Parked a
  zero-forex card as a *personal* finance call (≈₹1.2k/yr saving; off the critical path).

## Last decisions (2026-06-08, control-plane session)

- **Tenet 16 added — stateless, disposable, single-task sessions.** State lives in the
  **repo, not the chat**: checkpoint `STATUS.md` after *every* step and **end every response
  with a copy-paste Resume prompt**, so a fresh chat resumes with zero loss. In `tenets.md` +
  `AGENTS.md` (Working model rewritten: "single session" → one *surface*, many short
  *sessions*) + a DoD gate. Twelve-Factor stateless-process + backing-store; reinforces
  tenets 1, 13, 15.
- **COE 2026-06-08 — credit exhaustion.** A long-lived stateful session re-sends its whole
  transcript each turn → ~quadratic token cost (*context-window amplification*); one half-day
  session exhausted the **$60/mo Cursor plan credits**. Root cause: the agent session was
  never modelled as a metered, usage-based resource, so the cost discipline (tenets 6/15) was
  never pointed at the tooling itself. Fix = control plane first (tenet 16). Detect-layer
  follow-up parked in BACKLOG (P2 `[finops]`).
- **Tenet 17 added — minimize operator cognitive load; act on reversible (two-way-door)
  decisions, deliberate only on one-way doors.** Bias for action bounded by reversibility:
  the agent just does + reports easily-reversible work (incl. **commit every session, never
  leave changes hanging**) and reserves the operator's attention for one-way doors (spend,
  lock-in, deletion, scope). In `tenets.md` + `AGENTS.md`.

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

- ✅ **`chandrav.dev` registered** at Cloudflare (2026-06-07, Active, 10-yr prepay).
- **Local tooling:** `docker` + `make` still not installed (Compose stack runs on
  VPS; optional locally). `terraform` v1.15.5 works.
- ✅ **All 5 secrets gathered** and transcribed into `terraform.tfvars` + `infra/.env`
  (both gitignored, on laptop + droplet).
- ✅ **"Verify at deploy" items resolved** (Mem0 image arch/tags, graph + psycopg deps,
  dashboard image) — see "Done this session #3" for what each turned into.
- **API not yet usable (auth on, no admin).** Auth is on by default (PR #4837); a fresh
  install has no admin/API key, so protected routes 401 (`/docs` is open → 200). Create
  an admin + API key (server `make bootstrap`/CLI on the droplet, or the setup wizard —
  but the wizard needs the dashboard, which is deferred). **Blocks a `POST /memories` test.**
- **Model config unverified.** The `MEM0_DEFAULT_LLM_MODEL`/`_EMBEDDER_MODEL` env vars are
  **not** in the server's documented env table — model selection is likely via the server
  config/wizard, not those vars. Confirm `gpt-5-mini` + `text-embedding-3-small` are
  actually in effect once an admin exists (Configuration page / `/configure`).
- **Deploy not yet fully reproducible.** A fresh `bootstrap.sh` would fail at
  `docker compose pull` (it can't pull the locally-built `mem0-api-server:local`, and the
  dashboard image 404s). The image was built by hand this session. Fold the
  clone-mem0-src + `docker build` step into `bootstrap.sh` (or push the image to GHCR) and
  update `setup.md` — see BACKLOG P1.
- **Cosmetic:** Compose prints `"wdqOTNUqJsh" variable is not set` (the bcrypt `$` in
  `BASIC_AUTH_HASH`). Harmless (Caddy gets the right hash via `env_file`); silence by
  escaping `$`→`$$` in `.env` if desired.
- **apex `chandrav.dev`** TLS didn't verify from a Windows client (subdomains fine);
  likely apex cert not yet provisioned. Low priority (apex is a placeholder).
- **Operator income change risk (end-June 2026).** Possibly between jobs soon →
  once deployed, recurring spend (**~₹3,800/mo landed**, ~₹2,920 list) must stay
  **pause-able**. The pause path (`decommission.md` §2 → `teardown.py`) drops the
  droplet (~₹2,600/mo landed) in one command. Factor into *deploy timing* (tenet 12 /
  `financial-decisions.md`).

## Environment notes

- Use `working_directory` param, not raw `cd` (Drive path has spaces/parens).
- Windows PowerShell 5.1 only; git push auth cached.
- Repos: `github.com/vvbch/ai-memory-infra(-private)`.

## Next action

> **RESUME HERE — stack is DEPLOYED & healthy over HTTPS. Make it *usable*, then commit.**

1. **Commit the deploy changes** (tenet 1/11 — don't batch): `infra/mem0-server.Dockerfile`
   (new), `infra/docker-compose.yml`, `docs/planning/BACKLOG.md`, `docs/planning/STATUS.md`.
   Run `check-repo-health` first. (`infra/.env` + `terraform.tfvars` stay gitignored.)
2. **Create an admin + API key** so the API is usable (auth is on; protected routes 401).
   On the droplet: try `cd /opt/mem0-src/server && make bootstrap` (PR #4837 generates a
   random admin password) or the server CLI; store the admin creds + API key in Bitwarden.
3. **Verify model config** — confirm `gpt-5-mini` (extraction) + `text-embedding-3-small`
   (embeddings) are actually in effect (the `MEM0_DEFAULT_*` env vars may be ignored; check
   the server's Configuration/`/configure`). Re-set via config if needed (ADR 013/011).
4. **Functional test:** `POST /memories` round-trip with the API key (the setup.md
   "Done when" gate), then `GET`/search to confirm it persisted.
5. **Make the deploy reproducible** (BACKLOG P1): fold the mem0-source build into
   `bootstrap.sh` (or push `mem0-api-server` to GHCR) so a clean `bootstrap.sh` works;
   update `setup.md` (Step 6 + prereqs) to match the from-source build. Currently a fresh
   bootstrap fails at `docker compose pull`.

**Connection details:** droplet `168.144.145.29` (SSH `root@`, key passphrase in
Bitwarden); API `https://memory.chandrav.dev` (`/docs` open); Neo4j browser
`https://graph.chandrav.dev` (basic-auth `admin` / pwd in Bitwarden). Stack:
`docker compose -f docker-compose.yml -f docker-compose.prod.yml …` in
`/opt/ai-memory-infra/infra`. Pause/stop the bill anytime: `scripts/teardown.py`
(income-change risk above). The mem0 source is cloned at `/opt/mem0-src` for rebuilds.
