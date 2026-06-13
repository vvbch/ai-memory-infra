# ADR 022: Backup & restore design (Phase 2)

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** the operator

### Context

Phase 1 left three independent stateful stores on the droplet, with no off-box
copy: **Postgres/pgvector** (the memories + their embeddings), **Neo4j** (the
Mem0 + LifeGraph knowledge graph), and a **mem0 SQLite "history" DB** (the
edit log, in the `mem0_history` volume at `/app/history`). A disk loss, a bad
`compose up`, or a fat-fingered delete would be unrecoverable. Phase 2's job:
snapshot all three to the already-provisioned Spaces bucket
(`ai-memory-infra-backups-example`, sgp1) and prove a restore round-trips.

`scripts/backup.sh` / `scripts/restore.sh` existed only as empty scaffolding.

### Decision

**One timestamped prefix per backup**, holding all three artifacts plus a
checksum manifest: `s3://$BACKUP_BUCKET/backups/<UTC>/` →
`postgres.dump`, `neo4j.dump`, `mem0-history.tar.gz`, `MANIFEST.txt`.

Per-store method, chosen for **consistency with minimum downtime**:

1. **Postgres → `pg_dump -Fc`, online.** Run inside the running container; the
   custom-format dump is transactionally consistent, so **no downtime**. Restore
   is `pg_restore --clean --if-exists --no-owner` (drop+recreate objects); the
   pgvector extension and vector columns ride along in the dump.
2. **Neo4j → `neo4j-admin database dump`/`load`, OFFLINE.** Neo4j **Community**
   can only dump a *stopped* database (online `backup` is Enterprise-only —
   verified against the 5.26 Operations Manual). So the script briefly
   `compose stop neo4j`, runs the dump in an ephemeral `neo4j:5.26.4` container
   against the `neo4j_data` volume, then `compose start neo4j`. **Only the graph
   pauses (~20–30 s); the API, Postgres and SQLite stay up.** Restore is the
   mirror: stop → `load --overwrite-destination` → start.
3. **mem0 SQLite history → `tar` of the volume, online.** Tarring the whole
   `/app/history` dir (including any `-wal`/`-shm`) is crash-consistent — SQLite
   replays the WAL on next open. Restore wipes the volume and untars.

**Tooling: `s3cmd` (apt), creds in `infra/.env`.** Spaces is S3-compatible;
`s3cmd` is a single apt package (`backup.sh` installs it on first run, like
`bootstrap.sh` does for Docker). The bucket name + `SPACES_ACCESS_KEY`/
`SPACES_SECRET_KEY` (the same Spaces pair Terraform uses) live in the droplet's
gitignored `infra/.env` — the existing single home for secrets on the box
(gitignored *and* gitleaks-gated, so they can't reach git). New `.env.example`
keys document them.

**Safety rails:** restore verifies SHA-256 against `MANIFEST.txt` before
touching anything, and requires a typed `RESTORE` confirmation (`FORCE=1` to
skip for automation). Retention keeps the newest **7** prefixes.

### Alternatives considered

- **Neo4j online/cold-tar instead of offline dump.** Online backup needs
  Enterprise (paid — tenets 6/15). A *cold tar* of the `neo4j_data` volume would
  also work given we pin `neo4j:5.26.4`, but the `neo4j-admin` dump is the
  documented, version-portable, far smaller artifact (13 KB vs a multi-MB store
  tar) — worth the same brief stop. Chose dump/load.
- **`aws-cli` or `rclone` instead of `s3cmd`.** Both work with Spaces, but are
  heavier installs for no gain here (tenet 7 — fewer moving parts). `s3cmd` is
  one package and the flags map cleanly to a DO Spaces endpoint.
- **A separate `backup.env` for the Spaces creds.** Marginally tidier
  (keeps the Spaces secret out of the mem0/caddy container env), but adds a
  second secret file to manage. Reused `.env` for consistency; revisit if we
  ever split per-service secrets.
- **Scheduling now (cron/systemd timer).** Out of scope for "stand up + verify";
  the script is manual today. Automated daily backups + a periodic restore drill
  are parked in `BACKLOG.md` (P2).

### Consequences (reversible — tenet 12)

- **Backup costs a ~20–30 s graph-only pause**; full availability for the API
  and memory reads/writes that don't hit the graph. Restore is a maintenance
  operation (mem0 is stopped, all three stores overwritten) — expected.
- **Proven end-to-end (2026-06-08).** Wrote a known memory (codeword
  `ZEPHYR-7731`, user `backup-proof-20260608`) → backed up → **deleted** it
  (`GET` returned `[]`) → `restore.sh` (latest) → the exact record returned
  (same id/timestamp/hash) and a semantic `/search` ranked it — confirming the
  **pgvector embeddings**, not just the rows, restored.
- The scripts are reversible dev tooling (no vendor adoption — Spaces was
  adopted in Phase 1); a clean `git revert` removes them.
- **Not yet automated** — backups run on demand. Cron + restore-drill cadence
  is BACKLOG P2.

*(Sources: Neo4j 5.26 Operations Manual — offline backup/restore-dump pages;
verified live on the droplet 2026-06-08.)*

---
