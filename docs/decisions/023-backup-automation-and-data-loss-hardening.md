# ADR 023: Backup automation & data-loss hardening (Phase 2, reopened)

**Status:** Accepted — **§1 (timer) + §2 (heartbeat) LIVE; §3 (data-loss hardening) DONE
(incl. §3b least-privilege key); §4 (restore drill) IMPLEMENTED & VERIFIED 2026-06-08** (see
the Implementation updates below). All five decisions are now built; the only remaining task
is the operator console step to create the drill's second healthchecks.io check
(`DRILL_HEALTHCHECK_URL`). This ADR is the spec; the Implementation updates record what was
verified and built.
**Date:** 2026-06-08
**Deciders:** Chandra

### Context

ADR 022 stood up `scripts/backup.sh` / `restore.sh` and **proved** a restore round-trips
(codeword `ZEPHYR-7731`), but left two things open that a backup-strategy review
(2026-06-08) decided were not acceptable to ship Phase 2 on:

1. **Backups are manual.** Real RPO ("how much data can I lose?") is therefore "time since
   I last *remembered* to run it" — unbounded. A disk loss weeks after the last manual run
   loses weeks. (Restore RTO is already good: minutes, one command.)
2. **Failure is silent.** A skipped or failed backup tells no one. A backup nobody is
   alerted on is not a backup.

The review also surfaced a **control-plane miss** (now fixed): ADR 022's *destructive
whole-DB restore* and *delete-on-prune retention (newest-7)* are **data-loss semantics**
that were auto-made as "mechanical defaults" because the *scripts* are reversible (a `git
revert` removes them). Tenet 17 has been **sharpened**: classify a decision by the
irreversibility of its *effect on data*, not of the code — destructive restore / prune /
TTL / `DROP` are one-way doors needing operator sign-off even when the diff reverts
trivially. This ADR is where those data-loss choices are now explicitly ratified.

**Decision (operator): re-scope Phase 2 to include automation + data-loss hardening.**
Phase 2 is **not done** until backups are *scheduled, self-monitoring, and the restore
path has a recurring drill*. The "cron + restore drill" BACKLOG-P2 item is promoted into
the active Phase-2 scope. (Phase 3 — Chrome extension — comes after.)

### Decision

Five decisions, to be **implemented next session**:

1. **Schedule → daily `systemd` timer (not cron).** A `backup.service` (oneshot, runs
   `backup.sh` non-interactively — it already self-prunes and installs `s3cmd`) driven by a
   daily `backup.timer` with `Persistent=true` (catches a missed run if the droplet was
   paused — relevant to the income-risk pause/resume path), at a low-traffic UTC hour.
   *Why over cron (tenet 7):* systemd is already present (no new package), gives
   `journalctl` logs and a **native `OnFailure=`** hook for alerting; cron has neither
   cleanly. The timer unit ships as a versioned file installed by `bootstrap.sh` (tenet 1).
2. **Failure alerting → dead-man's-switch (heartbeat), direction decided; vendor is an
   operator decision.** `backup.sh` pings a monitor URL **on success**; if the expected
   ping doesn't arrive on schedule, the *monitor* alerts the operator. **Key insight:** a
   droplet that emails its own failures **cannot tell you it died** — only an external
   monitor watching for silence can. The **monitoring vendor is a one-way-door-ish adoption
   (tenet 12)** → the next session must **surface 2–3 options to the operator and let him
   pick** (candidates to web-verify, tenet 8: healthchecks.io free tier; cron-job.org; DO's
   own Uptime/Monitoring), with the documented exit path. Local backstop until chosen:
   `systemd OnFailure=` writing a clear marker to the journal + a freshness check (newest
   backup prefix < ~25 h old).
3. **Data-loss hardening (the tenet-17 trigger) — three parts:**
   - **(a) Don't let the prune be the only guard.** Today `backup.sh` issues a client-side
     `s3cmd del` of old prefixes — i.e. the *script* can delete backups. Move retention to
     **server-side bucket lifecycle expiry** and, if supported, enable **object
     versioning** so a delete/overwrite is recoverable. **Next session must web-verify
     (tenet 8)** DigitalOcean Spaces support for *versioning* and *object-lock/immutability*
     and lifecycle expiry **before implementing** — do not assume S3 parity. Prefer
     server-side lifecycle over the script deleting; keep newest-7-ish as the policy target.
   - **(b) Dedicated, least-privilege Spaces key for backups.** Today backup/restore reuse
     the same full-access Spaces pair Terraform uses. Issue a **separate backup credential**
     scoped to write+list on the backup bucket (no broad/mass-delete) so a leaked droplet
     key can't wipe the backup history. (Revisits ADR 022's parked "separate `backup.env`"
     alternative — now justified by blast-radius, not tidiness.) Stored in `infra/.env`
     (gitignored + gitleaks-gated) and Bitwarden (ADR 017).
   - **(c) Pre-restore safety snapshot.** `restore.sh` takes a quick backup of the
     **current** state *before* it overwrites anything, so a mistaken or wrong-snapshot
     restore is itself recoverable. This directly converts the destructive-restore one-way
     door into a two-way door. Gated so it can be skipped (`FORCE`/flag) for automated
     drills against throwaway state.
4. **Restore drill → recurring, automated where feasible.** A scheduled (monthly) drill
   that exercises the *restore* path so it can't silently rot as the stack changes. Cheapest
   automatable form: restore the latest backup into a **throwaway/parallel namespace or a
   disposable target** and assert a known codeword round-trips (mirrors the ZEPHYR proof);
   otherwise a documented checklist on a calendar trigger. Result feeds the same alerting
   channel as (2).
5. **Phase-2 Definition of Done updated.** Phase 2 closes only when: backups run on the
   timer, a success/failure signal reaches the operator, the backup store is delete/
   overwrite-resistant, restore takes a pre-snapshot, and a drill cadence exists.

### Alternatives considered

- **cron instead of a systemd timer.** Simpler mental model, equally zero-install, but no
  native failure hook and weaker logging. Rejected for the timer (tenet 7 favours the tool
  that *also* gives observability for free).
- **Self-sent email/Slack on failure (no heartbeat).** Can't report a *dead box* (the
  thing most likely to also kill the alert). Heartbeat/dead-man's-switch is the correct
  pattern; self-sent alerts are at most a secondary signal.
- **Keep backups manual (status quo / leave parked at P2).** Rejected by the operator —
  the manual-RPO + silent-failure gaps are exactly what Phase 2 exists to close.
- **Self-host the monitor** (e.g. self-hosted healthchecks). More control, but a new
  always-on service to run/secure/monitor on the same box whose death we're trying to
  detect (circular) — heavier than the value (tenet 7). Hosted free tier preferred; left to
  the operator (tenet 12).

### Consequences (reversible — tenet 12 / 17)

- Adds small moving parts: a versioned timer+service unit, a dedicated backup key, a
  monitor integration. Each is justified by closing the RPO / silent-failure / data-loss
  gaps, and each reverts cleanly (the *effects* — scheduling, alerting — create no
  destructive data semantics; the prune change *reduces* destructiveness).
- **One open operator decision carried into the next session:** the monitoring vendor
  (tenet 12). The next session surfaces options and gets the pick before wiring it.
- **Two facts to web-verify before baking (tenet 8):** DO Spaces versioning/object-lock
  support, and Spaces key-scoping granularity for the least-privilege backup key.
- Implementation is **deferred to a fresh session** (tenet 16); this ADR + STATUS "Next
  action" carry the full spec so that session resumes with zero loss.

*(Pairs with ADR 022, which it extends. Control-plane fix: tenet 17 "classify by the
irreversibility of the effect, not the code".)*

---

## Implementation update (2026-06-08, §3 data-loss hardening)

**Vendor facts web-verified first (tenet 8; source = DigitalOcean official docs):**

- **Spaces Bucket Versioning — SUPPORTED** (API/Terraform only, not the control panel). A
  delete creates a *delete-marker* and the prior object becomes a recoverable noncurrent
  version. Once enabled a bucket can never return to fully-unversioned (only suspended).
- **Spaces Bucket Lifecycle — SUPPORTED**: time-based `expiration`,
  `noncurrent_version_expiration`, `expired_object_delete_marker`, and
  abort-incomplete-multipart. (Tag-based rules are *not* supported — we don't need them.)
- **Object-Lock / WORM — NOT SUPPORTED** (DO-staff-confirmed). True immutability would
  require a *different provider* (S3/B2/Wasabi) = a tenet-12 vendor change, **out of scope**.
  Versioning is the practical delete/overwrite recovery net instead.
- **Spaces access-key scopes = Read / Read-Write-Delete / All only** → there is **no
  "write-but-cannot-delete" tier**. So §3(b)'s "no mass-delete" goal isn't fully attainable
  on DO; the realistic least-privilege is a key **scoped to the backup bucket only** (limits
  blast radius), with versioning as the recovery backstop.

**Built (operator-approved retention: keep 30 days; deleted/overwritten copies recoverable
14 days):**

- **(§3a) Versioning + server-side lifecycle, via Terraform** (`infra/terraform/main.tf`,
  `digitalocean_spaces_bucket.backups`). Versioning was already declared and confirmed
  **live** by a refresh-plan (no change). Added two `lifecycle_rule`s — `expire-old-backups`
  (`expiration.days=30`, `noncurrent_version_expiration.days=14`,
  `abort_incomplete_multipart_upload_days=1`) and `sweep-expired-delete-markers`
  (`expired_object_delete_marker=true`). `terraform apply` = *1 changed*; a follow-up plan
  reported **"No changes"** (converged). Retention is now a **declarative, auditable
  server-side policy**, not an imperative client-side `rm`.
- **(§3a, cont.) Removed the client-side prune** from `backup.sh` (the old
  `s3cmd del --recursive --force` of old prefixes). The backup path **no longer deletes
  anything** — a buggy or compromised droplet can't wipe the backup history.
- **(§3c) Pre-restore safety snapshot** added to `restore.sh`: after the typed `RESTORE`
  confirm and *before* any overwrite, it runs `backup.sh` to capture the **current** state,
  converting the destructive restore into a two-way door. Default ON; `SKIP_PRESNAPSHOT=1`
  escape hatch for when the current state is already broken/unbackupable. A failed snapshot
  **aborts** the restore (won't overwrite live data blindly).

**Still open:**

- ~~**(§3b) Least-privilege backup key**~~ — **DONE 2026-06-08 (session 4):** bucket-scoped
  `ai-memory-backup-only` key (R/W/D — DO has no write-without-delete tier) created in the
  console, stored in Bitwarden, swapped into the droplet `.env`; backup verified on it.
- ~~**(§4) Recurring restore drill**~~ — **DONE 2026-06-08 (session 5):** see the §4
  implementation update below.

*(Cross-platform fix shipped alongside: `backup.sh`/`restore.sh` `.env` readers now strip a
trailing CR via `tr -d '\r'`, so a Windows/PowerShell-appended `.env` line can't corrupt a
value — retires the manual `sed -i 's/\r$//'` gotcha.)*

---

## Implementation update (2026-06-08, §4 recurring restore drill)

**Design (operator-approved: lightweight, isolated):** a **monthly** drill that restores the
**latest** backup into **throwaway scratch containers/volumes** and asserts a known canary
survived — **never touching live Postgres/Neo4j/mem0 volumes**. "Lightweight" over a full
scratch-stack `/search` round-trip because the 4 GB droplet has no headroom to stand up a
second full stack alongside the live one without risking it (tenet 17 — don't let a drill
endanger live data). The drill verifies the part that actually rots — that the **backup
artifacts restore into structurally-valid, non-empty data** — not mem0's (unchanged) query
code.

**Built:**

- **`scripts/restore-drill.sh`** — downloads `latest` (or a given timestamp), verifies the
  SHA-256 manifest (same gate as `restore.sh`), then: **(Postgres)** restores `postgres.dump`
  into a scratch `ankane/pgvector` container (`--memory=512m`, unique name) and asserts the
  `memories` table is non-empty **and** ≥1 canary row exists *with a non-null embedding*
  (`payload::text ilike '%drill-canary%' and vector is not null`); **(Neo4j)** `neo4j-admin
  database load`s `neo4j.dump` into a throwaway volume (a clean load proves restorability);
  **(mem0 history)** extracts the tar and checks the SQLite file has a valid `SQLite format 3`
  header. An EXIT trap force-removes the scratch container + volume + temp dir every time.
  Reports to a **separate** dead-man's-switch (`DRILL_HEALTHCHECK_URL`, no-op if unset).
- **`scripts/plant-drill-canary.sh`** — plants the permanent, clearly-namespaced canary
  (`user_id=drill-canary`, codeword `DRILLCANARY7Q4Z9`) via `POST /memories` so every backup
  contains a deterministic assertion target. Idempotent enough (the drill only needs ≥1).
  Committed (tenet 1) so the canary is re-plantable after a from-scratch rebuild or a restore
  predating it.
- **systemd units** (`infra/systemd/ai-memory-restore-drill.{service,timer}` +
  `…-failure.service`) — monthly `OnCalendar=*-*-01 19:30 UTC` (01:00 IST, an hour after the
  nightly backup so the drill restores a fresh same-night backup and they never overlap),
  `Persistent=true` (catch-up if the box was paused), `OnFailure` journal marker.
  `bootstrap.sh` installs + `enable --now`s them for clean rebuilds.

**Verified on the droplet (tenet 17 — proven before declaring done):** planted the canary →
took a fresh backup (`Result=success`) → ran the drill → **DRILL PASSED**: checksums OK,
scratch Postgres `total=6, canary-with-embedding=2`, 258 MB Neo4j dump loaded clean, mem0
history a valid SQLite DB; scratch fully torn down (no leftover `drill-*` containers/volumes),
live stack untouched (mem0 up 9 h, ~2.3 GB free).

**Open operator step (concierge):** create the **second healthchecks.io check** for the drill
(period ~35 d, grace ~2 h) and paste its URL into the droplet `.env` as
`DRILL_HEALTHCHECK_URL` — until then the drill self-tests but doesn't externally alert.

**Phase-2 DoD (decision 5) now MET:** backups run on the timer · success/failure reaches the
operator · the store is delete/overwrite-resistant · restore pre-snapshots · **a drill cadence
exists**. Phase 2 closes (pending the drill heartbeat wiring). Next: **Phase 3 — Chrome
extension.**
