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

# ---- Secret helpers -------------------------------------------------------
.PHONY: gen-jwt
gen-jwt: ## Generate a JWT_SECRET
	openssl rand -base64 48

.PHONY: gen-basic-auth
gen-basic-auth: ## Generate a Caddy basic-auth hash (prompts for password)
	docker run --rm caddy:2-alpine caddy hash-password
