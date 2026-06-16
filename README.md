# ai-memory-infra

Self-hosted, cross-platform **AI memory infrastructure** with a knowledge graph.
A persistent memory layer under Claude, ChatGPT, Gemini, and DeepSeek — shared
context across every LLM, on any device.

## What it is

- **Memory layer**: Mem0 REST API over PostgreSQL/pgvector, with a local stdio MCP
  proxy for Claude Code, Cursor, and VS Code (ADR 025), plus a remote HTTP MCP
  endpoint with self-hosted OAuth for Claude mobile, ChatGPT, and Perplexity
  (ADR 034–036).
- **Knowledge graph**: Neo4j is provisioned and backed up on the VPS but **not
  written to yet** (ADR 032). LifeGraph — people, ventures, skills, decisions,
  milestones — is an **in-memory POC** in `src/life_graph/` (Phase 6 code ✅;
  live Neo4j seed is a follow-up ops step).
- **Reach**: Chrome extension (desktop / ChromeOS), local MCP proxy for IDEs,
  remote MCP for OAuth-capable native apps. Android extension coverage is
  best-effort only (ADR 004). Native LLM UIs unchanged. Coverage matrix:
  `docs/architecture.md`.
- **Agent personas**: Build Agent, Research and Strategy Agent, and Operator
  Assistant own future skills/tools. See `docs/agent-personas.md`.
- **Models**: OpenAI `gpt-5-mini` extraction (Mem0's default; chosen for
  structured-output reliability) + `text-embedding-3-small` embeddings (single
  provider, swappable; ~₹105/mo). See ADR 013.

## Quick start

```bash
gh repo clone <you>/ai-memory-infra && cd ai-memory-infra
python scaffold.py                 # lay down structure (idempotent)
cp infra/.env.example infra/.env   # fill in secrets
```

Operational walkthrough (Terraform, deploy, MCP connectors): `docs/setup.md`.

## Build status (honest)

Phases **0–8 core code** are in place; **Phase 9** (docs/polish) is ongoing.
Session state and next action: `docs/planning/STATUS.md`. Full phase map:
`AGENTS.md`.

| Area | Status |
|---|---|
| IaC + deploy | ✅ Terraform + Compose; **manual SSH** deploy today (`make deploy`) — no push-to-main CD yet |
| Memory read/write contract | ✅ acceptance probe green on live stack |
| Migration pipeline + bulk load | ✅ `src/migration/`; ADR facts loaded |
| LifeGraph POC | ✅ in-memory (`src/life_graph/`); live Neo4j seed **[target]** |
| Eval regression gate | ✅ synthetic gold blocks CI (`scripts/run_eval_gate.py`) |
| Observability | ✅ metrics, drift, alerts, health checker in code; Grafana via **`observability` compose profile** — see `docs/observability-deploy.md` |

## Engineering

Terraform IaC, GitHub Actions **CI** on every push/PR (ruff, mypy, pytest,
contract/STATUS gates, eval regression on synthetic gold), TDD (80%+ coverage on
`src/`), ADRs in `docs/decisions/`. Tenets in `docs/tenets.md`. Canonical agent
context in `AGENTS.md`.

## License

Apache-2.0.
