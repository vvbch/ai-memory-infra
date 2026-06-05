.PHONY: setup lint type test cov up down deploy backup eval
setup:        ## venv + dev deps
	python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
lint:
	ruff check src tests
type:
	mypy src
test:
	pytest
cov:
	pytest --cov-report=html
up:           ## local dev stack
	cd infra && docker compose up -d
down:
	cd infra && docker compose down
deploy:
	$(MAKE) -C infra deploy
backup:
	bash scripts/backup.sh
eval:
	python -m eval run --suite all
