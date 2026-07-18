# Market fit validation


The project was validated against the 2026 AI Engineer hiring checklist (10 skills). Before adding eval and observability, it scored 7/10. After:

| Checklist item | Coverage |
|---|---|
| Agent orchestration | ✅ MCP integration, Chrome extension, REST API orchestration |
| MCP integration | ✅ Local stdio MCP proxy + remote HTTP MCP (`mcp.`, OAuth) for Claude mobile / connectors (ADR 034/035) |
| Eval design | ✅ ADR 007 — retrieval/extraction/categorization + guardrail tests; CI synthetic-gold gate in place; live-stack eval **[target]** |
| Prompt engineering | ⚠️ Implicit (extraction prompts) — documented in ADR |
| Vector DB / RAG | ✅ pgvector, semantic search, retrieval pipeline |
| Cost optimization | ✅ Native UIs avoid chat API costs; single OpenAI provider kept cheap and swappable (ADR 013) |
| Safety / guardrails | ⚠️ ADR 009 decided; HTTPS + API auth + gitleaks **in place**; PII filter / CORS / rate limit remain **[target]** (`AGENTS.md`) |
| Computer-use deployment | ⚠️ Terraform IaC + Docker + CI **in place**; CD is **[target]** (manual SSH deploy today) |
| Production observability | ✅ ADR 008 — Prometheus, Grafana, drift detection |
| Frontier-model fluency | ✅ Multi-LLM clients (Claude, GPT, Gemini, DeepSeek); cross-LLM extraction matrix partially **[target]** |

Bangalore-specific: 2,726 agentic AI engineer jobs as of May 2026. Over 75% of AI engineering postings require domain specialization — the trading firm domain qualifies.
