# Personal AI Memory Infrastructure — Complete Setup Prompt

> **⚠️ HISTORICAL SNAPSHOT (the original Day-0 bootstrap prompt) — NOT current
> truth.** Several decisions below were superseded by later ADRs and should not be
> treated as the live design: extraction is OpenAI `gpt-5-mini`, not DeepSeek
> (ADR 013); Neo4j is reserved for LifeGraph and is **not** a live Mem0
> "dual namespace" (ADR 032). For current state read `docs/architecture.md`,
> `AGENTS.md`, and `docs/planning/STATUS.md`. Kept as-is for provenance.
>
> **How to use**: Paste everything below the line into a new Claude Code session.
> Self-contained. The new session needs nothing else. No pre-requisites — everything including VPS provisioning, DNS, API keys, and GitHub repo is part of the execution plan.

---

## COPY FROM HERE ↓

I need your help building my personal AI memory infrastructure — a self-hosted, cross-platform persistent memory layer with a knowledge graph. This is also my portfolio showcase project, so it must follow industry-standard engineering practices from day one: Infrastructure as Code, CI/CD, TDD, proper repo structure, documentation.

I was SDE3 at Amazon for 3 years, then SDM/EM for 10+. Skip basics. Be concise. Give me executable files and commands.

---

### WHO I AM

- **Chandra**, Senior Manager (L7) at Amazon Bangalore, leaving July 1, 2026
- Former SDE3 — comfortable with Docker, Terraform, CI/CD, Python, databases
- Based in Bangalore, India (matters for VPS datacenter selection)
- Devices: ExpertBook laptop (dev machine), ASUS Chromebook CX1405 (mobile AI workstation), Android/iOS phone, future Alienware 16 Aurora desktop
- Active LLMs: Claude Pro, ChatGPT, Gemini, DeepSeek — all via native web interfaces (NO API costs for chat)

### WHAT THIS SUPPORTS

Four interconnected ventures:
1. **Algorithmic trading firm (LLP)** — ETF pledge + Iron Condor on NIFTY/BANKNIFTY. Co-founder: cousin Vijaya. Tag: `trading_firm`
2. **Social media / content firm** — YouTube monetization. With Vijaya + another cousin. Tag: `social_media`
3. **RIA (Registered Investment Advisor)** — future monetization. Tag: `ria`
4. **Career / personal** — job search, Germany/Australia migration, PhD (Andhra Univ, Dec 2026). Tags: `personal`, `career`, `migration`

---

### ARCHITECTURE OVERVIEW

```
DEVICES (no change to daily workflow — native LLM interfaces)
├── Desktop/Chromebook (any Chromium browser)
│   └── Claude.ai, ChatGPT, Gemini, DeepSeek + OpenMemory Chrome extension
│       Extension captures + injects memory automatically. Cost: ₹0.
│
├── Android (Kiwi Browser supports Chrome extensions)
│   └── Same as desktop — full memory coverage
│
├── iOS
│   └── Claude app only after a future remote HTTP MCP endpoint
│       Non-Claude LLMs on iOS = their own siloed memory. Known gap.
│
├── Claude Code (terminal)
│   └── Local ai-memory MCP proxy for auto-capture + recall
│
└── Any future tool (Hermes Agent, OpenClaw, custom scripts)
    └── REST API: POST/GET to memory.{domain}

CLOUD (VPS — Bangalore/Mumbai region)
├── Caddy reverse proxy (auto-HTTPS)
│   ├── memory.{domain}  → Mem0 API (:8888)
│   ├── dash.{domain}    → Mem0 Dashboard (:3000)
│   ├── graph.{domain}   → Neo4j Browser (:7474)
│   └── monitor.{domain} → Grafana (:3001)
│
├── Docker Compose:
│   ├── mem0-api     (FastAPI — REST)
│   ├── postgres     (PostgreSQL 16 + pgvector)
│   ├── neo4j        (Knowledge graph — dual namespace)
│   │   ├── Mem0 namespace: :Entity, :Memory, :Relationship (auto-managed)
│   │   └── LifeGraph namespace: :Person, :Venture, :Skill, :Decision, :Milestone (POC, public)
│   ├── mem0-dash    (Next.js dashboard)
│   ├── prometheus   (Metrics collection — retrieval latency, extraction rate, system health)
│   └── grafana      (Dashboards — memory ops, knowledge growth, drift alerts)
│
└── Daily backup: pg_dump + neo4j-admin dump → cloud storage

LLM PROVIDERS (zero lock-in)
├── DeepSeek V4 Flash for fact extraction ($0.14/M tokens — near-free)
├── All chat via native web UIs — ₹0 API cost
└── Future: Ollama on Alienware for fully local extraction
```

### KEY DESIGN DECISIONS

1. **Native LLM interfaces, not a custom chat UI.** Memory wraps around them via Chrome extension + MCP. No API costs for conversation.
2. **DeepSeek V4 Flash for extraction.** OpenAI-compatible API. $0.14/M input. At 50 interactions/day ≈ ₹30/month.
3. **Soft separation via metadata categories.** All memories in one pool, tagged by venture. Cross-domain queries work naturally.
4. **Neo4j dual namespace.** Mem0's auto-managed knowledge graph + LifeGraph (personal professional knowledge graph). Different node labels, same instance. Cross-namespace queries JOIN personal memories with professional entities and milestones.
5. **Two-repo separation.** The public repo (`ai-memory-infra`) is the platform + LifeGraph POC. Domain-specific code (trading firm, social media, RIA) lives in separate PRIVATE repos that plug into this infrastructure via REST API. The public repo demonstrates capability without leaking firm IP. Private repos are LLP-owned assets.
6. **Graceful degradation.** VPS down = all LLMs still work normally with their own memory. Zero dependency. When VPS recovers, enrichment resumes.
7. **Docker Compose as deployment unit.** Runs on any VPS, any local machine. Zero vendor lock-in.

---

### GITHUB REPO STRUCTURE

This is a portfolio project. The repo must look like production-grade infrastructure that a senior engineer built. Industry standard. Not a hobby script dump.

```
ai-memory-infra/
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint + test on every PR
│       ├── cd.yml                    # Deploy to VPS on push to main
│       ├── backup-verify.yml         # Weekly: restore backup to temp DB, verify integrity
│       ├── eval-suite.yml            # Weekly: run full eval suite, post results to PR/dashboard
│       └── docker-build.yml          # Build + push custom images to GHCR
│
├── infra/
│   ├── terraform/                    # IaC for VPS provisioning
│   │   ├── main.tf                   # DigitalOcean/AWS droplet + firewall + DNS
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars.example
│   │   └── backend.tf                # Remote state in S3/DO Spaces
│   ├── docker-compose.yml            # Local dev stack
│   ├── docker-compose.prod.yml       # Production overrides (resource limits, restart policies)
│   ├── Caddyfile                     # Reverse proxy config
│   ├── .env.example                  # Template — never commit real secrets
│   └── Makefile                      # Common commands: make up, make deploy, make backup, make test
│
├── src/
│   ├── migration/                    # Context file migration pipeline
│   │   ├── __init__.py
│   │   ├── import_md.py              # Parse .md files → Mem0 memories
│   │   ├── import_gdrive.py          # Download + parse Google Drive docs
│   │   ├── categorizer.py            # Auto-classify into venture categories
│   │   ├── dedup.py                  # Deduplication logic
│   │   └── cli.py                    # Click CLI: `python -m migration import --source ./docs/`
│   │
│   ├── life_graph/                   # LifeGraph — personal knowledge graph POC
│   │   ├── __init__.py
│   │   ├── schema.py                 # Neo4j node/edge type definitions (:Person, :Venture, :Skill, :Decision, :Milestone)
│   │   ├── seed.py                   # Initial graph: people, ventures, skills, goals, timelines
│   │   ├── ingest.py                 # Add new entities, decisions, milestones from Mem0 memories
│   │   ├── queries.py                # Common Cypher query library (e.g., "who connects to what venture")
│   │   └── cli.py                    # Click CLI: `python -m life_graph seed / query / ingest`
│   │
│   └── health/                       # Health check + monitoring
│       ├── __init__.py
│       └── checker.py                # Verify all services, memory CRUD, graph connectivity
│
│   ├── eval/                         # Evaluation framework (THE key differentiator)
│   │   ├── __init__.py
│   │   ├── retrieval_eval.py         # Memory retrieval quality: precision@k, recall, MRR
│   │   ├── extraction_eval.py        # Fact extraction accuracy: DeepSeek vs GPT-4o-mini vs Gemini Flash
│   │   ├── categorization_eval.py    # Auto-categorizer precision/recall per venture category
│   │   ├── guardrails.py             # Security guardrail tests: PII filter, injection defense, secret detection
│   │   ├── gold_standard/            # Hand-labeled test datasets
│   │   │   ├── retrieval_pairs.json  # 50+ query → expected-memories pairs
│   │   │   ├── extraction_gold.json  # 30+ conversations → expected-facts pairs
│   │   │   └── categorization_gold.json  # 50+ facts → expected-category pairs
│   │   ├── runners.py                # Eval orchestrator: run all suites, aggregate scores
│   │   ├── reporters.py              # Generate eval reports (Markdown + JSON for CI)
│   │   └── cli.py                    # Click CLI: `python -m eval run --suite all`
│   │
│   └── observability/                # Production monitoring
│       ├── __init__.py
│       ├── metrics.py                # Prometheus metrics: retrieval latency, extraction rate, memory count
│       ├── drift_detector.py         # Weekly: sample extractions, score against gold standard, alert on regression
│       ├── dashboards/               # Grafana dashboard JSON exports
│       │   ├── memory_ops.json       # Retrieval latency p50/p95/p99, write throughput, error rate
│       │   └── knowledge_growth.json # Memories per category over time, dedup rate, graph stats
│       └── alerts.py                 # Alert rules: p95 > 500ms, extraction quality < 85%, VPS disk > 80%
│
├── tests/                            # TDD — tests written BEFORE implementation
│   ├── conftest.py                   # Shared fixtures: test DB, test Mem0 client
│   ├── test_migration/
│   │   ├── test_import_md.py         # Unit: .md parsing, section splitting, category tagging
│   │   ├── test_categorizer.py       # Unit: venture category classification
│   │   ├── test_dedup.py             # Unit: dedup logic
│   │   └── test_e2e_migration.py     # Integration: full pipeline against test Mem0 instance
│   ├── test_life_graph/
│   │   ├── test_schema.py            # Unit: graph schema validation
│   │   ├── test_seed.py              # Integration: seed graph + verify structure
│   │   └── test_queries.py           # Integration: Cypher query correctness
│   └── test_health/
│       └── test_checker.py           # Integration: service health verification
│   ├── test_eval/
│   │   ├── test_retrieval_eval.py    # Unit: retrieval scoring logic
│   │   ├── test_extraction_eval.py   # Unit: extraction comparison logic
│   │   ├── test_reporters.py         # Unit: report generation
│   │   ├── test_guardrails.py        # Unit+Integration: PII filter, injection defense, hallucination detection
│   │   └── test_e2e_eval.py          # Integration: full eval suite against test stack
│   └── test_observability/
│       ├── test_metrics.py           # Unit: metric emission
│       └── test_drift_detector.py    # Unit: drift detection logic
│
├── extension/                        # Forked OpenMemory Chrome extension
│   ├── README.md                     # Fork notes, what was changed, how to build
│   ├── src/                          # Modified source pointing to self-hosted API
│   └── build/                        # Build output (gitignored)
│
├── scripts/
│   ├── bootstrap.sh                  # One-shot VPS setup: Docker, firewall, deploy
│   ├── backup.sh                     # pg_dump + neo4j dump + upload to cloud storage
│   ├── restore.sh                    # Download backup + restore (tested in CI)
│   └── setup-accounts.sh             # Interactive: create DigitalOcean, DeepSeek, domain accounts
│
├── docs/
│   ├── architecture.md               # System architecture with diagrams
│   ├── setup.md                      # Step-by-step setup guide
│   ├── runbook.md                    # Operational: backup, restore, scaling, troubleshooting
│   ├── decisions/                    # ADRs (Architecture Decision Records)
│   │   ├── 001-mem0-over-alternatives.md
│   │   ├── 002-deepseek-for-extraction.md
│   │   ├── 003-soft-separation-over-hard-isolation.md
│   │   ├── 004-chromeos-for-mobile.md
│   │   ├── 005-neo4j-dual-namespace-lifegraph.md
│   │   ├── 006-two-repo-separation.md
│   │   ├── 007-eval-framework-design.md
│   │   ├── 008-observability-stack-choice.md
│   │   └── 009-security-guardrails-architecture.md
│   └── diagrams/
│       └── (Mermaid or SVG architecture diagrams)
│
├── README.md                         # Project overview, quick start, architecture diagram, interview talking points
├── LICENSE                           # Apache 2.0
├── pyproject.toml                    # Python project config (ruff, pytest, dependencies)
├── Makefile                          # Top-level: make setup, make test, make deploy, make backup
└── .gitignore
```

---

### ENGINEERING PRACTICES (NON-NEGOTIABLE)

#### Infrastructure as Code
- **Terraform** for VPS provisioning (droplet, firewall rules, DNS records, cloud storage bucket for backups)
- No manual DigitalOcean/AWS console clicks after initial API token creation
- `terraform plan` → `terraform apply` for all infra changes
- Remote state backend (DO Spaces or S3) so state isn't local-only

#### CI/CD (GitHub Actions)
- **CI on every PR**: ruff lint, mypy type check, pytest (unit + integration against docker-compose test stack)
- **CD on push to main**: SSH into VPS, pull latest, `docker compose -f docker-compose.prod.yml up -d --build`, run health check, rollback on failure
- **Weekly backup verification**: restore latest backup to ephemeral DB, run integrity checks, alert on failure
- **Docker image builds**: custom images pushed to GitHub Container Registry (GHCR)

#### TDD
- Tests written BEFORE implementation for migration pipeline and market graph
- Unit tests: pure logic (parsing, categorization, dedup, schema validation)
- Integration tests: full pipeline against test Docker Compose stack (spun up in CI)
- Fixtures: conftest.py with test Mem0 client, test Neo4j connection, sample .md files
- Coverage target: 80%+ on src/

#### Evaluation Framework — Accuracy & Correctness
- Gold-standard test datasets: hand-labeled query→memory pairs, conversation→facts pairs, fact→category pairs
- Three eval suites measuring **accuracy** and **correctness**:
  - Retrieval correctness: precision@k, recall, MRR — does the system return the RIGHT memories?
  - Extraction accuracy: cross-LLM comparison — does the system extract CORRECT facts from conversations?
  - Categorization accuracy: per-category precision/recall — does the system classify facts into the RIGHT venture?
- **Guardrail eval**: test that PII/secret patterns are correctly filtered, that hallucinated facts are flagged, that dedup correctly identifies duplicates vs near-duplicates
- Runs weekly in CI + on-demand. Blocks deploys if metrics regress below baseline.
- Cost-vs-quality analysis: quantitative comparison of DeepSeek V4 Flash vs GPT-4o-mini vs Gemini Flash
- This is the single most important differentiator for interview credibility.

#### Production Observability
- Prometheus metrics: retrieval latency histograms, write/search counters, memory gauges by category
- Grafana dashboards: memory ops (latency, throughput, errors), knowledge growth (memories over time, graph stats)
- Drift detection: weekly sample of extractions scored against gold standard, alert on regression
- Alert rules: latency, quality, disk, error rate thresholds

#### Security & Guardrails
- **Secrets management**: `.env.example` committed, `.env` gitignored. GitHub Actions secrets for VPS SSH key, DeepSeek API key, Terraform API token. No secrets ever in code, commits, or logs.
- **API authentication**: JWT-based auth on all Mem0 API endpoints. Admin API key for privileged operations (bulk delete, export). No unauthenticated access.
- **Network security**: UFW firewall (80/443/22 only). Docker internal network — Postgres, Neo4j, Prometheus not exposed to public internet. Only Caddy faces the internet.
- **HTTPS everywhere**: Caddy auto-provisions Let's Encrypt TLS. No plaintext HTTP. HSTS headers.
- **Basic auth on admin UIs**: Neo4j Browser, Grafana dashboard behind Caddy basic auth. Not publicly accessible without credentials.
- **Rate limiting**: Caddy rate limiting on API endpoints to prevent abuse. Chrome extension uses API key, not session cookies.
- **Memory safety guardrails**: Input validation — reject memory writes containing API keys, passwords, credit card patterns (regex filter). PII detection on extraction output — flag but don't store sensitive patterns (Aadhaar, PAN numbers). These guardrails prevent accidental secret leakage into the knowledge graph.
- **Memory integrity**: Dedup prevents memory poisoning via repeated injection. Extraction pipeline validates facts against source conversation — hallucinated facts flagged for review.
- **CORS policy**: Mem0 API allows only your domain origins + Chrome extension ID. No wildcard CORS.
- ADR 009: security architecture decisions

#### Documentation
- Architecture Decision Records (ADRs) for every major choice
- README with architecture diagram, quick start, and interview walkthrough section
- Operational runbook (backup, restore, scaling, troubleshooting)
- Setup guide that someone else could follow to replicate

---

### COST ANALYSIS

#### Phase 1: Build (June-July 2026)

| Line item | Monthly (₹) | Notes |
|---|---|---|
| VPS 4GB (DO Bangalore / AWS Lightsail Mumbai) | ~2,000 | Terraform-provisioned |
| DeepSeek API (extraction) | ~30 | V4 Flash, ~50 interactions/day |
| Domain | ~80 | ~₹1,000/year |
| GitHub | 0 | Free for public repo (portfolio) |
| **Incremental new cost** | **~₹2,100** | |

#### Steady state (Dec 2026+, post-Alienware)

| Line item | Monthly (₹) | Notes |
|---|---|---|
| VPS 2GB (downsize, Neo4j moved to Alienware) | ~1,000 | |
| Ollama local extraction | 0 | On Alienware |
| **Incremental new cost** | **~₹1,000** | |

#### 6-month total: ~₹12,000-13,000

---

### EXECUTION PLAN (in order)

**The new session should execute these phases sequentially. Each phase must be working and tested before moving to the next.**

#### Phase 0: Project scaffolding + accounts
1. Create GitHub repo `ai-memory-infra` with the full directory structure above
2. Initialize pyproject.toml, Makefile, .gitignore, LICENSE (Apache 2.0)
3. Write README.md skeleton with architecture section
4. Walk me through creating accounts (interactive script):
   - DigitalOcean account (or AWS) + generate API token
   - DeepSeek API key at platform.deepseek.com
   - Domain: either register new or create subdomain on existing
   - Generate SSH keypair for VPS access
5. Store all tokens as GitHub Actions secrets
6. First commit, push to GitHub

#### Phase 1: Infrastructure as Code
1. Write Terraform configs: VPS droplet (4GB, Bangalore), firewall (80/443/22), DNS records, Spaces bucket (backups)
2. Write Docker Compose (dev + prod): Mem0 API, Postgres/pgvector, Neo4j, Dashboard, Prometheus, Grafana, Caddy
3. Write Caddyfile with four subdomains (memory, dash, graph, monitor)
4. Write .env.example with DeepSeek as extraction LLM (OPENAI_API_BASE=https://api.deepseek.com)
5. Write bootstrap.sh for first-time VPS setup
6. `terraform apply` → deploy stack → verify with curl health checks
7. Write and run health check script
8. Commit, PR, CI passes, merge to main, CD deploys

#### Phase 2: Backup + restore pipeline
1. Write backup.sh (pg_dump + neo4j-admin dump → compress → upload to Spaces/S3)
2. Write restore.sh (download → restore → verify)
3. Set up daily cron on VPS
4. Write GitHub Actions workflow that weekly restores backup to ephemeral DB and verifies
5. Test manually: backup → destroy data → restore → verify
6. Commit, PR, merge

#### Phase 3: Chrome extension fork
1. Fork OpenMemory Chrome extension
2. Modify API endpoint → `memory.{domain}`
3. Build, load in Chrome, test on claude.ai, chatgpt.com, gemini.google.com, chat.deepseek.com
4. Document fork changes in extension/README.md
5. Commit, PR, merge

#### Phase 4: MCP integrations
1. Local stdio MCP proxy: `ai-memory-mcp` calls the live REST API.
2. Claude Code MCP: `claude mcp add ai-memory -- ai-memory-mcp`
3. Cursor / VS Code MCP: add a stdio server that runs `ai-memory-mcp`.
4. Test: MCP search finds a known live memory without pasting secrets in chat.
5. Later: remote HTTP MCP endpoint for Claude mobile/iOS.

#### Phase 5: Migration pipeline (TDD)
1. Write tests FIRST:
   - test_import_md.py: .md parsing, heading-based splitting, metadata extraction
   - test_categorizer.py: category classification logic
   - test_dedup.py: dedup detection
   - test_e2e_migration.py: full pipeline against test Mem0 instance
2. Implement src/migration/ to pass all tests
3. Run migration on my actual files:
   - Local .md files → Mem0
   - Google Drive docs (download manually or via API) → Mem0
4. Verify in dashboard: memories created, categories correct, no duplication
5. Commit, PR, CI passes (tests run against docker-compose test stack), merge

#### Phase 6: LifeGraph — personal knowledge graph POC (TDD)
1. Write tests FIRST:
   - test_schema.py: node/edge type validation for :Person, :Venture, :Skill, :Decision, :Milestone, :Goal, :Tool
   - test_seed.py: initial graph structure — people, ventures, connections
   - test_queries.py: Cypher query correctness ("who is connected to which venture?", "what skills map to what goals?", "timeline of decisions")
2. Implement src/life_graph/ to pass all tests
3. Seed initial LifeGraph from your migrated Mem0 memories:
   - People: Chandra, Vijaya, Chinnu, Swapna + roles and relationships
   - Ventures: TradingFirmLLP, ContentFirm, RIA + statuses and timelines
   - Skills: Python, distributed systems, AI/ML, options trading, cloud architecture
   - Decisions: "chose Mem0 over alternatives", "chose DeepSeek for extraction", "LLP structure for tax efficiency"
   - Milestones: Amazon exit (July 1), PhD deadline (Dec 2026), firm incorporation
   - Goals: $5M journey, international migration, AI engineering role
   - Tools: Claude, ChatGPT, Gemini, Neo4j, Mem0 + how they connect
   - Temporal edges with timestamps: [:DECIDED {date, context}], [:ACHIEVED {date}], [:TARGETS {deadline}]
4. Verify in Neo4j Browser: interactive visual graph, cross-namespace queries work (join Mem0 memories with LifeGraph entities)
5. Commit, PR, merge

**NOTE: Domain-specific graphs (trading strategies, market data, social media metrics) live in SEPARATE PRIVATE repos owned by the respective firms. They plug into this same Neo4j instance via REST API + Cypher. The public repo demonstrates the platform capability via LifeGraph without leaking firm IP.**

#### Phase 7: Evaluation framework (TDD) — THE interview differentiator
1. Build gold-standard test datasets FIRST:
   - `retrieval_pairs.json`: 50+ query → expected-memories pairs (hand-labeled from your actual migrated memories)
   - `extraction_gold.json`: 30+ real conversations → expected extracted facts
   - `categorization_gold.json`: 50+ facts → expected venture category
2. Write tests FIRST:
   - test_retrieval_eval.py: scoring logic for precision@k, recall, MRR
   - test_extraction_eval.py: comparison logic across LLM providers
   - test_reporters.py: report generation correctness
   - test_e2e_eval.py: full eval suite against test stack
3. Implement src/eval/ to pass all tests:
   - `retrieval_eval.py`: query Mem0 with gold standard queries, score results against expected memories. Metrics: precision@1, precision@5, recall@10, MRR. Compare vector-only retrieval vs graph-enhanced retrieval.
   - `extraction_eval.py`: feed gold standard conversations through extraction pipeline, compare extracted facts against expected facts. Run against DeepSeek V4 Flash, GPT-4o-mini, and Gemini Flash. Produce cost-vs-quality comparison table.
   - `categorization_eval.py`: feed gold standard facts through categorizer, measure per-category precision and recall.
   - `runners.py`: orchestrate all three eval suites, aggregate into single report.
   - `reporters.py`: generate Markdown report (for PRs) and JSON report (for CI/dashboards).
4. Implement guardrail tests (security + correctness):
   - Test PII filter: feed conversations containing Aadhaar numbers, PAN numbers, API keys → verify they're NOT stored in memories
   - Test hallucination detection: feed extraction output with known hallucinated facts → verify they're flagged
   - Test dedup correctness: feed near-duplicate memories → verify dedup identifies them without false positives
   - Test input validation: malformed API requests, injection attempts → verify clean rejection
5. Write GitHub Actions workflow `eval-suite.yml`:
   - Runs weekly on schedule AND on-demand via workflow_dispatch
   - Spins up ephemeral Docker Compose test stack
   - Runs full eval suite
   - Posts Markdown summary as a GitHub Actions summary
   - Fails pipeline if any metric drops below threshold (retrieval precision@5 < 0.7, extraction recall < 0.8)
5. Write ADR 007: eval framework design decisions
6. Run eval against your live system, capture baseline metrics
7. Commit, PR, CI passes, merge

#### Phase 8: Observability + monitoring
1. Add Prometheus + Grafana to Docker Compose (prod overlay):
   - `prometheus`: scrape Mem0 API metrics endpoint every 15s
   - `grafana`: pre-provisioned dashboards, datasource auto-configured
2. Instrument Mem0 API interactions in src/observability/:
   - `metrics.py`: Prometheus client — counters (memory_writes_total, memory_searches_total), histograms (retrieval_latency_seconds, extraction_latency_seconds), gauges (total_memories, memories_by_category, graph_nodes, graph_edges)
   - Expose at `/metrics` endpoint via FastAPI middleware or sidecar
3. Build Grafana dashboards (src/observability/dashboards/):
   - `memory_ops.json`: retrieval latency p50/p95/p99, write throughput, search throughput, error rate
   - `knowledge_growth.json`: memories per category over time, dedup rate, graph node/edge counts, top entities
4. Implement drift detection (src/observability/drift_detector.py):
   - Weekly cron: sample 5% of recent extractions, score against gold standard subset
   - If extraction quality drops below 85%, emit alert metric
   - Compare current scores against Phase 7 baseline
5. Write alert rules (src/observability/alerts.py):
   - Retrieval p95 > 500ms → alert
   - Extraction quality < 85% → alert
   - VPS disk usage > 80% → alert
   - Memory write errors > 5/hour → alert
   - Configure Grafana alerting to email or Slack webhook
6. Add `monitor.{domain}` route to Caddyfile (with basic auth — don't expose Grafana publicly without auth)
7. Write ADR 008: observability stack choice (Prometheus + Grafana vs LangFuse vs custom)
8. Commit, PR, merge

#### Phase 9: Documentation + portfolio polish
1. Write architecture.md with Mermaid diagrams
2. Write all 9 ADRs
3. Write operational runbook
4. Write "Interview Walkthrough" section in README
5. Add eval results summary to README (baseline metrics, cost-vs-quality table)
6. Add monitoring screenshots to README (Grafana dashboards)
7. Final README polish: badges (CI status, coverage, eval score), architecture diagram, quick start, demo screenshots
8. Commit, push, final state

---

### WHAT THIS LOOKS LIKE IN AN INTERVIEW

> "I built a self-hosted cross-platform AI memory infrastructure. It's a persistent knowledge graph that sits underneath Claude, ChatGPT, Gemini, and DeepSeek — giving me shared context across all of them, on any device.
>
> The stack is Mem0 + PostgreSQL/pgvector + Neo4j, deployed via Terraform to a VPS in Bangalore, with CI/CD through GitHub Actions. Tests run against an ephemeral Docker Compose stack in CI. Backups are verified weekly by restoring to an ephemeral database.
>
> The knowledge graph has two namespaces. One is auto-managed by Mem0 for semantic memory. The other is what I call LifeGraph — a temporal knowledge graph of my professional life: people, ventures, skills, decisions, and milestones, all connected with timestamped relationships. Cross-namespace Cypher queries join memories with entities — 'what decisions did I make about X venture in the last month?' The architecture supports pluggable domain graphs — my trading firm and content business each have their own private repos that connect to the same Neo4j instance.
>
> I built an evaluation framework that measures retrieval **correctness** (precision@5, MRR), extraction **accuracy** across three LLM providers, and auto-categorization precision per venture. The eval runs weekly in CI and blocks deploys if metrics regress below baseline. I proved DeepSeek V4 Flash matches GPT-4o-mini extraction accuracy at 1/4th the cost — that analysis is in the repo with reproducible numbers.
>
> **Security guardrails** are built in: JWT auth on all endpoints, PII detection that prevents Aadhaar/PAN numbers and API keys from leaking into the knowledge graph, input validation against injection, HTTPS everywhere, no admin UIs exposed without auth. The eval suite includes guardrail tests that verify these protections work.
>
> Production observability via Prometheus + Grafana tracks retrieval latency (p50/p95/p99), extraction quality drift, and knowledge growth over time. A weekly drift detector samples 5% of extractions and alerts if accuracy drops below 85%.
>
> It costs under ₹2,000/month to run. The public repo is the platform and LifeGraph POC — anyone can fork it. Domain-specific IP lives in private repos. The entire codebase has Terraform IaC, Docker Compose, TDD with 80%+ coverage, a full eval suite with guardrail tests, production monitoring, and ADRs for every major decision."

---

### START NOW

Begin with Phase 0. Create the GitHub repo structure, then walk me through account creation interactively. Don't explain what Terraform is — give me the files. Let's go.

