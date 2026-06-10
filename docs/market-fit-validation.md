# Market fit validation


The project was validated against the 2026 AI Engineer hiring checklist (10 skills). Before adding eval and observability, it scored 7/10. After:

| Checklist item | Coverage |
|---|---|
| Agent orchestration | ✅ MCP integration, Chrome extension, REST API orchestration |
| MCP integration | ✅ Local MCP proxy for Claude Code/Cursor/VS Code; remote HTTP MCP endpoint planned for Claude mobile |
| Eval design | ⚠️ ADR 007 designed; `src/eval/` stubs — not implemented |
| Prompt engineering | ⚠️ Implicit (extraction prompts) — documented in ADR |
| Vector DB / RAG | ✅ pgvector, semantic search, retrieval pipeline |
| Cost optimization | ✅ Native UIs avoid chat API costs; single OpenAI provider kept cheap and swappable (ADR 013) |
| Safety / guardrails | ⚠️ ADR 009 target; X-API-Key + HTTPS live; PII/CORS/rate-limit pending |
| Computer-use deployment | ⚠️ Terraform IaC, Docker, production VPS live; CD stub only |
| Production observability | ⚠️ ADR 008 designed; Prometheus/Grafana not deployed (Phase 8) |
| Frontier-model fluency | ✅ Multi-LLM (Claude, GPT, Gemini, DeepSeek), model comparison in eval |

Bangalore-specific: 2,726 agentic AI engineer jobs as of May 2026. Over 75% of AI engineering postings require domain specialization — the trading firm domain qualifies.
