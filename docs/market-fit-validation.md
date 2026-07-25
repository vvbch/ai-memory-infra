# Market fit validation

> Snapshot of hiring-checklist coverage. Keep status tags honest (tenet 10) —
> prefer `[target]` over a green check when the capability is designed but not
> live. Last honesty pass: 2026-07-25 weekly scan.

The project was validated against the 2026 AI Engineer hiring checklist (10 skills). Before adding eval and observability, it scored 7/10. After:

| Checklist item | Coverage |
|---|---|
| Agent orchestration | ✅ MCP integration, Chrome extension, REST API orchestration |
| MCP integration | ✅ Local stdio MCP proxy + remote HTTP MCP with OAuth (ADR 034–036) for Claude mobile, ChatGPT, Perplexity |
| Eval design | ✅ ADR 007 — synthetic gold suites + CI/weekly gate; live-stack eval **[target]** |
| Prompt engineering | ⚠️ Implicit (extraction prompts) — documented in ADR |
| Vector DB / RAG | ✅ pgvector, semantic search, retrieval pipeline |
| Cost optimization | ✅ Native UIs avoid chat API costs; single OpenAI provider kept cheap and swappable (ADR 013) |
| Safety / guardrails | ◑ ADR 009 — HTTPS + API auth + gitleaks in place; PII filter / rate limit / CORS allowlist **[target]** |
| Computer-use deployment | ◑ Terraform IaC, Docker, CI on every PR; CD **[target]** (manual SSH deploy today) |
| Production observability | ✅ ADR 008 — Prometheus, Grafana, drift detection (Grafana via observability profile) |
| Frontier-model fluency | ✅ Multi-LLM clients (Claude, GPT, Gemini, DeepSeek); model comparison in eval **[target]** |

Bangalore-specific job-count figures in earlier drafts go stale quickly — re-verify before citing externally.
