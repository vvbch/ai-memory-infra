#!/usr/bin/env bash
# First-time VPS setup for the 4GB Ubuntu droplet provisioned by Terraform.
# Idempotent: safe to re-run. Installs Docker + Compose, sets a host firewall
# (belt-and-suspenders alongside the DO cloud firewall), and brings the prod
# stack up. Run as root (or via sudo) on the droplet:
#
#   ssh root@<droplet_ipv4>
#   git clone <repo> /opt/ai-memory-infra && cd /opt/ai-memory-infra/infra
#   cp .env.example .env && nano .env          # fill in secrets
#   sudo bash ../scripts/bootstrap.sh
#
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/ai-memory-infra}"
INFRA_DIR="${APP_DIR}/infra"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# 1. Base packages -----------------------------------------------------------
log "Updating apt and installing prerequisites"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl gnupg ufw

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

# 5. Bring up the production stack -------------------------------------------
log "Starting the stack (prod overlay)"
cd "${INFRA_DIR}"
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Health check ------------------------------------------------------------
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
