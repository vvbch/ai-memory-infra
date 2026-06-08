#!/usr/bin/env bash
# Phase 2 backup — snapshot all three datastores to DigitalOcean Spaces.
#
# Backs up, into one timestamped prefix in the Spaces bucket:
#   1. Postgres/pgvector  -> pg_dump custom-format archive (online, consistent)
#   2. Neo4j graph        -> neo4j-admin database dump (OFFLINE: Community Edition
#                            can only dump a stopped DB, so we briefly stop/start
#                            the neo4j container — the rest of the stack stays up)
#   3. mem0 SQLite history-> tar of the /app/history volume (incl. any -wal/-shm)
#
# Layout in the bucket:
#   s3://$BACKUP_BUCKET/backups/<UTC-timestamp>/
#       postgres.dump  neo4j.dump  mem0-history.tar.gz  MANIFEST.txt
#
# Run on the droplet (idempotent; installs s3cmd if missing):
#   sudo bash /opt/ai-memory-infra/scripts/backup.sh
#
# Credentials + target come from infra/.env (gitignored):
#   BACKUP_BUCKET  SPACES_REGION  SPACES_ACCESS_KEY  SPACES_SECRET_KEY
#   POSTGRES_USER  POSTGRES_DB    POSTGRES_PASSWORD
# Nothing secret is ever printed.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ai-memory-infra}"
INFRA_DIR="${APP_DIR}/infra"
ENV_FILE="${INFRA_DIR}/.env"
PROJECT="${COMPOSE_PROJECT_NAME:-ai-memory-infra}" # `name:` in docker-compose.yml
NEO4J_IMAGE="${NEO4J_IMAGE:-neo4j:5.26.4}"         # must match the running version
NEO4J_DB="${NEO4J_DB:-neo4j}"                       # default DB holds mem0 + LifeGraph
RETAIN="${RETAIN:-7}"                               # keep this many newest backups

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die() {
	echo "ERROR: $*" >&2
	exit 1
}

# Read a single value from .env WITHOUT sourcing it (the bcrypt BASIC_AUTH_HASH
# contains `$` that a shell `source` would try to expand/mangle).
envval() {
	local key="$1"
	[[ -f "${ENV_FILE}" ]] || die "${ENV_FILE} not found."
	local line
	line="$(grep -E "^${key}=" "${ENV_FILE}" | head -n1 || true)"
	[[ -n "${line}" ]] || die "${key} is not set in ${ENV_FILE}."
	# strip `key=`, surrounding quotes, and any trailing inline comment/whitespace
	printf '%s' "${line#*=}" | sed -e 's/[[:space:]]*#.*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

# Like envval, but returns empty (no error) when the key is absent — for OPTIONAL
# settings such as the heartbeat URL.
envval_opt() {
	local key="$1"
	[[ -f "${ENV_FILE}" ]] || return 0
	local line
	line="$(grep -E "^${key}=" "${ENV_FILE}" | head -n1 || true)"
	[[ -n "${line}" ]] || return 0
	printf '%s' "${line#*=}" | sed -e 's/[[:space:]]*#.*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

# Optional dead-man's-switch heartbeat (ADR 023 §2). If HEALTHCHECK_URL is set in
# .env, ping it: "/start" when the backup begins, the bare URL on success, and
# "/fail" on any failure. An external monitor (healthchecks.io) alerts the
# operator if the success ping never arrives on schedule — catching a dead box, a
# skipped timer run, or a silent failure that a self-sent email never could. Always
# a no-op (never fatal) when unset or the monitor is unreachable.
hc_ping() {
	[[ -n "${HC_URL:-}" ]] || return 0
	curl -fsS -m 10 --retry 3 -o /dev/null "${HC_URL}${1:-}" || true
}

cd "${INFRA_DIR}" || die "cannot cd to ${INFRA_DIR}"

BACKUP_BUCKET="$(envval BACKUP_BUCKET)"
SPACES_REGION="$(envval SPACES_REGION)"
SPACES_ACCESS_KEY="$(envval SPACES_ACCESS_KEY)"
SPACES_SECRET_KEY="$(envval SPACES_SECRET_KEY)"
PG_USER="$(envval POSTGRES_USER)"
PG_DB="$(envval POSTGRES_DB)"
PG_PW="$(envval POSTGRES_PASSWORD)"
HC_URL="$(envval_opt HEALTHCHECK_URL)" # optional dead-man's-switch (ADR 023 §2)

SPACES_HOST="${SPACES_REGION}.digitaloceanspaces.com"
S3=(s3cmd
	"--access_key=${SPACES_ACCESS_KEY}"
	"--secret_key=${SPACES_SECRET_KEY}"
	"--host=${SPACES_HOST}"
	"--host-bucket=%(bucket)s.${SPACES_HOST}"
	--no-progress)

# --- 0. Tooling: ensure s3cmd is installed (Spaces is S3-compatible) ----------
if ! command -v s3cmd >/dev/null 2>&1; then
	log "Installing s3cmd (one-time)"
	export DEBIAN_FRONTEND=noninteractive
	apt-get update -y && apt-get install -y s3cmd
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
PREFIX="backups/${TS}"
STAGE="$(mktemp -d)"
# On exit: always clean the stage dir; if we're exiting non-zero, fire the "/fail"
# heartbeat so the monitor alerts fast (the missing success ping would catch it
# anyway, just later).
cleanup() {
	local rc=$?
	rm -rf "${STAGE}"
	[[ ${rc} -eq 0 ]] || hc_ping /fail
}
trap cleanup EXIT
hc_ping /start
log "Staging backup ${TS} in ${STAGE}"

# --- 1. Postgres/pgvector (online, transactionally consistent) ----------------
log "Dumping Postgres database '${PG_DB}' (pg_dump -Fc)"
"${COMPOSE[@]}" exec -T -e PGPASSWORD="${PG_PW}" postgres \
	pg_dump -U "${PG_USER}" -d "${PG_DB}" -Fc >"${STAGE}/postgres.dump"
[[ -s "${STAGE}/postgres.dump" ]] || die "postgres.dump is empty."

# --- 2. mem0 SQLite history (tar the /app/history volume) ---------------------
# Done while mem0 runs; including any -wal/-shm makes the copy crash-consistent
# (SQLite replays the WAL on next open).
log "Archiving mem0 SQLite history volume"
docker run --rm \
	-v "${PROJECT}_mem0_history:/history:ro" \
	-v "${STAGE}:/out" \
	alpine:3 \
	sh -c "tar czf /out/mem0-history.tar.gz -C /history . && ls -la /history" \
	>/dev/null
[[ -s "${STAGE}/mem0-history.tar.gz" ]] || die "mem0-history.tar.gz is empty."

# --- 3. Neo4j (OFFLINE dump — Community can only dump a stopped DB) ------------
log "Stopping neo4j for an offline dump (rest of the stack stays up)"
"${COMPOSE[@]}" stop neo4j
# The neo4j image entrypoint runs as root and chowns /data (so it must be mounted
# read-write — the chown is a no-op since it's already neo4j-owned), then drops to
# the neo4j user to run the dump. That user must be able to write the host stage
# dir, so make it world-writable (it's an ephemeral mktemp dir, removed on exit).
chmod 777 "${STAGE}"
neo4j_dump_ok=0
if docker run --rm \
	-v "${PROJECT}_neo4j_data:/data" \
	-v "${STAGE}:/backups" \
	"${NEO4J_IMAGE}" \
	neo4j-admin database dump "${NEO4J_DB}" --to-path=/backups --overwrite-destination=true; then
	neo4j_dump_ok=1
fi
log "Restarting neo4j"
"${COMPOSE[@]}" start neo4j
[[ "${neo4j_dump_ok}" -eq 1 ]] || die "neo4j dump failed (neo4j was restarted)."
[[ -s "${STAGE}/${NEO4J_DB}.dump" ]] || die "${NEO4J_DB}.dump is empty."
# neo4j-admin names the file <db>.dump; normalise to neo4j.dump for restore.
[[ "${NEO4J_DB}" == "neo4j" ]] || mv "${STAGE}/${NEO4J_DB}.dump" "${STAGE}/neo4j.dump"

# --- 4. Manifest --------------------------------------------------------------
log "Writing MANIFEST.txt"
{
	echo "ai-memory-infra backup"
	echo "timestamp_utc: ${TS}"
	echo "neo4j_image:   ${NEO4J_IMAGE}"
	echo "postgres_db:   ${PG_DB}"
	echo "files:"
	(cd "${STAGE}" && sha256sum postgres.dump neo4j.dump mem0-history.tar.gz)
} >"${STAGE}/MANIFEST.txt"

# --- 5. Upload to Spaces ------------------------------------------------------
log "Uploading to s3://${BACKUP_BUCKET}/${PREFIX}/"
for f in postgres.dump neo4j.dump mem0-history.tar.gz MANIFEST.txt; do
	"${S3[@]}" put "${STAGE}/${f}" "s3://${BACKUP_BUCKET}/${PREFIX}/${f}"
done

# --- 6. Retention: keep the newest $RETAIN backup prefixes --------------------
log "Pruning old backups (keeping newest ${RETAIN})"
mapfile -t PREFIXES < <("${S3[@]}" ls "s3://${BACKUP_BUCKET}/backups/" | awk '{print $NF}' | grep -E '/backups/[0-9TZ]+/$' | sort)
count=${#PREFIXES[@]}
if ((count > RETAIN)); then
	prune=$((count - RETAIN))
	for ((i = 0; i < prune; i++)); do
		echo "  removing ${PREFIXES[i]}"
		"${S3[@]}" del --recursive --force "${PREFIXES[i]}" >/dev/null
	done
fi

log "Backup complete: s3://${BACKUP_BUCKET}/${PREFIX}/"
"${S3[@]}" ls "s3://${BACKUP_BUCKET}/${PREFIX}/"

# Success heartbeat — tells the dead-man's-switch this run finished cleanly.
hc_ping
