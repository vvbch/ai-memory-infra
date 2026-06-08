#!/usr/bin/env python3
"""scaffold.py - lay down the ai-memory-infra repo tree (cross-platform).

Idempotent: skips files that already exist, so it won't clobber the LICENSE
that `gh repo create --license apache-2.0` writes, nor the real files
(AGENTS.md, ADRs, etc.) you may have placed first.

Run from inside the repo root:  python scaffold.py
Pure stdlib. Works on macOS, Windows, Linux. No shell, no make required.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

ROOT = Path.cwd()


def write(rel: str, body: str) -> None:
    """Create file with content, only if absent."""
    p = ROOT / rel
    if p.exists():
        print(f"  skip   {rel} (exists)")
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    if rel.endswith(".sh") and os.name == "posix":
        p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"  create {rel}")


def stub(rel: str, comment: str = "TODO") -> None:
    """Create a phase-tagged placeholder, only if absent."""
    bodies = {
        ".py": f"# {comment}\n",
        ".sh": f"#!/usr/bin/env bash\n# {comment}\nset -euo pipefail\n",
        ".md": f"# {comment}\n\n> TODO\n",
        ".json": "{}\n",
    }
    ext = Path(rel).suffix
    write(rel, bodies.get(ext, f"# {comment}\n"))


# ---- root files with real content -----------------------------------------

GITIGNORE = """\
# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/

# Secrets / env - NEVER commit real values
.env
*.env
!.env.example
!infra/.env.example
*.pem
id_ed25519*
id_rsa*

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
!*.tfvars.example
crash.log

# Node / extension build
node_modules/
extension/build/

# OS / editor
.DS_Store
.idea/
.vscode/
"""

ENV_EXAMPLE = """\
# ---- Domain & TLS -------------------------------------------------
DOMAIN=example.com                      # set in Phase 0 step 2
ACME_EMAIL=you@example.com              # Let's Encrypt registration

# ---- Service ports (host side; resolve REST vs MCP split in Phase 1)
MEM0_API_PORT=8888
MEM0_MCP_PORT=8765
DASH_PORT=3000
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
GRAFANA_PORT=3001
PROMETHEUS_PORT=9090

# ---- Extraction LLM: DeepSeek V4 Flash (OpenAI-compatible) --------
# Mem0 reads OPENAI_* even when pointed at DeepSeek. The var name is
# OPENAI_BASE_URL (confirm against your Mem0 server version at deploy).
OPENAI_API_KEY=sk-REPLACE_ME           # DeepSeek key from platform.deepseek.com
OPENAI_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat                # confirm exact id via GET /v1/models

# ---- Datastores ---------------------------------------------------
POSTGRES_USER=mem0
POSTGRES_PASSWORD=REPLACE_ME
POSTGRES_DB=mem0
NEO4J_AUTH=neo4j/REPLACE_ME            # format: user/password

# ---- API auth (Phase 1 security) ----------------------------------
JWT_SECRET=REPLACE_ME
ADMIN_API_KEY=REPLACE_ME

# ---- Admin UI basic auth (Caddy) ----------------------------------
BASIC_AUTH_USER=admin
BASIC_AUTH_HASH=REPLACE_ME             # `caddy hash-password`
"""

PYPROJECT = """\
[project]
name = "ai-memory-infra"
version = "0.0.1"
description = "Self-hosted cross-platform AI memory infrastructure with a knowledge graph"
requires-python = ">=3.12"
license = { text = "Apache-2.0" }
dependencies = [
    "mem0ai>=0.1.0",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "neo4j>=5.20",
    "psycopg[binary]>=3.2",
    "click>=8.1",
    "httpx>=0.27",
    "prometheus-client>=0.20",
    "python-jose[cryptography]>=3.3",
    "pydantic>=2.7",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.6",
    "mypy>=1.11",
    "pytest>=8.3",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.24",
    "respx>=0.21",
]

[tool.ruff]
line-length = 100
target-version = "py312"
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
addopts = "-ra --cov=src --cov-report=term-missing --cov-fail-under=80"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = ["*/cli.py", "*/__init__.py"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
"""

# Makefile = Unix convenience only (tenet 3: not a hard dep; Windows runs the
# underlying commands directly). Recipe lines MUST start with a tab.
MAKEFILE = "\n".join([
    ".PHONY: setup lint type test cov up down deploy backup eval",
    "setup:        ## venv + dev deps",
    "\tpython -m venv .venv && . .venv/bin/activate && pip install -e \".[dev]\"",
    "lint:",
    "\truff check src tests",
    "type:",
    "\tmypy src",
    "test:",
    "\tpytest",
    "cov:",
    "\tpytest --cov-report=html",
    "up:           ## local dev stack",
    "\tcd infra && docker compose up -d",
    "down:",
    "\tcd infra && docker compose down",
    "deploy:",
    "\t$(MAKE) -C infra deploy",
    "backup:",
    "\tbash scripts/backup.sh",
    "eval:",
    "\tpython -m eval run --suite all",
    "",
])

README = """\
# ai-memory-infra

Self-hosted, cross-platform **AI memory infrastructure** with a knowledge graph.
A persistent memory layer under Claude, ChatGPT, Gemini, and DeepSeek - shared
context across every LLM, on any device.

## What it is

- **Memory layer**: Mem0 REST API over PostgreSQL/pgvector, with a local MCP
  proxy for Claude Code, Cursor, and VS Code (ADR 025).
- **Knowledge graph**: Neo4j, dual namespace - Mem0's auto-managed semantic
  graph + LifeGraph (people, ventures, skills, decisions, milestones).
- **Reach**: Chrome extension (desktop / ChromeOS) + local MCP proxy for
  Claude Code, Cursor, and VS Code. Claude mobile needs a later remote HTTP MCP
  endpoint. Android extension coverage is best-effort only (see ADR 004). Native
  LLM UIs unchanged.
- **Models**: OpenAI `gpt-5-mini` extraction + `text-embedding-3-small`
  embeddings (single provider, swappable; see ADR 013).

## Quick start

```bash
gh repo clone <you>/ai-memory-infra && cd ai-memory-infra
python scaffold.py                 # lay down structure (idempotent)
cp infra/.env.example infra/.env   # fill in secrets
```

## Engineering

Terraform IaC, GitHub Actions CI/CD, TDD (80%+ coverage), eval suite with
guardrail tests, Prometheus + Grafana, ADRs in `docs/decisions/`. Tenets in
`docs/tenets.md`. Canonical agent context in `AGENTS.md`.

## License

Apache-2.0.
"""


def main() -> None:
    print("==> root files")
    write(".gitignore", GITIGNORE)
    write("pyproject.toml", PYPROJECT)
    write("Makefile", MAKEFILE)
    write("README.md", README)
    write("infra/.env.example", ENV_EXAMPLE)

    print("==> CI/CD workflow stubs")
    for w in ("ci", "cd", "backup-verify", "eval-suite", "docker-build"):
        stub(f".github/workflows/{w}.yml", f"{w} workflow")

    print("==> infra stubs (real content in Phase 1)")
    stub("infra/docker-compose.yml", "dev stack - Phase 1")
    stub("infra/docker-compose.prod.yml", "prod overrides - Phase 1")
    stub("infra/Caddyfile", "reverse proxy - Phase 1")
    stub("infra/Makefile", "infra targets (Unix convenience) - Phase 1")
    for t in ("main", "variables", "outputs", "backend"):
        stub(f"infra/terraform/{t}.tf", f"terraform {t} - Phase 1")
    stub("infra/terraform/terraform.tfvars.example", "tfvars template - Phase 1")

    print("==> python package stubs")
    pkgs = {
        "migration": ["import_md", "import_gdrive", "categorizer", "dedup", "cli"],
        "life_graph": ["schema", "seed", "ingest", "queries", "cli"],
        "eval": ["retrieval_eval", "extraction_eval", "categorization_eval",
                 "guardrails", "runners", "reporters", "cli"],
        "observability": ["metrics", "drift_detector", "alerts"],
        "health": ["checker"],
    }
    phase = {"migration": 5, "life_graph": 6, "eval": 7, "observability": 8, "health": 1}
    for pkg, mods in pkgs.items():
        stub(f"src/{pkg}/__init__.py", "")
        for m in mods:
            stub(f"src/{pkg}/{m}.py", f"{pkg}.{m} - Phase {phase[pkg]}")
    for g in ("retrieval_pairs", "extraction_gold", "categorization_gold"):
        stub(f"src/eval/gold_standard/{g}.json")
    for d in ("memory_ops", "knowledge_growth"):
        stub(f"src/observability/dashboards/{d}.json")

    print("==> test stubs (tests written FIRST per phase - TDD)")
    stub("tests/conftest.py", "shared fixtures: test mem0 client, test neo4j, sample .md")
    tests = {
        "test_migration": [
            "test_import_md",
            "test_categorizer",
            "test_dedup",
            "test_e2e_migration",
        ],
        "test_life_graph": ["test_schema", "test_seed", "test_queries"],
        "test_eval": ["test_retrieval_eval", "test_extraction_eval", "test_reporters",
                      "test_guardrails", "test_e2e_eval"],
        "test_observability": ["test_metrics", "test_drift_detector"],
        "test_health": ["test_checker"],
    }
    for d, mods in tests.items():
        for m in mods:
            stub(f"tests/{d}/{m}.py", "TDD")

    print("==> scripts")
    stub("scripts/bootstrap.sh", "first-time VPS setup: docker, ufw, deploy - Phase 1")
    stub("scripts/backup.sh", "pg_dump + neo4j-admin dump -> object storage - Phase 2")
    stub("scripts/restore.sh", "download + restore + verify - Phase 2")
    stub("scripts/setup_accounts.py", "interactive: DO + DeepSeek + domain + SSH - Phase 0 step 2")

    print("==> docs + ADRs (rich ADRs already present are kept)")
    stub("docs/architecture.md", "Architecture")
    stub("docs/setup.md", "Setup Guide")
    stub("docs/runbook.md", "Operational Runbook")
    adrs = [
        ("001-mem0-over-alternatives", "Mem0 over alternatives"),
        ("002-deepseek-for-extraction", "DeepSeek V4 Flash for extraction"),
        ("003-soft-separation-over-hard-isolation", "Soft separation via metadata"),
        ("004-chromeos-for-mobile", "ChromeOS for mobile"),
        ("005-neo4j-dual-namespace-lifegraph", "Neo4j dual namespace + LifeGraph"),
        ("006-two-repo-separation", "Public platform vs private domain repos"),
        ("007-eval-framework-design", "Evaluation framework design"),
        ("008-observability-stack-choice", "Prometheus + Grafana"),
        ("009-security-guardrails-architecture", "Security guardrails architecture"),
        ("010-portability-and-versioning", "Portability + everything-versioned tenets"),
    ]
    for slug, title in adrs:
        stub(f"docs/decisions/{slug}.md", f"ADR {slug.split('-')[0]}: {title}")

    print("==> extension + editor dirs")
    stub("extension/README.md", "OpenMemory fork - what changed, how to build (Phase 3)")
    (ROOT / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
    (ROOT / "extension" / "src").mkdir(parents=True, exist_ok=True)

    print("\nDone. Next:")
    print("  git add -A && git commit -m 'chore: scaffold structure (Phase 0)'")
    print("  git push -u origin main")


if __name__ == "__main__":
    main()
