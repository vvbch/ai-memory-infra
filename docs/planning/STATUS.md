# STATUS — resumable session snapshot

> Overwritten each session (tenet 1 / Definition of Done). **Read this first to
> resume.** Full reasoning lives in `docs/decisions/` and the private
> `interview_packet.md`. Working model + teaching prefs: `AGENTS.md`.

**Last updated:** 2026-06-08 (**Phase 3 — session 15: completion gate corrected;
commit+push required at handoff**). Phase 2 is closed; Phase 3 browser reach is active. Session 8 created
private GitHub repo **`vvbch/ai-memory-extension`**, imported the upstream
MIT `mem0ai/mem0-chrome-extension` history, installed Node.js LTS on Windows, verified the raw
upstream build, then rewrote the extension in commit **`7ac3011`**: default server
`https://memory.chandrav.dev`; local popup settings for server URL + API key + user id; `X-API-Key`
helper; `/memories` + `/search` paths; mem0 cloud login/session-scraper removed; mem0 cloud host
permissions removed; PostHog/mem0 extension telemetry no-op/removed. Verification: OpenAPI fetched
from live server and confirmed `/memories`, `/search`, and `X-API-Key`; repo search shows **no
`api.mem0.ai`, `app.mem0.ai`, PostHog, or live `Authorization` headers**; `npm run type-check` green;
`npm run build` green. npm reported **11 inherited audit findings** (4 moderate, 7 high);
`lint:check` / `format:check` still fail on upstream-wide Prettier/CRLF noise, including untouched
files, so not fixed in this rewrite. Session 9: operator loaded `ai-memory-extension/dist` as an
unpacked Chrome extension and confirmed **OpenMemory** appears on `chrome://extensions`. The previous
operator prompt was stale/ambiguous, so Chrome's current "Load unpacked" flow was web-verified and the
control plane was updated: `AGENTS.md` + `docs/tenets.md` now require current-doc/live-UI verification
for volatile console/browser prompts, and the extension README now says to select the `dist` folder
itself, the folder containing `manifest.json`. Session 10: after API-key entry, the sidebar showed
**Error loading memories**; fixed `src/sidebar.ts` to fetch `GET /memories?user_id=...` using the same
stored `serverUrl`, `apiKey`, and `userId` helper path as the popup/content scripts, to reject non-2xx
responses clearly, and to tolerate both array and `{ results, count }` response shapes. Verification:
`npm run type-check` green; `npm run build` green. Session 11: operator reloaded the unpacked extension
in Chrome, but the browser still displayed errors on `https://chatgpt.com/`: **`Error fetching
memories: TypeError: Failed to fetch`** at `assets/sidebar.ts-CSsZSEPr.js:126`, plus **`Unchecked
runtime.lastError: Cannot create item with duplicate id mem0.saveSelection`**. **Next: start a fresh
debug session; inspect the extension runtime/service-worker/content-script errors, verify whether the
fetch failure is CORS/host-permission/service-worker-context related, and make context-menu creation
idempotent.** Session 12: root cause verified against Chrome docs — content scripts inherit the page
origin and cannot directly bypass CORS, even with extension host permissions; extension pages/service
workers can fetch permitted hosts. Implemented a small background API relay for `/memories` and
`/search`, switched the sidebar Recent Memories fetch and ChatGPT content-script search/save calls to
use it, and made `mem0.saveSelection` context-menu creation remove/recreate idempotently on reload.
Verification: `npm run type-check` green; `npm run build` green; `dist/` regenerated. **Next:
operator reloads the unpacked extension
in Chrome and tests the ChatGPT sidebar; if it still fails, inspect the extension service-worker
console and page console for the new background-relay error.** Session 13: operator corrected the
agent working model after root/context drift. Updated `AGENTS.md` to make explicit that the parent
`ai-memory` workspace is the operating surface, `ai-memory-infra` is the control plane for all three
sibling repos, package repos are targeted data-plane workspaces only, and reversible completed work
items must be committed and pushed to remote in the same session. Session 14: ran repo-health green
for `ai-memory-infra` + `ai-memory-infra-private`; reloaded the real unpacked OpenMemory extension in
Chrome (`jdajdehjpohgmolnlijiiggfbolmenmo`, loaded from `ai-memory-extension/dist`); opened
`https://chatgpt.com/`; the OpenMemory sidebar rendered successfully and loaded live Recent Memories:
**Total Memories = 1**, with a memory card plus Copy/View actions. The prior `TypeError: Failed to
fetch` sidebar failure did **not** reproduce in the visible sidebar path, and the duplicate
context-menu reload failure did not block extension startup. **Next:** continue Phase 3 browser
verification by proving ChatGPT-side save/search behavior against the live server, then update docs
and close the extension browser-reach milestone. Session 15: operator caught that session 14 ended
without committing/pushing, violating the repo's completion gate and atomic-session handoff model.
Sharpened `AGENTS.md`: reading `AGENTS.md`/`STATUS.md` and continuing the next action is the standing
operator authorization to commit+push reversible completed work in this repo; do not wait for a second
commit prompt unless blocked, one-way-door, secret, destructive, or explicitly paused.

**Prior update:** 2026-06-08 (**Phase 2 automation — session 6: drill dead-man's-switch
WIRED & VERIFIED GREEN → Phase 2 COMPLETE**). Closed the final operator step. Walked the
operator click-by-click to create the **drill's own (second) healthchecks.io check** ("ai-memory
restore drill", cron `30 19 1 * *` UTC = 01:00 IST on the 1st, **2 h grace**, email notification
on), saved its ping URL in Bitwarden (ADR 017), then **appended `DRILL_HEALTHCHECK_URL=…` to the
droplet `/opt/ai-memory-infra/infra/.env`** cleanly (verified with `cat -A` — line ends at `$`,
**no trailing CR**; the readers `tr -d '\r'` anyway). **Verified end-to-end (tenet 17):** ran
`bash scripts/restore-drill.sh` on the droplet → **DRILL PASSED** (`20260608T151504Z`; scratch
Postgres canary+embedding restored, 257.8 MB Neo4j dump loaded clean, mem0 history valid SQLite,
scratch torn down) → its success ping fired → **operator confirmed the check went green**. Droplet
was already at GitHub truth (clean tree, `0 ahead / 0 behind` — session-5's `restore-drill.sh` +
drill units were already committed + pulled), so no reset was needed. **Phase 2 DoD now FULLY MET
— no operator steps remain. Next: Phase 3 (Chrome extension fork).**

**Prior update:** 2026-06-08 (**Phase 2 automation — session 5: ADR 023 §4 restore DRILL
DONE & VERIFIED → Phase 2 COMPLETE bar one operator console step**). Built a **monthly,
lightweight, isolated restore drill** that proves the restore path still works **without
touching live data**: new `scripts/restore-drill.sh` restores the latest backup into
**throwaway scratch containers/volumes** (a scratch `pgvector` container + a throwaway Neo4j
volume), asserts a **permanent canary memory** (`user_id=drill-canary`, planted by the new
committed `scripts/plant-drill-canary.sh`) round-trips **with its pgvector embedding intact**,
confirms the Neo4j dump `neo4j-admin load`s clean and the mem0 history is a valid SQLite file,
then tears all scratch down (EXIT trap). Wired three `systemd` units (monthly
`OnCalendar=*-*-01 19:30 UTC` = 01:00 IST, an hour after the nightly backup so they never
overlap; `Persistent=true`; `OnFailure` journal marker) + a **separate** drill dead-man's-switch
(`DRILL_HEALTHCHECK_URL`, no-op until set); `bootstrap.sh` installs/enables them. **Verified
on the droplet (tenet 17):** planted canary → fresh backup (`Result=success`) → ran the drill
→ **DRILL PASSED** (scratch `total=6, canary-with-embedding=2`; 258 MB Neo4j dump loaded clean;
mem0 history valid SQLite), scratch fully cleaned up, **live stack untouched** (mem0 up 9 h,
~2.3 GB free). Why lightweight not a full scratch-stack `/search`: the 4 GB box has no headroom
for a second full stack without risking live. **ADR 023 §4 + setup.md updated; the drill
verifies the part that rots — backup artifacts restoring into working data.** **Phase-2 DoD now
MET** (backups scheduled + self-monitoring + delete-resistant + pre-snapshot + drill exists).
**ONE operator step remains:** create a 2nd healthchecks.io check for the drill + paste its URL
as `DRILL_HEALTHCHECK_URL`. **Next: that console step, then Phase 3 (Chrome extension).**

**Prior update:** 2026-06-08 (**Phase 2 automation — session 4: ADR 023 §3(b) least-privilege
backup key DONE & VERIFIED**). Created a **bucket-scoped DO Spaces "Limited Access" key**
(`ai-memory-backup-only`, scoped to `ai-memory-infra-backups-chandrav`, R/W/D — DO has no
write-without-delete tier) via the console (operator click-step), stored it in Bitwarden (ADR 017,
custody closed), and **swapped it into the droplet `infra/.env`** in place of the broad "All
buckets/All permissions" key. **Verified before retiring (tenet 17):** ran the backup through the
exact nightly path (`systemctl start ai-memory-backup.service`) → first attempt **403
InvalidAccessKeyId** (the swap had injected CR junk — the cross-shell quoting trap; `tr -d "\r\n"`
mangled through PowerShell→ssh→bash so the value carried a trailing `\r`); **repaired on-server**
with bash ANSI-C `${raw%%$'\r'*}` truncation (no fragile escaping), re-ran → **Result=success,
ExecMainStatus=0, all 4 artifacts uploaded**. The old broad key is **no longer on the droplet**
(retained locally only — the limited key *can't* change bucket config, so lifecycle/versioning stays
under the full Terraform key, which is correct). Shredded the temp `.env.bak.*` files (held the old
key in plaintext) once verified. **§3 (a)+(b)+(c) all DONE. Next: §4 restore drill, then Phase 3
(Chrome extension).**

**Prior update:** 2026-06-08 (**Phase 2 automation — session 3: ADR 023 §3 data-loss hardening
DONE + Windows→Linux CRLF bug fixed for good**). **(1) Portability fix (committed `9344466`):** the
recurring Windows→Linux pain wasn't git (`.gitattributes` already pins `.sh` to LF) — it was *runtime*
CR injection when appending to the droplet `.env` from PowerShell over SSH (trailing `\r` → broke the
heartbeat URL last session). Fixed once and for all: `backup.sh`/`restore.sh` `.env` readers now pipe
through `tr -d '\r'`, so a CRLF `.env` line can't corrupt a value — no more manual `sed -i 's/\r$//'`
(verified with a CRLF fixture; `bash -n` clean). **(2) ADR 023 §3 (operator-approved retention: keep
30 d, recoverable 14 d):** web-verified DO Spaces facts first (versioning ✅, lifecycle ✅, Object-Lock/
WORM ❌, key scopes = Read/RWD/All only). Built via Terraform: versioning confirmed **already live**
(refresh-plan = no change) + added two lifecycle rules (expire current @30 d, noncurrent @14 d, sweep
delete-markers, abort incomplete MPU @1 d); `terraform apply` = 1 changed, re-plan = **converged**.
**Removed the client-side `s3cmd del` prune** from `backup.sh` (the backup path no longer deletes
anything → a compromised box can't wipe history; retention is now declarative server-side). **Added a
pre-restore safety snapshot** to `restore.sh` (backs up current state before overwriting; `SKIP_PRESNAPSHOT=1`
escape hatch; a failed snapshot aborts). ADR 023 + `setup.md` updated. **Still open in §3: (b)
least-privilege bucket-scoped backup key — needs an operator console step (next).** **§4 restore drill
not started.** **Next: §3(b) key, then §4 drill, then Phase 3 (Chrome extension).**

**Prior update:** 2026-06-08 (**Phase 2 automation — implementation session 2: DEPLOYED & GREEN**).
Brought the droplet to GitHub truth (`git reset --hard origin/main` → `c4f31b8`; **verified first**
that the droplet's only un-committed live edits to `backup.sh`/`restore.sh`/`docker-compose.yml` were
already represented in `origin/main`, so nothing live-only was lost — tenet 11), then **deployed +
switched on the nightly backup**: installed the three `systemd` units to `/etc/systemd/system/`,
`systemctl enable --now ai-memory-backup.timer` (**enabled + active; next run 18:32 UTC ≈ 00:02 IST**,
`Persistent=true` catch-up), added `HEALTHCHECK_URL` to the droplet `infra/.env`, and **ran two
on-demand backups via the service** (`Result=success`, ExecMainStatus 0; all four artifacts uploaded
to `s3://…/backups/<UTC>/`, newest-7 prune ran). **Dead-man's-switch CONFIRMED GREEN:** healthchecks.io
returned **HTTP 200 `OK`** to the success ping. **Gotcha found + fixed:** the *first* run's heartbeat
errored `curl: (3) URL rejected: Malformed input to a URL function` — appending the URL line to the
Linux `.env` *from Windows* left a trailing `\r`; fixed with `sed -i 's/\r$//' .env` and re-verified
(see Environment notes — always strip CR when appending to the droplet `.env` from PowerShell). **ADR
023 §1 (daily timer) + §2 (heartbeat monitor) are now DONE & LIVE on the droplet.** Remaining for
Phase 2: **§3 data-loss hardening** (⚠ one-way-door class — tenet 17 needs operator sign-off, and
web-verify DO Spaces versioning/lifecycle FIRST) + **§4 restore drill**. **Next: ADR 023 §3 → §4, then
Phase 3 (Chrome extension).**

**Prior update:** 2026-06-08 (**Phase 2 automation — implementation session 1**). Built the
*reversible half* of ADR 023 and picked the monitor. **(1) Daily backup schedule DONE (in
repo):** versioned `systemd` units — `infra/systemd/ai-memory-backup.service` (oneshot →
`backup.sh`), `…backup.timer` (18:30 UTC = midnight IST, `Persistent=true` catch-up if the
box was paused), and `…backup-failure.service` (local `OnFailure` journal marker) — installed
by `bootstrap.sh`. **(2) Monitoring vendor CHOSEN = healthchecks.io** (free Hobbyist tier,
open-source/self-hostable = no lock-in; web-verified vs cron-job.org + DO Uptime, tenet 8).
Wired the dead-man's-switch into `backup.sh` (pings `/start`, success on completion, `/fail`
on error via the EXIT trap; optional `HEALTHCHECK_URL`, no-op if unset). Operator created the
check (cron `30 18 * * *` UTC, 1 h grace) + saved the ping URL to Bitwarden; `HEALTHCHECK_URL`
staged in local gitignored `.env`. **NOT yet deployed to the droplet.** **(3) data-loss
hardening + (4) restore drill = NOT started** (next session). **Control-plane fix:** the
Resume prompt was bloating into a second copy of STATUS (token cost every prompt — the COE
2026-06-08 failure mode; drift, tenet 10) → **slimmed it to a pure pointer** (tenet 16, same
discipline ADR 018 applies to editor pointer files); caveats now live in this file, not the
prompt. `bash -n` clean on all touched scripts; repo-health green. **Next: deploy the timer +
heartbeat to the droplet & confirm a real ping, then ADR 023 §3 (data-loss hardening) + §4
(drill).**

**Prior update:** 2026-06-08 (**backup-strategy review** — decisions-only session). Reviewed the
backup/restore strategy with the operator. Two outcomes: **(1) control-plane fix** — sharpened
**tenet 17** so a decision is classified by the irreversibility of its *effect on data*, not of
the code (destructive restore / delete-on-prune / TTL are one-way doors needing sign-off even
when the script reverts trivially); **(2) Phase 2 re-scoped** — automating backups + adding a
restore drill is pulled *into* Phase 2 (not "done" until backups are scheduled, self-monitoring,
and drilled). Locked the automation + data-loss-hardening design in **ADR 023** (daily systemd
timer; dead-man's-switch alerting w/ vendor = an open operator pick; server-side lifecycle/
versioning instead of client-side delete-prune; least-privilege backup key; pre-restore safety
snapshot; recurring drill). **Implementation deferred to the next session (tenet 16).** No code
changed this session; tenets.md + AGENTS.md (tenet 17), ADR 023, BACKLOG (promoted), STATUS
updated. **Next: implement Phase 2 automation (ADR 023), THEN Phase 3.**

**Prior update:** 2026-06-08 (Phase 2 — backup/restore session — **scripts DONE; restore round-trip
PROVEN**). Fleshed out `scripts/backup.sh` + `scripts/restore.sh` (were empty scaffolding) and
**stood up + verified the full backup/restore path** to the Spaces bucket
(`ai-memory-infra-backups-chandrav`, sgp1). **Backup** = `pg_dump -Fc` (Postgres, online) + `tar`
of the mem0 SQLite history volume (online) + an **offline** `neo4j-admin database dump` (Community
can't dump a running DB → brief ~20–30 s `stop`/`start`; only the graph pauses, API stays up),
uploaded as `postgres.dump` + `neo4j.dump` + `mem0-history.tar.gz` + a SHA-256 `MANIFEST.txt` under
one timestamped prefix, self-pruned to the newest 7. **Restore** verifies checksums, asks for a
typed `RESTORE` (`FORCE=1` skips), then `pg_restore --clean` + wipe/untar SQLite + offline neo4j
`load --overwrite`. **Tooling:** `s3cmd` (apt, S3-compatible Spaces); creds (`SPACES_*` +
`BACKUP_BUCKET`) added to the droplet `infra/.env` (read from local `terraform.tfvars`, never
printed) + `.env.example`. **PROVEN round-trip:** wrote a known memory (codeword `ZEPHYR-7731`,
user `backup-proof-20260608`) → backed up → **deleted** it (`GET` → `[]`) → `restore.sh latest` →
the **exact record returned** (same id/timestamp/hash) and a semantic `/search` ranked it (so the
**pgvector embeddings** restored, not just rows). Cleaned up the test memory + took a final clean
backup. **ADR 022** written; `setup.md` Phase-2 section + BACKLOG (cron/restore-drill = P2) updated.
**Next: Phase 3 — Chrome extension fork.**

**Prior update:** 2026-06-08 (P1-security session — **secret-scan gate DONE; `.env`-strip
consciously DEFERRED to a post-burn-in cleanup pass**). Added **gitleaks v8.30.1** as a second
pre-commit gate (after the Tenet-11 repo-health gate) in `scripts/hooks/pre-commit`: it runs
`gitleaks git --staged` against a versioned `.gitleaks.toml` and **blocks the commit** on any
finding (or if gitleaks is missing — a silent no-op would defeat the gate). `install-hooks.ps1`
now also **ensures gitleaks is installed** (winget). **Tested both ways:** a staged fake AWS key
was blocked (exit 1); the real changeset passed ("no leaks found"). So "no secrets in git" is now
a deterministic gate. **The plaintext secrets comment block in `infra/.env` was NOT stripped this
session** — the operator is keeping the admin-UI login note handy through ~1 week of real usage;
it's parked in BACKLOG with a trigger (~2026-06-15) under the new **tenet 18 (burn-in before
hardening)**. Safe to hold: `.env` is gitignored *and* the new gitleaks gate stops it ever
reaching git (the active risk — secrets in history — is closed). **Added tenet 18** to
`tenets.md` + the `AGENTS.md` summary.

**Prior update:** 2026-06-08 (reproducible-deploy session — **step 5 DONE; Phase 1 fully
reproducible**). Rebuilt `mem0-api-server:local` on the droplet from the patched
`infra/mem0-server.Dockerfile` (ADR 021 baked in, build-time `assert` passed), then
**`compose up --force-recreate`'d mem0 and re-ran the round-trip** (user_id
`diag-rebuild-20260608`): `POST /memories` extracted 2 facts → `GET` + `/search` returned them
ranked — proving the redeploy no longer reverts the gpt-5-mini bug (the live patch is now in the
*image*, not just the writable layer). **Folded the from-source build into `scripts/bootstrap.sh`**
(clones pinned `MEM0_REF`, `docker build`s the image, pulls only external base images) and
**updated `docs/setup.md`**. A clean `bootstrap.sh` works end-to-end (`bash -n` clean; build
verified on the droplet). **Earlier (prior chat):** the OpenAI embeddings 403 is
fixed (operator set the
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
the image must be rebuilt from the Dockerfile before the next redeploy (BACKLOG P1). **Custody
gate CLOSED:** `ADMIN_API_KEY` (43-char) copied from the droplet `.env` → operator's clipboard
(never shown in chat) → saved to Bitwarden `ai-memory-infra` as "ADMIN_API_KEY (mem0)".
**Steps 1–4 are all DONE; next is step 5 (reproducible deploy, BACKLOG P1).**)

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
   route returns 401 with no key, **200 with the `X-API-Key` header**). ✅ Custody gate now
   closed too — the key is saved in Bitwarden (2026-06-08).
3. ✅ **Test it** — DONE. Added a test memory, read it back, searched it — **it stuck.**
   This took two fixes: (a) your OpenAI "allow all models" change cleared the embeddings
   error; (b) we then hit a *separate* bug in the memory software (it sent OpenAI an old
   setting name that the new `gpt-5-mini` model rejects) — fixed it (ADR 021). The server
   now correctly saved "favorite language = Python" and "lives in Bangalore" and found them
   on search. ✅ **And your master API key is now saved in Bitwarden** (custody gate closed —
   copied server→clipboard→vault, never shown in chat). **Steps 1–4 are all done.**
4. ✅ **Make reinstall repeatable** — DONE (2026-06-08). The install script
   (`bootstrap.sh`) now builds the app image from source automatically (it used to need a
   manual by-hand build), and the `gpt-5-mini` bug-fix is permanently baked into the image —
   we proved a from-scratch-style redeploy keeps it (rebuilt the image + recreated the
   container + the memory test still stuck). So a clean reinstall just works now.
5. ✅ **Lock the door on accidental secret leaks** — DONE (2026-06-08). Added an automatic
   "secret scanner" (gitleaks) that runs every time we save work to git: if a password or key
   ever sneaks into a file we're about to commit, the save is **blocked** before it can reach
   GitHub. Tested it — it caught a planted fake key and stopped the commit, and let a clean
   one through. So "no secrets in git" is now enforced by a machine, not just a rule we try to
   remember.
6. ⏸️ **Tidy the leftover password note in the config file** — ON PURPOSE, LATER. There's a
plaintext note (the admin login for the graph/dashboard pages) sitting in the server's
config file. It's already safe in Bitwarden, but you asked to keep it handy for ~a week of
real use before we delete it. It's parked with a reminder (~Jun 15) and it's safe to leave:
that config file never goes to git, and the new scanner above would block it anyway. This is
the new "burn-in, then clean up" rule (tenet 18).
7. 🔄 **Set up backups + prove we can get your memories back** — backup/restore WRITTEN & PROVEN,
   automation NOW IN PROGRESS (2026-06-08). The server has a one-command **backup** that copies all
   three places your data lives (the memory database, the knowledge graph, and the edit-history
   file) into the cloud backup bucket, and a one-command **restore** that pulls them back. We
   **proved** it: saved a test memory (a codeword), backed up, **deleted** it, ran restore, and the
   codeword came back exactly — and search found it again. **What changed this session:** we started
   *building* the automation. **(a)** The nightly **auto-backup schedule is written** — the server
   will run the backup itself every night at midnight (India time), and if it happens to be switched
   off at that hour it runs the missed one as soon as it's back. **(b)** We picked the **watchdog**:
   a free service (healthchecks.io) that expects a nightly "backup OK" ping and **emails you if it
   ever goes silent** — the only way to catch a *dead* server (a dead box can't email you itself).
   You created the check and saved its link in Bitwarden; I wired the server to ping it. **✅ NOW LIVE
   (2026-06-08):** the nightly auto-backup is switched on on the *real* server (first run tonight ~00:02
   IST), and we watched a real "backup OK" ping land — **healthchecks.io went green (HTTP 200)**. So the
   watchdog is now actually watching. **✅ NOW DONE TOO (2026-06-08):** the backup storage is now
   **resistant to accidental deletion** — the cloud bucket keeps old versions and auto-expires them on
   a 30-day / 14-day schedule (server-side, so a hacked server can't wipe history), and the server now
   uses a **narrow "backup-only" key** that can reach *only* the backup bucket and nothing else in your
   cloud account (we created it, saved it in Bitwarden, swapped it in, and watched a real backup
   succeed on it). **✅ NOW DONE TOO (2026-06-08):** the regular *practice* restore (a "drill") is
   built and **passed for real**. Once a month the server quietly restores the latest backup into a
   **disposable scratch copy** (never your live data), checks that a planted "canary" memory comes
   back **with its search-vector intact**, that the knowledge-graph file reloads cleanly, and that the
   edit-history file is a valid database — then throws the scratch copy away. We ran it end-to-end and
   it passed. So we now *know* the recover-button keeps working, not just hope so. **✅ NOW DONE TOO
   (2026-06-08):** the monthly drill has its **own second watchdog** — we created a second free
   healthchecks.io check, wired the server to ping it, ran a real drill, and **watched the check go
   green**. So you'll now get **emailed if a monthly drill ever fails or stops running**, exactly like
   the nightly backup. **Phase 2 is now fully closed — nothing left for you to do here. Next we move to
   Phase 3 — the Chrome browser extension.**

**How to do the Bitwarden check (✅ DONE 2026-06-08 — kept for reference):** the master API
key (`ADMIN_API_KEY`) lives safely on the server, but per our custody rule (ADR 017) it must
*also* be in your password vault so it's never lost. To confirm it's there:
1. Open Bitwarden (app or [vault.bitwarden.com](https://vault.bitwarden.com)) and unlock.
2. Open the **`ai-memory-infra`** folder.
3. Look for an item named like **"ADMIN_API_KEY"** / **"mem0 admin key"** with a 43-character
   value. If it exists → done, nothing more to do.
4. If it's **missing**: in the next chat, ask the agent to read it from the server `.env` and
   show it **once** so you can paste it into a new Bitwarden login item in that folder (the
   agent never stores secrets in chat history beyond that one-time display).

**How to talk to the next agent:** paste the line below into a **new chat** and ask for
**concierge mode** (one step at a time, plain English). The Resume prompt is a **thin
pointer by design** (tenet 16; same discipline ADR 018 applies to editor pointer files)
— it carries **zero** context. *All* state lives in this file (Plain English + Next
action) and `AGENTS.md`, which the agent reads first. **Do not inline status, ADR
summaries, or caveats into it** — that re-creates a second copy of STATUS (drift, tenet
10) and spends tokens every prompt (the exact context-bloat behind COE 2026-06-08).
Operational caveats (gitleaks PATH refresh, "don't strip `.env` early", SSH-key-in-agent,
etc.) live under **Environment notes** / **Next action** below — not in the prompt.

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```

**Your passwords:** all in Bitwarden folder `ai-memory-infra`. SSH into the server still
needs your key passphrase (also in Bitwarden). Never paste secrets in chat.

## Current phase

**Phase 3 — Chrome extension fork → IN PROGRESS (session 14).** Decision made (**ADR 024**): fork
mem0's MIT `mem0-chrome-extension` into a separate **private** GitHub repo and rewire it to our
self-hosted server. `ai-memory-infra` keeps only a pointer under `extension/`; extension source now
lives in private repo **`vvbch/ai-memory-extension`**. Upstream baseline builds green, and the
self-hosted rewrite is committed in that repo (`7ac3011`): `memory.chandrav.dev`, `X-API-Key`,
`/memories`, `/search`, local settings, no mem0 cloud login, no PostHog. `dist/` is now loaded in
Chrome and **OpenMemory** appears on `chrome://extensions`; after the background-relay fix, the
ChatGPT sidebar now opens and loads Recent Memories from the live server. **Next: prove ChatGPT-side
save/search behavior against the live server, then close Phase 3 browser-reach docs.**

**Phase 2 — backup/restore → COMPLETE.** Scripts DONE & PROVEN; automation §1–§4 all built &
verified; the drill's 2nd healthchecks.io check (`DRILL_HEALTHCHECK_URL`) is now **wired & verified
green** (session 6). **DoD fully met — no operator steps remain.**

**Phase 2 — backup/restore → (history) REOPENED (scripts DONE & PROVEN; automation IN PROGRESS).**
`scripts/backup.sh` + `scripts/restore.sh` are live and proven: backup = online `pg_dump -Fc` +
online `tar` of the mem0 SQLite history + **offline** `neo4j-admin database dump` (brief
graph-only stop/start), uploaded with a SHA-256 manifest to
`s3://ai-memory-infra-backups-chandrav/backups/<UTC>/` (newest-7 retention); restore verifies
checksums, confirms, then `pg_restore --clean` + SQLite untar + offline neo4j `load`. **Restore
round-trip verified end-to-end** (write→backup→delete→restore→memory + vector search returned;
ADR 022). **But Phase 2 was re-scoped 2026-06-08 (backup-strategy review):** backups *were*
**manual** (unbounded RPO) and failed **silently**, so automation is in-scope. **Implementing ADR 023:
§1+§2 DEPLOYED & LIVE (2026-06-08):** ✅ daily systemd timer enabled+active on the droplet (next run
18:32 UTC); ✅ dead-man's-switch live, vendor = healthchecks.io, **confirmed green (HTTP 200)** from two
real service runs. ✅ **§3 data-loss hardening DONE (2026-06-08):** server-side versioning + 30 d/14 d
lifecycle (replaces the client-side delete-prune, removed from `backup.sh`); **least-privilege
bucket-scoped backup key** (`ai-memory-backup-only`, swapped into the droplet `.env` + verified —
session 4); pre-restore safety snapshot in `restore.sh`. ✅ **§4 recurring restore drill DONE &
VERIFIED (2026-06-08, session 5):** `scripts/restore-drill.sh` restores `latest` into throwaway
scratch (never live), asserts a planted canary round-trips **with its pgvector embedding** + the
Neo4j dump `neo4j-admin load`s clean + mem0 history is valid SQLite, then cleans up; monthly
`systemd` timer + separate drill heartbeat; drill **PASSED** on the droplet. **Phase 2 DoD MET** —
only wiring the drill's 2nd healthchecks.io check (`DRILL_HEALTHCHECK_URL`) remains (operator
console step), then Phase 3.

**Phase 1 — Infrastructure as Code → DEPLOYED.** `tf-init`/`plan`/`apply` all run:
9 resources created (droplet `s-2vcpu-4gb` BLR1 `168.144.145.29`, firewall 22/80/443,
5 Cloudflare A records, Spaces bucket `ai-memory-infra-backups-chandrav`). Droplet
bootstrapped (Docker + Compose + UFW). **Core stack live & healthy**: Caddy + Mem0
(built from source, `mem0-api-server:local`) + Postgres/pgvector + Neo4j. RAM ~1.6G/3.9G
used (headroom OK). `memory.chandrav.dev/docs` → 200 over HTTPS w/ valid cert. **API is
usable** (admin key works, models verified, round-trip persists), **reproducible**
(`bootstrap.sh` builds the image from pinned source; step 5 done), **and secured** (gitleaks
secret-scan pre-commit gate live — "no secrets in git" is deterministic). The one remaining
P1 item (strip the plaintext admin-UI note from `infra/.env`, local + droplet) is consciously
deferred to a post-burn-in cleanup pass (tenet 18, ~2026-06-15). **Next: Phase 3 (Chrome
extension fork).**

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

## Last decisions (2026-06-08, backup-strategy review — decisions only)

- **Tenet 17 sharpened (control-plane fix) — classify by the irreversibility of the
  *effect*, not the code.** A reversible artifact (script/config a `git revert` removes) can
  encode an *irreversible effect* — destructive restore, delete-on-prune retention, `DROP`,
  TTL/expiry, `--force` push. Those data-loss semantics are **one-way doors needing operator
  sign-off**, even though the diff reverts trivially. Test: "if this runs, can I get the data
  back?" Trigger: the review found ADR 022's destructive-restore + newest-7 delete-prune had
  been auto-made as "mechanical defaults" because the *scripts* were reversible — they should
  have been surfaced. In `tenets.md` + `AGENTS.md` summary.
- **Phase 2 re-scoped to include automation + data-loss hardening (ADR 023).** Backups are
  manual (unbounded RPO) and fail silently — not acceptable to close Phase 2 on. The
  BACKLOG-P2 "cron + restore drill" item is **promoted into active Phase 2**. Locked design
  (implement next session, tenet 16): **(1)** daily `systemd` timer (`Persistent=true`) over
  cron (tenet 7 — native logs + `OnFailure=`); **(2)** **dead-man's-switch** failure alerting
  (a self-sent email can't report a dead box) — the **monitoring vendor is an open operator
  decision (tenet 12)**: surface 2–3 options and let Chandra pick; **(3)** data-loss hardening
  — replace the client-side delete-prune with **server-side Spaces lifecycle/versioning**
  (web-verify DO Spaces versioning/object-lock first, tenet 8), a **least-privilege backup-only
  Spaces key**, and a **pre-restore safety snapshot** (makes a wrong restore recoverable);
  **(4)** a recurring **restore drill**. No code changed this session — decisions only.

## Last decisions (2026-06-08, backup/restore session)

- **ADR 022 — backup/restore design.** One timestamped Spaces prefix per backup holding
  `postgres.dump` + `neo4j.dump` + `mem0-history.tar.gz` + a SHA-256 `MANIFEST.txt`.
  **Per-store method = consistency with minimum downtime:** Postgres `pg_dump -Fc` online
  (transactionally consistent, zero downtime); mem0 SQLite history `tar`'d online (WAL-included =
  crash-consistent); **Neo4j offline `neo4j-admin dump`/`load`** because Community can only
  dump a *stopped* DB (online backup is Enterprise — verified vs the 5.26 manual) → a brief
  ~20–30 s graph-only stop/start, API stays up. **Tooling = `s3cmd` (apt)** over aws-cli/rclone
  (tenet 7 — one package); Spaces creds reuse the gitignored+gitleaks-gated `infra/.env`
  (not a new file). **Restore is whole-DB destructive** with a checksum gate + typed `RESTORE`
  confirm (`FORCE=1` skips). **No new vendor** (Spaces adopted in Phase 1), so no tenet-12
  deliberation — reversible dev tooling. **Proven:** codeword `ZEPHYR-7731` round-tripped
  write→backup→delete→restore incl. vector `/search`. Cron scheduling + a periodic restore
  drill are parked (BACKLOG P2).

## Last decisions (2026-06-08, P1-security session)

- **Tenet 18 added — burn-in before hardening; defer non-critical cleanup to a tracked
  post-launch pass.** Operator's call: keep a few convenience/diagnostic affordances (here,
  the plaintext admin-UI login note in `infra/.env`) through ~1 week of real usage, then sweep
  them in a deliberate hardening pass. The deferral must be **explicit, tracked, time-boxed**
  (parked in `BACKLOG.md` with a trigger), never left to memory — and **active risks / one-way
  doors are exempt** (fixed now, not parked). In `tenets.md` + `AGENTS.md` summary. Same
  reversibility test as tenet 17, applied to cleanup *timing*.
- **P1(a) `.env`-strip DEFERRED (tenet 18), P1(b) secret-scan DONE.** Split the BACKLOG P1
  security item: the plaintext-block strip is parked to the post-burn-in pass (~2026-06-15);
  the gitleaks pre-commit gate is implemented now. No ADR needed — gitleaks is a standard,
  reversible dev-tooling addition (the vendor-deliberation tenet 12 is for paid/lock-in
  dependencies; gitleaks is free, MIT, single static binary, trivially removable).
- **Secret-scan = native binary + the existing hand-rolled hook, not the `pre-commit`
  framework.** Chose `gitleaks git --staged` invoked from `scripts/hooks/pre-commit` (which
  already runs the Tenet-11 repo-health gate) over adopting the Python `pre-commit` framework —
  fewer moving parts (tenet 7; no Python-framework + Go/Docker toolchain), and it reuses the
  install path we already have (`install-hooks.ps1`, ADR 015). Config is a versioned
  `.gitleaks.toml` (tenet 1) extending the upstream default ruleset. **Missing-binary policy:
  BLOCK** (a security gate that silently no-ops is worse than one that asks to be installed);
  `install-hooks.ps1` auto-installs gitleaks via winget to keep the gate deterministic.

## Last decisions (2026-06-08, reproducible-deploy session)

- **Step 5 closed — deploy is reproducible; no new ADR needed.** Rebuilt the Mem0 image from
  the patched `infra/mem0-server.Dockerfile` (this is the control-plane fix promised by ADR
  021), proved it survives `compose up --force-recreate` via a fresh round-trip, and folded the
  clone-pinned-src + `docker build` into `scripts/bootstrap.sh`. **Reproducibility choices:**
  (a) **pin `MEM0_REF`** to a full commit SHA (overridable) so the build is deterministic —
  the Dockerfile's build-time `assert` is the safety net if a bumped ref restructures the
  patched code; (b) **build from source on the droplet** rather than push to GHCR (tenet 7 —
  fewer moving parts, no registry account/secret to manage; revisit GHCR only if multi-node);
  (c) **`compose pull` names only the external images** (caddy/postgres/neo4j) so the
  local-only Mem0 image + profiled-off dashboard can't break a clean bootstrap. Also documented
  the OpenAI allow-both-models prereq in `setup.md` (closes the step-4 blocker's doc debt).

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
source so it can't drift. Holds deferred-but-valuable work (P1 `.env` plaintext-note
strip — deferred to the post-burn-in pass, tenet 18; P2 policy-as-code pointer
enforcement + eval/CI gates; P3 Bitwarden family rollout + KeePassXC offline backup)
so nothing is lost and nothing displaces the critical path (tenet 13). **P1 secret-scan
pre-commit is now DONE** (gitleaks gate).

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
  dashboard later. ✅ **Custody DONE (2026-06-08):** `ADMIN_API_KEY` saved in Bitwarden
  `ai-memory-infra` (copied server→clipboard→vault, never shown in chat).
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
  **✅ Caveat RESOLVED (2026-06-08, step 5):** the writable-layer patch is now baked into the
  rebuilt image — `compose up --force-recreate mem0` + a fresh round-trip (user_id
  `diag-rebuild-20260608`) proved the gpt-5-mini bug no longer reverts on redeploy, and the
  from-source build is folded into `bootstrap.sh`. ✅ **Steps 1–5 all done** (Bitwarden custody
  gate closed; deploy reproducible).
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
- ✅ **Deploy now fully reproducible (2026-06-08, step 5 DONE).** `scripts/bootstrap.sh`
  now clones the **pinned** mem0 source (`MEM0_REF=366945965…`, overridable), `docker
  build`s `mem0-api-server:local` from `infra/mem0-server.Dockerfile` (graph deps + ADR 021
  patch + build-time `assert`), and pulls only the external base images (caddy/postgres/neo4j)
  so the local-only Mem0 image + profiled-off dashboard don't break `pull`. **Proven on the
  droplet:** rebuilt the image → `compose up --force-recreate mem0` → round-trip persisted
  (user_id `diag-rebuild-20260608`), confirming the gpt-5-mini patch now lives in the image,
  not just the writable layer. `bash -n` clean. `setup.md` updated (Step 6 auto-build +
  OpenAI allow-both-models prereq). Remaining redeploy nicety (P2): the dashboard image still
  needs building before its profile can be enabled.
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
- **gitleaks PATH:** gitleaks is installed but not on a fresh PowerShell PATH — before
  committing, refresh PATH in the same shell:
  `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`.
- **SSH:** key is in `ssh-agent` (passphrase in Bitwarden); secrets are read from the server
  `.env`, never printed. Droplet `168.144.145.29` (`root@`).
- **Appending to the droplet `.env` from Windows → CR now handled at the reader (FIXED 2026-06-08).**
  Piping a line from PowerShell over SSH (`$line | ssh … "cat >> .env"`) appends a trailing `\r`
  (CRLF), which used to silently break values read by `backup.sh`/`restore.sh` (a heartbeat URL with
  a `\r` → `curl: (3) URL rejected: Malformed input`). **Fixed once and for all:** `envval`/`envval_opt`
  now pipe every value through `tr -d '\r'`, so a CRLF `.env` line can no longer corrupt a value — no
  manual `sed -i 's/\r$//'` needed anymore (verified with a CRLF fixture: URL + quoted value both come
  out clean, no `0d` byte). Tracked `.sh` files are separately pinned to LF by `.gitattributes`.
- **Droplet repo sync = `git fetch && git reset --hard origin/main` (tenet 11, remote is truth).**
  The droplet `/opt/ai-memory-infra` is a real clone; it had live working-tree edits from earlier
  on-box sessions, but those were already committed to `origin/main` — verify with
  `git diff --stat origin/main` (expect only the intended new delta) *before* resetting, so no
  live-only patch is lost. `.env`/`terraform.tfvars` are gitignored, so a hard reset never touches them.
- **No-bash-on-Windows:** `bash -n` syntax checks use the Git-bundled bash at
  `C:\Program Files\Git\bin\bash.exe`.

## Next action

> **RESUME HERE — Phase 3 (Chrome extension fork) IN PROGRESS. Private repo exists; self-hosted
> rewrite is committed; unpacked extension load is done; background-relay fix is built; Chrome reload
> + ChatGPT sidebar Recent Memories are verified green.** Session 8 (2026-06-08): created private GitHub repo
> **`vvbch/ai-memory-extension`**,
> imported upstream MIT history, verified the raw upstream baseline, then rewrote and committed the
> self-hosted fork (`7ac3011`). Session 9: operator loaded `ai-memory-extension/dist` as an unpacked
> Chrome extension and confirmed **OpenMemory** appears on `chrome://extensions`. The stale Chrome
> load prompt was fixed in the control plane: web-verify current console/browser UI docs before
> prompting, name the exact artifact to select, and give the visible success condition. Node.js LTS was
> installed with `winget`; on this Windows PowerShell use `C:\Program Files\nodejs\npm.cmd` because
> `npm.ps1` is blocked by execution policy. npm reported 11 inherited audit findings; do not run
> `npm audit fix` blindly.
>
> **NEXT ACTION (next session, one step at a time):**
> 1. ✅ Create private GitHub repo **`ai-memory-extension`** and preserve upstream history/attribution.
> 2. ✅ Move the working surface to that repo and verify the raw upstream baseline (`npm install`,
>    `npm run build`) before changing code.
> 3. ✅ Rewire the transport/auth layer: `https://api.mem0.ai` gone; default server
>    `https://memory.chandrav.dev`; `Authorization: Bearer/Token` gone; **`X-API-Key`** helper; Google
>    sign-in replaced with local settings (server URL + API key + user id); PostHog/mem0 telemetry
>    removed/no-op. `npm run type-check` + `npm run build` green.
> 4. ✅ Load `ai-memory-extension/dist` as an unpacked Chrome extension. Current Chrome flow:
>    `chrome://extensions/` → Developer mode toggle → **Load unpacked** → select the `dist` folder
>    itself (the folder containing `manifest.json`) → confirm **OpenMemory** appears.
> 5. ✅ Enter the real API key from Bitwarden in the OpenMemory popup. Sidebar initially showed
>    **Error loading memories**.
> 6. ✅ Fix and rebuild the sidebar Recent Memories fetch: it now uses stored `serverUrl`, `apiKey`, and
>    `userId` consistently, handles non-2xx responses, and accepts the self-hosted memory response shape.
>    `npm run type-check` + `npm run build` green.
> 7. ✅ Reloaded the unpacked extension in `chrome://extensions/`; browser still showed:
>    `Error fetching memories: TypeError: Failed to fetch` on `https://chatgpt.com/`
>    (`assets/sidebar.ts-CSsZSEPr.js:126`) and `Cannot create item with duplicate id mem0.saveSelection`.
> 8. ✅ Fixed and rebuilt the two runtime errors from session 11. Chrome docs confirmed content scripts
>    on `chatgpt.com` cannot directly bypass CORS; the extension service worker must perform permitted
>    cross-origin API calls. Added a background API relay for `/memories` + `/search`, switched the
>    sidebar Recent Memories fetch plus ChatGPT content-script search/save calls through that relay, and
>    made `mem0.saveSelection` context-menu setup idempotent by remove/recreate on worker init.
>    `npm run type-check` + `npm run build` green; `dist/` regenerated.
> 9. ✅ Reloaded the real unpacked OpenMemory extension in Chrome
>    (`jdajdehjpohgmolnlijiiggfbolmenmo`, loaded from `ai-memory-extension/dist`), opened
>    `https://chatgpt.com/`, and verified the OpenMemory sidebar renders live Recent Memories:
>    **Total Memories = 1**, with Copy/View actions on the loaded memory card. The prior visible
>    `TypeError: Failed to fetch` sidebar state did not recur after the background relay.
> 10. **NEXT ACTION:** prove ChatGPT-side save/search behavior against the live server. Use the real
>    Chrome profile with OpenMemory already loaded; if it fails, inspect the OpenMemory service-worker
>    console plus the ChatGPT page console for background-relay errors.
> 11. **Handoff rule reminder:** when the next reversible session step is done and verified, update
>    `STATUS.md`/logs, run repo-health, then commit and push every touched repo before final response.
>    This is already authorized by the project control plane; do not leave completed work uncommitted.
> 12. Keep it a **thin REST/MCP client** of the live API (tenets 4/7) — no second brain. ChromeOS is
>    the first-class mobile path (ADR 004); Android best-effort (Kiwi archived Jan 2025).
>
> **Reminders / still-true context:** Nightly backup timer live (18:30 UTC ≈ 00:00 IST); monthly
> drill timer live (`30 19 1 * *` UTC ≈ 01:00 IST on the 1st), both watched by healthchecks.io. The
> permanent drill **canary** (`user_id=drill-canary`) is planted in live data — leave it. P1 `.env`
> plaintext-note strip stays **deferred** (tenet 18, trigger ~2026-06-15). Droplet sync, if ever
> needed: `git fetch && git diff --stat origin/main` then `git reset --hard origin/main` (`.env`
> gitignored, untouched by reset).

**§3(b) console flow (web-verified 2026-06-08, DO docs — for the next step):** DO **Per-Bucket Access
Keys** are GA. Console → **Spaces Object Storage** → **Access Keys** tab → **Create Access Key** →
scope **Limited access** → tick **only** `ai-memory-infra-backups-chandrav` → permission
**Read/Write/Delete** (DO has no write-without-delete tier) → name it (e.g. `ai-memory-backup-only`) →
**copy the secret once** → Bitwarden (ADR 017, never in chat). Note: a *limited* key can't change
bucket config (lifecycle/versioning stays under the full Terraform key — good) and is incompatible
with `PutBucketPolicy`. Then swap `SPACES_ACCESS_KEY`/`SPACES_SECRET_KEY` in the droplet
`/opt/ai-memory-infra/infra/.env`, run `backup.sh` to confirm, then retire the shared key's backup use.

1. ✅ **Commit the deploy changes** — DONE (prior session: `3d1db74` infra + `b6ffa2d`
   docs; repo-health green, both repos `0 ahead/0 behind`). No pending changes.
2. ✅ **Create an admin + API key** — DONE (2026-06-08). The `ADMIN_API_KEY` was already in
   the droplet `.env` (legacy admin mode, tenet 7 — no `make bootstrap`/dashboard needed);
   verified working (`X-API-Key` → 200, no key → 401). ✅ **Custody DONE (2026-06-08):** the key
   is in Bitwarden. **`make bootstrap` is a locked dead end (ADR 020)** — it would spin up mem0's
   *own* conflicting compose/DB stack; our stack runs from `/opt/ai-memory-infra/infra`. Do
   not revisit.
3. ✅ **Verify model config** — DONE (2026-06-08). Live container runs `gpt-5-mini` +
   `text-embedding-3-small`; `main.py` *does* read `MEM0_DEFAULT_*` (earlier note corrected).
   See the model-config blocker entry above for the source lines + the `gpt-4.1-nano` fallback
   risk.
4. ✅ **`POST /memories` round-trip — DONE (2026-06-08), persists end-to-end.** Both blockers
   cleared (OpenAI "allow all models"; mem0ai gpt-5-mini patch, ADR 021). Verified on the
   droplet: `POST /memories` (user_id `diag-roundtrip-20260608`) extracted 2 facts → `GET
   /memories?user_id=…` + `POST /search` returned them (setup.md "Done when" met). ✅ **Custody
   gate closed (2026-06-08):** `ADMIN_API_KEY` saved in Bitwarden `ai-memory-infra` (copied
   server→clipboard→vault, never shown in chat). **Steps 1–4 are all complete.**
5. ✅ **Make the deploy reproducible — DONE (2026-06-08).** Rebuilt `mem0-api-server:local`
   from the patched `infra/mem0-server.Dockerfile` on the droplet (ADR 021 baked in, build-time
   `assert` passed); `compose up --force-recreate mem0` + a fresh round-trip (user_id
   `diag-rebuild-20260608`) proved the gpt-5-mini bug no longer reverts. Folded the
   clone-pinned-src + `docker build` into `scripts/bootstrap.sh` (pulls only external base
   images so the local Mem0 image doesn't break `pull`); updated `setup.md` (Step 6 auto-build +
   OpenAI allow-both-models prereq). A clean `bootstrap.sh` now works (`bash -n` clean).
6. **P1 security cleanup — split (2026-06-08):** (a) **DEFERRED** — strip the plaintext admin-UI
   note from `infra/.env` (local + droplet `/opt/ai-memory-infra/infra/.env`) is parked to the
   post-burn-in cleanup pass (**tenet 18**, trigger ~2026-06-15); safe because `.env` is
   gitignored AND gitleaks now blocks it from git. (b) ✅ **DONE** — gitleaks secret-scan
   pre-commit gate added + tested (blocks secrets, passes clean); `install-hooks.ps1` ensures
   gitleaks is installed. "No secrets in git" is now deterministic.
7. 🔄 **Phase 2: backup/restore — SCRIPTS DONE & PROVEN; AUTOMATION re-scoped IN (2026-06-08).**
   Fleshed out `scripts/backup.sh` + `scripts/restore.sh`: backup = online `pg_dump -Fc` + online
   `tar` of the mem0 SQLite history + **offline** `neo4j-admin database dump` (brief graph
   stop/start), to `s3://ai-memory-infra-backups-chandrav/backups/<UTC>/` with a SHA-256 manifest,
   newest-7 retention; restore verifies checksums + typed-`RESTORE` confirm, then `pg_restore
   --clean` + SQLite untar + offline neo4j `load`. **Round-trip proven:** wrote codeword
   `ZEPHYR-7731` (user `backup-proof-20260608`) → backup → delete (`GET`→`[]`) → `restore.sh
   latest` → exact record + `/search` returned (vectors restored). ADR 022. **Re-scoped
   2026-06-08:** backups are manual (unbounded RPO) + fail silently → automation pulled into
   Phase 2 (see step 8). Tenet 17 sharpened (effect-vs-code).
8. 🔄 **Phase 2 automation + data-loss hardening (ADR 023) — §1+§2 DEPLOYED & LIVE; §3+§4 next.**
   (1) ✅ **Daily `systemd` timer DEPLOYED & LIVE** — `infra/systemd/ai-memory-backup.{service,timer}`
   (`Persistent=true`, 18:30 UTC) + `…-failure.service` (`OnFailure` journal marker); installed to
   `/etc/systemd/system/` on the droplet and **`enable --now`'d (enabled + active; next run 18:32 UTC ≈
   00:02 IST)**; also installed by `bootstrap.sh` for clean rebuilds. (2) ✅ **Dead-man's-switch wired +
   vendor = healthchecks.io + CONFIRMED GREEN** (free, open-source, no lock-in; web-verified vs
   cron-job.org + DO Uptime, tenet 8). `backup.sh` pings `/start` + success + `/fail` from
   `HEALTHCHECK_URL`; **added to the droplet `infra/.env`** (CR-strip gotcha fixed, see Environment
   notes); two on-demand `systemctl start ai-memory-backup.service` runs succeeded and **healthchecks.io
   returned HTTP 200 `OK`**. Operator's check = cron `30 18 * * *` UTC, 1 h grace; URL in Bitwarden.
   **Local backstop** = `OnFailure=` marker (a "newest prefix < 25 h" freshness check is still a TODO if
   we want belt-and-suspenders, but the external monitor covers silence).    (3) ✅ **Data-loss hardening — DONE 2026-06-08 (operator signed off: keep 30 d, recoverable 14 d).**
   Web-verified DO facts first (versioning ✅, lifecycle ✅, **Object-Lock/WORM ❌**, key scopes =
   Read/RWD/All only — no write-without-delete). **(a)** versioning confirmed already live; added two
   `lifecycle_rule`s to `infra/terraform/main.tf` (`expire-old-backups`: current @30 d + noncurrent
   @14 d + abort-MPU @1 d; `sweep-expired-delete-markers`) → `terraform apply` 1 changed, re-plan
   converged. **Removed the client-side `s3cmd del` prune** from `backup.sh`. **(c)** `restore.sh`
   now takes a **pre-restore safety snapshot** (default on; `SKIP_PRESNAPSHOT=1` escape hatch; failed
   snapshot aborts). **✅ (b) least-privilege key DONE (2026-06-08, session 4):** bucket-scoped DO
   Spaces "Limited Access" key `ai-memory-backup-only` (R/W/D — DO has no write-without-delete tier) →
   Bitwarden (custody) → swapped into the droplet `infra/.env`; **backup verified on the new key**
   (`Result=success`, 4 artifacts uploaded) after repairing a CR-injection from the cross-shell swap;
   old broad key removed from the droplet (retained locally for Terraform — the limited key can't
   change bucket config, so versioning/lifecycle stays under the full key). Temp `.env.bak.*` shredded.
   (4) ✅ **Restore drill — DONE & VERIFIED (2026-06-08, session 5).** Monthly, automated into a
   **throwaway scratch target** (`scripts/restore-drill.sh` + `scripts/plant-drill-canary.sh` +
   `infra/systemd/ai-memory-restore-drill.{service,timer,-failure.service}`). Lightweight by design
   (no full second stack — 4 GB box has no headroom): asserts a planted canary round-trips with its
   pgvector embedding, the Neo4j dump loads clean, and mem0 history is valid SQLite; never touches
   live data; **drill PASSED on the droplet**. **Done when** = all five met: backups run on the timer,
   success/failure reaches the operator, the store is delete/overwrite-resistant, restore pre-snapshots,
   and a drill cadence exists. ✅ **The drill's own healthchecks.io check (`DRILL_HEALTHCHECK_URL`) is
   now WIRED & VERIFIED GREEN (2026-06-08, session 6)** — 2nd check created (cron `30 19 1 * *` UTC,
   2 h grace, email on), URL in Bitwarden, appended to the droplet `.env` (clean/no-CR), drill re-run →
   **PASSED** → check green. **Phase 2 is fully closed; next is Phase 3.**
9. **THEN — Phase 3: Chrome extension fork.** Per build phases (AGENTS.md): fork/adapt a
   Chrome extension so the memory layer reaches the browser (desktop / ChromeOS). Web-verify
   the current extension landscape before committing (tenet 8); Android is best-effort only
   (Kiwi archived, ADR 004); keep it an MCP/REST client of the live API.

**Connection details:** droplet `168.144.145.29` (SSH `root@`, key passphrase in
Bitwarden); API `https://memory.chandrav.dev` (`/docs` open); Neo4j browser
`https://graph.chandrav.dev` (basic-auth `admin` / pwd in Bitwarden). Stack:
`docker compose -f docker-compose.yml -f docker-compose.prod.yml …` in
`/opt/ai-memory-infra/infra`. Pause/stop the bill anytime: `scripts/teardown.py`
(income-change risk above). The mem0 source is cloned at `/opt/mem0-src` for rebuilds.
