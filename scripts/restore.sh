#!/usr/bin/env bash
# Phase 2 restore — pull a backup from DigitalOcean Spaces and restore all three
# datastores. DESTRUCTIVE: it overwrites the live Postgres DB, Neo4j graph, and
# mem0 SQLite history with the snapshot.
#
# Usage (on the droplet):
#   sudo bash /opt/ai-memory-infra/scripts/restore.sh            # newest backup, interactive confirm
#   sudo bash /opt/ai-memory-infra/scripts/restore.sh 20260608T101500Z
#   sudo FORCE=1 bash /opt/ai-memory-infra/scripts/restore.sh    # skip the typed confirmation
#
# Credentials + target come from infra/.env (same vars as backup.sh).
# Nothing secret is ever printed.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ai-memory-infra}"
INFRA_DIR="${APP_DIR}/infra"
ENV_FILE="${INFRA_DIR}/.env"
PROJECT="${COMPOSE_PROJECT_NAME:-ai-memory-infra}"
NEO4J_IMAGE="${NEO4J_IMAGE:-neo4j:5.26.4}"
NEO4J_DB="${NEO4J_DB:-neo4j}"
WHICH="${1:-latest}"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die() {
	echo "ERROR: $*" >&2
	exit 1
}

envval() {
	local key="$1"
	[[ -f "${ENV_FILE}" ]] || die "${ENV_FILE} not found."
	local line
	line="$(grep -E "^${key}=" "${ENV_FILE}" | head -n1 || true)"
	[[ -n "${line}" ]] || die "${key} is not set in ${ENV_FILE}."
	printf '%s' "${line#*=}" | sed -e 's/[[:space:]]*#.*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

cd "${INFRA_DIR}" || die "cannot cd to ${INFRA_DIR}"

BACKUP_BUCKET="$(envval BACKUP_BUCKET)"
SPACES_REGION="$(envval SPACES_REGION)"
SPACES_ACCESS_KEY="$(envval SPACES_ACCESS_KEY)"
SPACES_SECRET_KEY="$(envval SPACES_SECRET_KEY)"
PG_USER="$(envval POSTGRES_USER)"
PG_DB="$(envval POSTGRES_DB)"
PG_PW="$(envval POSTGRES_PASSWORD)"

SPACES_HOST="${SPACES_REGION}.digitaloceanspaces.com"
S3=(s3cmd
	"--access_key=${SPACES_ACCESS_KEY}"
	"--secret_key=${SPACES_SECRET_KEY}"
	"--host=${SPACES_HOST}"
	"--host-bucket=%(bucket)s.${SPACES_HOST}"
	--no-progress)

command -v s3cmd >/dev/null 2>&1 || die "s3cmd not installed (run backup.sh once, or apt-get install s3cmd)."

# --- Resolve which backup prefix to restore -----------------------------------
if [[ "${WHICH}" == "latest" ]]; then
	TS="$("${S3[@]}" ls "s3://${BACKUP_BUCKET}/backups/" | awk '{print $NF}' | grep -oE '[0-9]{8}T[0-9]{6}Z' | sort | tail -n1 || true)"
	[[ -n "${TS}" ]] || die "no backups found in s3://${BACKUP_BUCKET}/backups/"
else
	TS="${WHICH}"
fi
PREFIX="backups/${TS}"
log "Restoring backup ${TS} from s3://${BACKUP_BUCKET}/${PREFIX}/"

# --- Download + verify checksums ----------------------------------------------
STAGE="$(mktemp -d)"
trap 'rm -rf "${STAGE}"' EXIT
for f in postgres.dump neo4j.dump mem0-history.tar.gz MANIFEST.txt; do
	"${S3[@]}" get --force "s3://${BACKUP_BUCKET}/${PREFIX}/${f}" "${STAGE}/${f}" >/dev/null \
		|| die "could not download ${f} (is ${TS} a complete backup?)"
done
log "Verifying checksums against MANIFEST.txt"
(cd "${STAGE}" && grep -E '\.(dump|tar\.gz)$' MANIFEST.txt | sha256sum -c -) || die "checksum mismatch — refusing to restore."

# --- Confirm (destructive) ----------------------------------------------------
if [[ "${FORCE:-0}" != "1" ]]; then
	echo
	echo "This will OVERWRITE the live Postgres DB, Neo4j graph, and mem0 history"
	echo "on this droplet with the ${TS} snapshot. This cannot be undone."
	read -r -p 'Type RESTORE to proceed: ' ans
	[[ "${ans}" == "RESTORE" ]] || die "aborted."
fi

# --- 1. Stop the app so nothing writes mid-restore ----------------------------
log "Stopping mem0 (drops its DB connections)"
"${COMPOSE[@]}" stop mem0

# --- 2. Postgres restore (drop + recreate objects) ----------------------------
log "Restoring Postgres '${PG_DB}'"
"${COMPOSE[@]}" exec -T -e PGPASSWORD="${PG_PW}" postgres \
	pg_restore --clean --if-exists --no-owner -U "${PG_USER}" -d "${PG_DB}" <"${STAGE}/postgres.dump"

# --- 3. mem0 SQLite history restore (wipe volume, untar) ----------------------
log "Restoring mem0 SQLite history volume"
docker run --rm \
	-v "${PROJECT}_mem0_history:/history" \
	-v "${STAGE}:/in:ro" \
	alpine:3 \
	sh -c "rm -rf /history/* /history/.[!.]* /history/..?* 2>/dev/null || true; tar xzf /in/mem0-history.tar.gz -C /history"

# --- 4. Neo4j restore (OFFLINE load, then fix ownership) -----------------------
log "Stopping neo4j for an offline load"
"${COMPOSE[@]}" stop neo4j
# Same mechanics as backup.sh: /data must be read-write (root entrypoint chowns it,
# then drops to the neo4j user), and the stage dir must be readable by that user.
# Loading as the neo4j user means the restored store files are correctly owned.
chmod 777 "${STAGE}"
docker run --rm \
	-v "${PROJECT}_neo4j_data:/data" \
	-v "${STAGE}:/backups" \
	"${NEO4J_IMAGE}" \
	neo4j-admin database load "${NEO4J_DB}" --from-path=/backups --overwrite-destination=true
log "Restarting neo4j"
"${COMPOSE[@]}" start neo4j

# --- 5. Bring mem0 back -------------------------------------------------------
log "Starting mem0"
"${COMPOSE[@]}" start mem0

log "Restore complete from ${TS}. Give Neo4j ~30s to warm up, then verify with a /search."
