# Convenience wrappers for the infra stack (Unix/macOS/WSL; on native Windows
# run the underlying `docker compose` / `terraform` commands shown here).
# Secrets come from infra/.env — never commit it.

COMPOSE      := docker compose
PROD         := -f docker-compose.yml -f docker-compose.prod.yml
TF           := terraform -chdir=terraform

.DEFAULT_GOAL := help

.PHONY: help
help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ---- Local dev ------------------------------------------------------------
.PHONY: up
up: ## Start the dev stack
	$(COMPOSE) up -d

.PHONY: down
down: ## Stop the dev stack
	$(COMPOSE) down

.PHONY: logs
logs: ## Tail logs (make logs svc=mem0)
	$(COMPOSE) logs -f $(svc)

.PHONY: ps
ps: ## Show stack status
	$(COMPOSE) ps

# ---- Production (on the VPS) ----------------------------------------------
.PHONY: prod-up
prod-up: ## Start the prod stack (base + prod overlay)
	$(COMPOSE) $(PROD) up -d

.PHONY: prod-pull
prod-pull: ## Pull latest prod images
	$(COMPOSE) $(PROD) pull

.PHONY: deploy
deploy: ## Pull + restart prod stack (used by CD)
	$(COMPOSE) $(PROD) pull
	$(COMPOSE) $(PROD) up -d

.PHONY: deploy-obs
deploy-obs: ## Pull + restart prod stack with observability profile
	$(COMPOSE) $(PROD) -f docker-compose.observability.yml --profile observability pull
	$(COMPOSE) $(PROD) -f docker-compose.observability.yml --profile observability up -d

.PHONY: prod-up-obs
prod-up-obs: ## Start prod stack + observability profile
	$(COMPOSE) $(PROD) -f docker-compose.observability.yml --profile observability up -d

.PHONY: health
health: ## Hit the local API health/docs endpoint
	curl -fsS http://127.0.0.1:8888/docs >/dev/null && echo "OK" || (echo "DOWN"; exit 1)

# ---- Terraform ------------------------------------------------------------
.PHONY: tf-init
tf-init: ## terraform init
	$(TF) init

.PHONY: tf-fmt
tf-fmt: ## terraform fmt (check)
	$(TF) fmt -check -recursive

.PHONY: tf-plan
tf-plan: ## terraform plan
	$(TF) plan

.PHONY: tf-apply
tf-apply: ## terraform apply (uses your cloud creds — review the plan first)
	$(TF) apply

.PHONY: tf-plan-destroy
tf-plan-destroy: ## Preview a full teardown (read-only; destroys nothing)
	$(TF) plan -destroy

.PHONY: teardown
teardown: ## Guided, confirmed teardown of all cloud infra (see docs/decommission.md)
	python $(ROOT)/scripts/teardown.py

# ---- Repo integrity: Drive-sync guard (Tenet 11 / ADR 015) ---------------
# Scripts live at the repo root (../scripts). On Unix/WSL PowerShell is `pwsh`;
# on native Windows (no make) run the .ps1 directly — see docs/runbook.md.
ROOT := ..
PWSH := pwsh -NoProfile -ExecutionPolicy Bypass -File

.PHONY: repo-health
repo-health: ## Full Drive-sync integrity check (fsck + conflict + lock + ahead/behind)
	$(PWSH) $(ROOT)/scripts/check-repo-health.ps1

.PHONY: repo-health-fast
repo-health-fast: ## Fast subset (conflicted-copy + stale index.lock only)
	$(PWSH) $(ROOT)/scripts/check-repo-health.ps1 -Fast

.PHONY: install-hooks
install-hooks: ## Copy the pre-commit integrity hook into the repo(s) (re-run after re-clone)
	$(PWSH) $(ROOT)/scripts/install-hooks.ps1

.PHONY: register-health-task
register-health-task: ## Register the daily Windows scheduled integrity check
	$(PWSH) $(ROOT)/scripts/register-repo-health-task.ps1

# ---- Secret helpers -------------------------------------------------------
.PHONY: gen-jwt
gen-jwt: ## Generate a JWT_SECRET
	openssl rand -base64 48

.PHONY: gen-basic-auth
gen-basic-auth: ## Generate a Caddy basic-auth hash (prompts for password)
	docker run --rm caddy:2-alpine caddy hash-password
