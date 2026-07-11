# Market fit validation


The project was validated against the 2026 AI Engineer hiring checklist (10 skills). Before adding eval and observability, it scored 7/10. After:

| Checklist item | Coverage |
|---|---|
| Agent orchestration | ✅ MCP integration, Chrome extension, REST API orchestration |
| MCP integration | ✅ Local stdio MCP + remote HTTP MCP (`mcp.`, ADR 034/035) live for Claude/ChatGPT/Perplexity |
| Eval design | ✅ ADR 007 — synthetic gold + CI gate; live-stack eval **[target]** |
| Prompt engineering | ⚠️ Implicit (extraction prompts) — documented in ADR |
| Vector DB / RAG | ✅ pgvector, semantic search, retrieval pipeline |
| Cost optimization | ✅ Native UIs avoid chat API costs; single OpenAI provider kept cheap and swappable (ADR 013) |
| Safety / guardrails | ⚠️ ADR 009 — HTTPS + API key/JWT + basic auth in place; PII filter / CORS / rate-limit **[target]** |
| Computer-use deployment | ✅ Terraform IaC, Docker, CI on every PR, production VPS; CD **[target]** (manual SSH today) |
| Production observability | ✅ ADR 008 — Prometheus, Grafana, drift detection |
| Frontier-model fluency | ✅ Multi-LLM (Claude, GPT, Gemini, DeepSeek), model comparison in eval |

Bangalore-specific: 2,726 agentic AI engineer jobs as of May 2026. Over 75% of AI engineering postings require domain specialization — the trading firm domain qualifies.
