#!/usr/bin/env bash
# First-time VPS setup for the 4GB Ubuntu droplet provisioned by Terraform.
# Idempotent: safe to re-run. Installs Docker + Compose, sets a host firewall
# (belt-and-suspenders alongside the DO cloud firewall), BUILDS the Mem0 API
# image from source, and brings the prod stack up. Run as root (or via sudo)
# on the droplet:
#
#   ssh root@<droplet_ipv4>
#   git clone <repo> /opt/ai-memory-infra && cd /opt/ai-memory-infra/infra
#   cp .env.example .env && nano .env          # fill in secrets
#   sudo bash ../scripts/bootstrap.sh
#
# Why a build step (not just `docker compose pull`): the published
# `mem0/mem0-api-server` image is arm64-only (no amd64 manifest) and omits the
# Neo4j graph extras we need, so we build `mem0-api-server:local` from the
# mem0ai/mem0 `server/` source via infra/mem0-server.Dockerfile (which also
# carries the gpt-5-mini extraction patch — ADR 021). The mem0 source is pinned
# to MEM0_REF for a reproducible build; override any of the MEM0_* vars to bump.
#
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ai-memory-infra}"
INFRA_DIR="${APP_DIR}/infra"

# Mem0 source + image (see header). Pinned for reproducibility; the Dockerfile's
# build-time assert fails loudly if a newer ref restructures the patched code.
MEM0_REPO="${MEM0_REPO:-https://github.com/mem0ai/mem0.git}"
MEM0_REF="${MEM0_REF:-366945965df43aa7084be98d1b5073b62a20b431}"
MEM0_SRC="${MEM0_SRC:-/opt/mem0-src}"
MEM0_IMAGE="${MEM0_IMAGE:-mem0-api-server:local}"
MEM0_DOCKERFILE="${INFRA_DIR}/mem0-server.Dockerfile"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# 1. Base packages -----------------------------------------------------------
log "Updating apt and installing prerequisites"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl gnupg ufw git

# 2. Docker Engine + Compose plugin (official repo) --------------------------
if ! command -v docker >/dev/null 2>&1; then
	log "Installing Docker Engine + Compose plugin"
	install -m 0755 -d /etc/apt/keyrings
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
	chmod a+r /etc/apt/keyrings/docker.gpg
	echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
		>/etc/apt/sources.list.d/docker.list
	apt-get update -y
	apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
	systemctl enable --now docker
else
	log "Docker already installed — skipping"
fi

# 3. Host firewall (DO cloud firewall already restricts; this is defense-in-depth)
log "Configuring UFW (22/80/443)"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 4. Pre-flight: .env must exist ---------------------------------------------
if [[ ! -f "${INFRA_DIR}/.env" ]]; then
	echo "ERROR: ${INFRA_DIR}/.env not found. Copy .env.example to .env and fill it in first." >&2
	exit 1
fi

# 5. Build the Mem0 API image from source ------------------------------------
# Clone (or update) the pinned mem0 source, then build mem0-api-server:local
# from our Dockerfile (context = the source's server/ dir). Idempotent: Docker
# layer-caches the slow pip step, so re-runs are cheap.
if [[ ! -f "${MEM0_DOCKERFILE}" ]]; then
	echo "ERROR: ${MEM0_DOCKERFILE} not found (is the repo checkout complete?)." >&2
	exit 1
fi
log "Fetching mem0 source ${MEM0_REF} into ${MEM0_SRC}"
if [[ ! -d "${MEM0_SRC}/.git" ]]; then
	git clone "${MEM0_REPO}" "${MEM0_SRC}"
fi
git -C "${MEM0_SRC}" fetch --quiet origin
git -C "${MEM0_SRC}" checkout --quiet "${MEM0_REF}"

log "Building ${MEM0_IMAGE} (this carries the ADR 021 gpt-5-mini patch)"
docker build -f "${MEM0_DOCKERFILE}" -t "${MEM0_IMAGE}" "${MEM0_SRC}/server"

# 6. Bring up the production stack -------------------------------------------
log "Starting the stack (prod overlay)"
cd "${INFRA_DIR}"
# Pull only the external base images; mem0-api-server:local is built above and
# can't be pulled (the dashboard image is profiled-off and 404s, so skip both).
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull caddy postgres neo4j
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 7. Health check ------------------------------------------------------------
log "Waiting for the API to answer (up to ~90s for Neo4j to warm up)"
for i in $(seq 1 18); do
	if curl -fsS http://127.0.0.1:8888/docs >/dev/null 2>&1; then
		log "API is up. Stack is running."
		docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
		exit 0
	fi
	sleep 5
done

echo "WARNING: API did not respond in time. Check logs:" >&2
echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml logs mem0 --tail 50" >&2
exit 1
