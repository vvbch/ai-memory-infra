# ai-memory-infra

Self-hosted, cross-platform **AI memory infrastructure** with a knowledge graph.
A persistent memory layer under Claude, ChatGPT, Gemini, and DeepSeek - shared
context across every LLM, on any device.

## What it is

- **Memory layer**: Mem0 REST API over PostgreSQL/pgvector, with a local MCP
  proxy for Claude Code, Cursor, and VS Code (ADR 025).
- **Knowledge graph**: Neo4j reserved for LifeGraph (Phase 6); Mem0's built-in
  graph path is not wired in the pinned mem0ai 2.0.4 build — see BACKLOG P1
  `[docs-drift]`.
- **Reach**: Chrome extension (desktop / ChromeOS) + local MCP proxy for
  Claude Code, Cursor, and VS Code. Claude mobile needs a later remote HTTP MCP
  endpoint. Android extension coverage is best-effort only (see ADR 004). Native
  LLM UIs unchanged.
- **Agent personas**: Build Agent, Research and Strategy Agent, and Operator
  Assistant own future skills/tools. See `docs/agent-personas.md`.
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

Terraform IaC, GitHub Actions CI on every PR (CD planned), TDD (80%+ coverage),
eval framework + observability planned (Phases 7–8), ADRs in `docs/decisions/`.
Tenets in
`docs/tenets.md`. Canonical agent context in `AGENTS.md`.

## License

Apache-2.0.
