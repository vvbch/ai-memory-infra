#!/usr/bin/env bash
# Plant the permanent restore-drill canary (ADR 023 §4).
#
# The monthly restore drill (scripts/restore-drill.sh) proves a backup restores
# into WORKING data by asserting a known memory survives the round-trip. For that
# assertion to be deterministic, a permanent, clearly-namespaced "canary" memory
# must exist in the live data so every backup contains it. This script plants it.
#
# Idempotent enough: re-running just adds another canary memory under the same
# user_id — the drill only needs >=1 to exist, so duplicates are harmless. Run
# once after first deploy, and again after any restore that predates the canary.
#
#   sudo bash /opt/ai-memory-infra/scripts/plant-drill-canary.sh
#
# Reads ADMIN_API_KEY from infra/.env; nothing secret is printed.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ai-memory-infra}"
INFRA_DIR="${APP_DIR}/infra"
ENV_FILE="${INFRA_DIR}/.env"
API_URL="${API_URL:-http://127.0.0.1:8888}"
CANARY_USER="${DRILL_CANARY_TAG:-drill-canary}"
CANARY_CODEWORD="${DRILL_CANARY_CODEWORD:-DRILLCANARY7Q4Z9}"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die() {
	echo "ERROR: $*" >&2
	exit 1
}

# Read a single value from .env without sourcing it; strip a trailing CR so a
# Windows/PowerShell-appended line can't corrupt the value (see backup.sh).
envval() {
	local key="$1"
	[[ -f "${ENV_FILE}" ]] || die "${ENV_FILE} not found."
	local line
	line="$(grep -E "^${key}=" "${ENV_FILE}" | head -n1 || true)"
	[[ -n "${line}" ]] || die "${key} is not set in ${ENV_FILE}."
	printf '%s' "${line#*=}" | tr -d '\r' | sed -e 's/[[:space:]]*#.*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

API_KEY="$(envval ADMIN_API_KEY)"

BODY="$(mktemp)"
trap 'rm -f "${BODY}"' EXIT
cat >"${BODY}" <<JSON
{"messages":[{"role":"user","content":"Remember my permanent backup-drill canary codeword: ${CANARY_CODEWORD}. I run restore drills monthly to verify backups."}],"user_id":"${CANARY_USER}"}
JSON

log "Planting drill canary (user_id=${CANARY_USER}) via ${API_URL}/memories"
code="$(curl -fsS -o /dev/null -w '%{http_code}' \
	-H "X-API-Key: ${API_KEY}" \
	-H 'Content-Type: application/json' \
	--data @"${BODY}" \
	"${API_URL}/memories" || true)"
[[ "${code}" == "200" || "${code}" == "201" ]] || die "POST /memories returned HTTP ${code} (expected 200/201)."

log "Confirming the canary is retrievable"
got="$(curl -fsS -H "X-API-Key: ${API_KEY}" "${API_URL}/memories?user_id=${CANARY_USER}" || true)"
echo "${got}" | grep -qi "${CANARY_USER}" \
	|| die "canary not found on GET /memories?user_id=${CANARY_USER} (extraction may have stored 0 memories — check OpenAI model access)."

log "Drill canary planted. Take a fresh backup so the next backup contains it:"
echo "    sudo systemctl start ai-memory-backup.service   # or: bash scripts/backup.sh"
