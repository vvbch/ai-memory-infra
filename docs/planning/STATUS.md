# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). **Read this first to
> resume.** Full reasoning lives in `docs/decisions/` and the private
> `interview_packet.md`. Working model + teaching prefs: `AGENTS.md`.

**Last updated:** 2026-06-08 (round-trip session — **step 4 round-trip CLOSED; only the
Bitwarden custody gate remains**). The OpenAI embeddings 403 is fixed (operator set the
`ai-memory` project to "allow all models" — `text-embedding-3-small` → 200). Re-running the
round-trip then surfaced a **second, different blocker**: extraction to `gpt-5-mini` 400'd with
*"Unsupported parameter: 'max_tokens' … use 'max_completion_tokens'"* — a **bug in `mem0ai`
2.0.4**: `_is_reasoning_model()` lists `gpt-5o-mini` but not `gpt-5-mini`, so our model got sent
`max_tokens` (which every real GPT-5 model rejects) and extraction **silently** failed (`add`
returned `200` with 0 memories). **Fixed (ADR 021):** patch `_is_reasoning_model()` to treat the
whole `gpt-5*` family as reasoning models. Patched the **live container** (writable layer) to
prove it + baked the patch into `infra/mem0-server.Dockerfile` for rebuilds. **Round-trip now
verified end-to-end:** `POST /memories` extracted 2 facts (Python / Bangalore); `GET /memories`
+ `POST /search` returned them (user_id `diag-roundtrip-20260608`). **Caveat:** the live
container's in-place patch survives restart/reboot but **not** a `compose up --force-recreate`;
the image must be rebuilt from the Dockerfile before the next redeploy (BACKLOG P1). **Only open
step-1–4 item: confirm `ADMIN_API_KEY` is in Bitwarden (custody gate) — needs the operator.**)

**Prior update:** 2026-06-08 (control-plane session — **tenet 16: stateless, disposable
sessions**. Codified after a long-lived Cursor session burned a month's $60 plan credits in
half a day (context-window amplification, COE 2026-06-08): one task per chat, checkpoint
`STATUS.md` per step, end every response with a Resume prompt.)

**Earlier update:** 2026-06-07 (session-resume #3 — **PHASE 1 DEPLOYED**. `tf-apply`
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
1. ✅ **Save our work to GitHub** — DONE (was already committed + pushed in prior
   session: `3d1db74` infra + `b6ffa2d` docs; both repos clean, `0 ahead/0 behind`).
2. ✅ **Create a login for the API** — DONE. The admin API key was already generated
   into the server's `.env` at deploy time; verified working this session (a protected
   route returns 401 with no key, **200 with the `X-API-Key` header**). Still TODO:
   confirm the key is saved in Bitwarden (custody gate).
3. ✅ **Test it** — DONE. Added a test memory, read it back, searched it — **it stuck.**
   This took two fixes: (a) your OpenAI "allow all models" change cleared the embeddings
   error; (b) we then hit a *separate* bug in the memory software (it sent OpenAI an old
   setting name that the new `gpt-5-mini` model rejects) — fixed it (ADR 021). The server
   now correctly saved "favorite language = Python" and "lives in Bangalore" and found them
   on search. **One small chore left: confirm your master API key is saved in Bitwarden**
   (see "How to do the Bitwarden check" below — this is the only thing left from steps 1–4).
4. **Make reinstall repeatable** — if we had to rebuild the server from scratch today,
   the install script would need a manual fix (we built the app image by hand this
   session, and the `gpt-5-mini` bug-fix patch must be rebuilt into the image before the
   next redeploy). Parked in BACKLOG P1.

**How to do the Bitwarden check (the only thing left from steps 1–4):** the master API
key (`ADMIN_API_KEY`) lives safely on the server, but per our custody rule (ADR 017) it must
*also* be in your password vault so it's never lost. To confirm it's there:
1. Open Bitwarden (app or [vault.bitwarden.com](https://vault.bitwarden.com)) and unlock.
2. Open the **`ai-memory-infra`** folder.
3. Look for an item named like **"ADMIN_API_KEY"** / **"mem0 admin key"** with a 43-character
   value. If it exists → done, nothing more to do.
4. If it's **missing**: in the next chat, ask the agent to read it from the server `.env` and
   show it **once** so you can paste it into a new Bitwarden login item in that folder (the
   agent never stores secrets in chat history beyond that one-time display).

**How to talk to the next agent:** paste the line in the box below into a **new chat**.
Ask for **concierge mode** (one step at a time, plain English, no jargon).

```
Resume ai-memory-infra — read STATUS.md (Plain English section) and AGENTS.md, run repo-health, then Next action step 5: make the deploy reproducible (BACKLOG P1) — rebuild the mem0 image from infra/mem0-server.Dockerfile (now carries the ADR 021 gpt-5-mini patch) on the droplet so a clean bootstrap.sh works, and fold the from-source build into bootstrap.sh; update setup.md. Concierge mode, one step at a time, plain English. Context: steps 1–4 DONE — the POST /memories round-trip persists end-to-end (user_id diag-roundtrip-20260608; verified via GET + /search). Two blockers were cleared: OpenAI embeddings 403 (operator set project to "allow all models") and a mem0ai 2.0.4 bug where gpt-5-mini was sent max_tokens (ADR 021 — patched live container + Dockerfile). CAVEAT: the live container's patch is in its writable layer only; it survives restart/reboot but a `compose up --force-recreate`/redeploy from the un-rebuilt image reverts the bug — rebuild the image first. ADR 020 (make bootstrap = locked dead end) still stands. If the ADMIN_API_KEY-in-Bitwarden custody gate is still open, close it first. SSH key is in ssh-agent; secrets read from server .env, never printed.
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
- **Committed + pushed** (2026-06-08, no longer pending): `infra/mem0-server.Dockerfile`
  (new) + `infra/docker-compose.yml` in `3d1db74`; `docs/planning/BACKLOG.md` +
  `docs/planning/STATUS.md` in `b6ffa2d`. (`infra/.env` + `terraform.tfvars` stay gitignored.)

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

## Last decisions (2026-06-08, round-trip session)

- **ADR 021 — patch mem0ai's GPT-5 detection so `gpt-5-mini` extraction works.** mem0ai 2.0.4's
  `_is_reasoning_model()` lists `gpt-5o-mini` but not `gpt-5-mini`, so our model was sent
  `max_tokens` (rejected by every real GPT-5 model → 400), and `add` silently stored 0 memories.
  Patched `_is_reasoning_model()` to cover the `gpt-5*` family (drops the unsupported params);
  applied to the live container + baked into `infra/mem0-server.Dockerfile` (idempotent, with a
  build-time `assert` so a future mem0 restructure fails loudly instead of no-op'ing). Kept
  `gpt-5-mini` (ADR 013 unchanged) — this is an upstream-bug patch, not a model change.
  **Control-plane debt:** the live container's patch is writable-layer-only; rebuild the image
  from the Dockerfile before the next redeploy (BACKLOG P1).

## Last decisions (2026-06-08, usable-API session)

- **ADR 020 — built-in `ADMIN_API_KEY`, not `make bootstrap` (LOCKED).** Verified against
  the mem0 source/docs that `make bootstrap` runs mem0's *own* bundled compose (its own
  Postgres + stack); on our custom stack it would stand up a **second, conflicting DB
  stack** (tenets 7/4). The droplet `.env` already had a working 43-char `ADMIN_API_KEY`
  (`X-API-Key` → 200, no key → 401). Dashboard + `/setup` wizard + per-user `m0sk_` keys
  remain additive, reversible options (BACKLOG P2). **Decision is locked — do not
  re-litigate `make bootstrap` in future sessions.** Stale BACKLOG entry removed.

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
- ✅ **API is now usable (admin API key works).** Auth is on (`AUTH_DISABLED=false`,
  PR #4837). The legacy `ADMIN_API_KEY` (43-char, in the droplet `.env`) was generated at
  deploy time; verified 2026-06-08: `GET /memories?user_id=diag` → **401 without** the key,
  **200 with** `X-API-Key`. No `make bootstrap` / dashboard needed (tenet 7 — fewer moving
  parts). Per-user `m0sk_` keys + the `/setup` wizard remain available if we add the
  dashboard later. **Custody TODO:** confirm `ADMIN_API_KEY` is stored in Bitwarden.
- ✅ **Step-4 round-trip DONE — persists end-to-end** (2026-06-08). Cleared **two** blockers:
  **(1) OpenAI embeddings 403** — the project `ai-memory` (`proj_BBdR6RuERcssScuTgCBjCnht`)
  was restricted to only `gpt-5-mini`; operator set it to **"Allow all models"** →
  `text-embedding-3-small` now 200 (verified directly on the droplet). **(2) mem0ai 2.0.4
  `gpt-5-mini` bug** — extraction 400'd (`max_tokens` unsupported on GPT-5; needs
  `max_completion_tokens`) because `_is_reasoning_model()` omits `gpt-5-mini`; `add` returned
  `200` with **0 memories** (silent). Fixed by patching `_is_reasoning_model()` to cover the
  `gpt-5*` family (**ADR 021**) — applied to the live container (writable layer) + baked into
  `infra/mem0-server.Dockerfile`. **Verified:** `POST /memories` (user_id
  `diag-roundtrip-20260608`) extracted 2 facts (Python / Bangalore, event `ADD`); `GET
  /memories?user_id=…` + `POST /search "favorite programming language"` returned them ranked.
  **⚠️ Caveat (control-plane debt):** the live patch is in the container's writable layer — it
  survives `docker restart` + droplet reboot but **not** a `compose up --force-recreate` /
  redeploy from the un-rebuilt image. **Rebuild the image from the patched Dockerfile before
  the next redeploy** (BACKLOG P1). **Remaining step-1–4 item: the Bitwarden custody gate.**
- ✅ **Model config VERIFIED (2026-06-08, step 3).** Earlier note was **wrong** — the
  server source *does* read these env vars: `main.py` L115-116 `DEFAULT_LLM_MODEL =
  os.environ.get("MEM0_DEFAULT_LLM_MODEL", "gpt-4.1-nano-2025-04-14")` /
  `DEFAULT_EMBEDDER_MODEL = ...get("MEM0_DEFAULT_EMBEDDER_MODEL", "text-embedding-3-small")`,
  which feed `DEFAULT_CONFIG` → `Memory.from_config()` at boot (`server_state.initialize_state`).
  Live container `printenv` confirms **`gpt-5-mini`** + **`text-embedding-3-small`** in effect
  (matches ADR 013/011). **Latent risk (control plane):** the LLM *fallback* is
  `gpt-4.1-nano`, so if `MEM0_DEFAULT_LLM_MODEL` were ever unset the server would silently
  run nano — `.env.example` already pins it; keep it set. No `/configure` GET route; config
  is boot-time only (no persisted override; ADR 020 = no dashboard/wizard).
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

> **RESUME HERE — stack is DEPLOYED & healthy over HTTPS. Make it *usable*.**

1. ✅ **Commit the deploy changes** — DONE (prior session: `3d1db74` infra + `b6ffa2d`
   docs; repo-health green, both repos `0 ahead/0 behind`). No pending changes.
2. ✅ **Create an admin + API key** — DONE (2026-06-08). The `ADMIN_API_KEY` was already in
   the droplet `.env` (legacy admin mode, tenet 7 — no `make bootstrap`/dashboard needed);
   verified working (`X-API-Key` → 200, no key → 401). **Custody TODO:** confirm the key is
   in Bitwarden. **`make bootstrap` is a locked dead end (ADR 020)** — it would spin up mem0's
   *own* conflicting compose/DB stack; our stack runs from `/opt/ai-memory-infra/infra`. Do
   not revisit.
3. ✅ **Verify model config** — DONE (2026-06-08). Live container runs `gpt-5-mini` +
   `text-embedding-3-small`; `main.py` *does* read `MEM0_DEFAULT_*` (earlier note corrected).
   See the model-config blocker entry above for the source lines + the `gpt-4.1-nano` fallback
   risk.
4. ✅ **`POST /memories` round-trip — DONE (2026-06-08), persists end-to-end.** Both blockers
   cleared (OpenAI "allow all models"; mem0ai gpt-5-mini patch, ADR 021). Verified on the
   droplet: `POST /memories` (user_id `diag-roundtrip-20260608`) extracted 2 facts → `GET
   /memories?user_id=…` + `POST /search` returned them (setup.md "Done when" met). **Only open
   item from steps 1–4: the custody gate** — confirm `ADMIN_API_KEY` is saved in Bitwarden
   (`ai-memory-infra` folder). Operator-only (agent can't reach the vault); guide click-by-click.
5. **← NEXT — Make the deploy reproducible** (BACKLOG P1): the live container's ADR-021 patch is
   in its writable layer only, so a redeploy from the un-rebuilt image reverts the gpt-5-mini
   bug. **Rebuild `mem0-api-server:local` from the patched `infra/mem0-server.Dockerfile`** on
   the droplet, then fold the clone-mem0-src + `docker build` step into `bootstrap.sh` (or push
   the image to GHCR) so a clean `bootstrap.sh` works; update `setup.md` (Step 6 + prereqs).
   Currently a fresh bootstrap fails at `docker compose pull`.

**Connection details:** droplet `168.144.145.29` (SSH `root@`, key passphrase in
Bitwarden); API `https://memory.chandrav.dev` (`/docs` open); Neo4j browser
`https://graph.chandrav.dev` (basic-auth `admin` / pwd in Bitwarden). Stack:
`docker compose -f docker-compose.yml -f docker-compose.prod.yml …` in
`/opt/ai-memory-infra/infra`. Pause/stop the bill anytime: `scripts/teardown.py`
(income-change risk above). The mem0 source is cloned at `/opt/mem0-src` for rebuilds.
