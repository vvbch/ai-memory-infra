# ai-memory-infra

Self-hosted, cross-platform **AI memory infrastructure** with a knowledge graph.
A persistent memory layer under Claude, ChatGPT, Gemini, and DeepSeek - shared
context across every LLM, on any device.

## What it is

- **Memory layer**: Mem0 (FastAPI REST + MCP) over PostgreSQL/pgvector.
- **Knowledge graph**: Neo4j, dual namespace - Mem0's auto-managed semantic
  graph + LifeGraph (people, ventures, skills, decisions, milestones).
- **Reach**: Chrome extension (desktop / ChromeOS) + Claude MCP connector
  (iOS, Claude Code) + Cursor/VS Code as MCP clients. Android extension
  coverage is best-effort only (see ADR 004). Native LLM UIs unchanged.
- **Models**: OpenAI `gpt-5-mini` extraction (Mem0's default; chosen for
  structured-output reliability) + `text-embedding-3-small` embeddings (single
  provider, swappable; ~Rs.105/mo). See ADR 013.

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
