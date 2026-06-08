#!/usr/bin/env bash
# Phase 2 restore DRILL (ADR 023 §4) — prove the restore path still works,
# WITHOUT touching live data.
#
# A backup you have never test-restored is only a hope. This drill restores the
# latest backup into THROWAWAY, isolated scratch containers/volumes (never the
# live Postgres/Neo4j/mem0 volumes), asserts a known canary memory survived the
# round-trip — including its pgvector embedding — and tears everything down. It
# is safe to run unattended on a schedule (monthly systemd timer).
#
# Why "lightweight" (no full mem0 API round-trip): the 4GB droplet has no room to
# stand up a second full stack alongside the live one without risking it. So the
# drill verifies the BACKUP ARTIFACTS restore into structurally-valid, non-empty
# data (the part that actually rots) rather than re-exercising mem0's query code:
#   - Postgres dump  -> restored into a scratch pgvector container; asserts the
#                       canary row exists AND has a non-null embedding vector.
#   - Neo4j dump     -> loaded via `neo4j-admin database load` into a scratch
#                       volume; a clean load proves the dump is restorable.
#   - mem0 history   -> the tar extracts and the SQLite file has a valid header.
#
# Run on the droplet:
#   sudo bash /opt/ai-memory-infra/scripts/restore-drill.sh            # latest
#   sudo bash /opt/ai-memory-infra/scripts/restore-drill.sh 20260608T143749Z
#
# Reports to a SEPARATE dead-man's-switch (DRILL_HEALTHCHECK_URL in infra/.env)
# so a drill that fails — or stops running — alerts the operator, exactly like
# the nightly backup. No-op if that URL is unset. Nothing secret is printed.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ai-memory-infra}"
INFRA_DIR="${APP_DIR}/infra"
ENV_FILE="${INFRA_DIR}/.env"
PG_IMAGE="${PG_IMAGE:-ankane/pgvector:v0.5.1}" # must match the live Postgres image
NEO4J_IMAGE="${NEO4J_IMAGE:-neo4j:5.26.4}"     # must match the live Neo4j version
NEO4J_DB="${NEO4J_DB:-neo4j}"
CANARY_TAG="${DRILL_CANARY_TAG:-drill-canary}" # see scripts/plant-drill-canary.sh
WHICH="${1:-latest}"

# Unique, collision-proof scratch names so a drill can never touch live objects.
SUFFIX="$(date -u +%Y%m%d%H%M%S)-$$"
PGC="drill-pg-${SUFFIX}"
NEO_VOL="drill-neo4j-${SUFFIX}"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die() {
	echo "ERROR: $*" >&2
	exit 1
}

# Read a single value from .env without sourcing; strip a trailing CR (Windows
# CRLF safety — see backup.sh).
envval() {
	local key="$1"
	[[ -f "${ENV_FILE}" ]] || die "${ENV_FILE} not found."
	local line
	line="$(grep -E "^${key}=" "${ENV_FILE}" | head -n1 || true)"
	[[ -n "${line}" ]] || die "${key} is not set in ${ENV_FILE}."
	printf '%s' "${line#*=}" | tr -d '\r' | sed -e 's/[[:space:]]*#.*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}
envval_opt() {
	local key="$1"
	[[ -f "${ENV_FILE}" ]] || return 0
	local line
	line="$(grep -E "^${key}=" "${ENV_FILE}" | head -n1 || true)"
	[[ -n "${line}" ]] || return 0
	printf '%s' "${line#*=}" | tr -d '\r' | sed -e 's/[[:space:]]*#.*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

# Separate dead-man's-switch for the drill (ADR 023 §4 -> §2 pattern). Distinct
# from the backup's HEALTHCHECK_URL: a passing drill pings success; a failure or
# a missed run leaves the monitor silent and alerts the operator. Never fatal.
hc_ping() {
	[[ -n "${DRILL_HC_URL:-}" ]] || return 0
	curl -fsS -m 10 --retry 3 -o /dev/null "${DRILL_HC_URL}${1:-}" || true
}

cd "${INFRA_DIR}" || die "cannot cd to ${INFRA_DIR}"

BACKUP_BUCKET="$(envval BACKUP_BUCKET)"
SPACES_REGION="$(envval SPACES_REGION)"
SPACES_ACCESS_KEY="$(envval SPACES_ACCESS_KEY)"
SPACES_SECRET_KEY="$(envval SPACES_SECRET_KEY)"
DRILL_HC_URL="$(envval_opt DRILL_HEALTHCHECK_URL)"

SPACES_HOST="${SPACES_REGION}.digitaloceanspaces.com"
S3=(s3cmd
	"--access_key=${SPACES_ACCESS_KEY}"
	"--secret_key=${SPACES_SECRET_KEY}"
	"--host=${SPACES_HOST}"
	"--host-bucket=%(bucket)s.${SPACES_HOST}"
	--no-progress)

command -v s3cmd >/dev/null 2>&1 || die "s3cmd not installed (run backup.sh once, or apt-get install s3cmd)."

STAGE="$(mktemp -d)"
# Always clean up scratch: the temp dir, the throwaway pg container, and the
# throwaway neo4j volume. On a non-zero exit, fire the drill /fail heartbeat.
cleanup() {
	local rc=$?
	docker rm -f "${PGC}" >/dev/null 2>&1 || true
	docker volume rm -f "${NEO_VOL}" >/dev/null 2>&1 || true
	rm -rf "${STAGE}"
	[[ ${rc} -eq 0 ]] || hc_ping /fail
}
trap cleanup EXIT
hc_ping /start

# --- Resolve which backup to restore ------------------------------------------
if [[ "${WHICH}" == "latest" ]]; then
	TS="$("${S3[@]}" ls "s3://${BACKUP_BUCKET}/backups/" | awk '{print $NF}' | grep -oE '[0-9]{8}T[0-9]{6}Z' | sort | tail -n1 || true)"
	[[ -n "${TS}" ]] || die "no backups found in s3://${BACKUP_BUCKET}/backups/"
else
	TS="${WHICH}"
fi
PREFIX="backups/${TS}"
log "DRILL: restoring ${TS} into THROWAWAY scratch (live data is untouched)"

# --- Download + verify checksums (same gate as restore.sh) --------------------
for f in postgres.dump neo4j.dump mem0-history.tar.gz MANIFEST.txt; do
	"${S3[@]}" get --force "s3://${BACKUP_BUCKET}/${PREFIX}/${f}" "${STAGE}/${f}" >/dev/null \
		|| die "could not download ${f} (is ${TS} a complete backup?)"
done
log "Verifying checksums against MANIFEST.txt"
(cd "${STAGE}" && grep -E '\.(dump|tar\.gz)$' MANIFEST.txt | sha256sum -c -) \
	|| die "checksum mismatch — backup artifacts are corrupt."

# --- 1. Postgres: restore into a throwaway pgvector container ------------------
log "Starting scratch Postgres (${PGC})"
docker run -d --name "${PGC}" \
	--memory=512m \
	-e POSTGRES_USER=mem0 -e POSTGRES_PASSWORD=drill -e POSTGRES_DB=mem0 \
	"${PG_IMAGE}" >/dev/null
# Wait for it to accept connections (bounded).
ok=0
for _ in $(seq 1 30); do
	if docker exec "${PGC}" pg_isready -q -U mem0 >/dev/null 2>&1; then
		ok=1
		break
	fi
	sleep 2
done
[[ "${ok}" -eq 1 ]] || die "scratch Postgres never became ready."

log "Restoring postgres.dump into the scratch DB"
docker cp "${STAGE}/postgres.dump" "${PGC}:/tmp/postgres.dump"
docker exec -e PGPASSWORD=drill "${PGC}" \
	pg_restore --clean --if-exists --no-owner -U mem0 -d mem0 /tmp/postgres.dump 2>/dev/null || true
# pg_restore can emit non-fatal NOTICE/skip noise on a fresh DB; the assertions
# below — not its exit code — are the real pass/fail signal.

log "Asserting the canary memory survived (row + non-null embedding)"
total="$(docker exec -e PGPASSWORD=drill "${PGC}" \
	psql -U mem0 -d mem0 -At -c "select count(*) from memories" 2>/dev/null || echo 0)"
canary="$(docker exec -e PGPASSWORD=drill "${PGC}" \
	psql -U mem0 -d mem0 -At \
	-c "select count(*) from memories where payload::text ilike '%${CANARY_TAG}%' and vector is not null" 2>/dev/null || echo 0)"
log "  scratch memories total=${total}, canary-with-embedding=${canary}"
[[ "${total}" =~ ^[0-9]+$ && "${total}" -ge 1 ]] || die "restored 'memories' table is empty or missing — restore did not produce working data."
[[ "${canary}" =~ ^[0-9]+$ && "${canary}" -ge 1 ]] \
	|| die "canary (user_id=${CANARY_TAG}) not found WITH an embedding in the restored DB — run plant-drill-canary.sh, then take a fresh backup."

# --- 2. Neo4j: load the dump into a throwaway volume (CLI, no running server) --
log "Loading neo4j.dump into a throwaway volume (proves the dump is restorable)"
chmod 777 "${STAGE}"
docker run --rm \
	-v "${NEO_VOL}:/data" \
	-v "${STAGE}:/backups" \
	"${NEO4J_IMAGE}" \
	neo4j-admin database load "${NEO4J_DB}" --from-path=/backups --overwrite-destination=true \
	|| die "neo4j-admin load failed — the graph dump is not restorable."

# --- 3. mem0 SQLite history: extracts + valid SQLite header --------------------
log "Checking mem0 history archive (extracts + valid SQLite file)"
HIST_DIR="${STAGE}/hist"
mkdir -p "${HIST_DIR}"
tar xzf "${STAGE}/mem0-history.tar.gz" -C "${HIST_DIR}" || die "mem0-history.tar.gz did not extract."
DBFILE="$(find "${HIST_DIR}" -maxdepth 3 -type f \( -name '*.db' -o -name 'history*' \) -size +0c | head -n1 || true)"
[[ -n "${DBFILE}" ]] || die "no non-empty mem0 history DB file inside the archive."
hdr="$(head -c 16 "${DBFILE}" | tr -d '\000')"
[[ "${hdr}" == "SQLite format 3" ]] || die "mem0 history file is not a valid SQLite database (header='${hdr}')."

log "DRILL PASSED for ${TS}: Postgres canary+embedding restored, Neo4j dump loadable, mem0 history valid."
hc_ping
