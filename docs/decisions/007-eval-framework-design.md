# ADR 007: Eval framework design

**Status:** Accepted
**Date:** 2026-06-04

### Context

Multiple 2026 hiring analyses identify evaluation framework design as "the single best signal of real LLM experience." The project initially had TDD but no LLM-specific evaluation. Market fit analysis against the 2026 AI engineer hiring checklist showed eval as the #1 gap (project scored 7/10 without it, 10/10 with it).

### Decision

Three eval suites plus guardrail tests, run weekly in CI:

1. **Retrieval correctness**: Query Mem0 with 50+ gold-standard query/expected-memory pairs. Metrics: precision@1, precision@5, recall@10, MRR. Compare vector-only vs graph-enhanced retrieval.
2. **Extraction accuracy**: Feed 30+ gold-standard conversations through the extraction pipeline. Compare output facts against expected facts. Run against DeepSeek V4 Flash, GPT-4o-mini, and Gemini Flash. Produce cost-vs-quality comparison table.
3. **Categorization accuracy**: Feed 50+ gold-standard facts through auto-categorizer. Measure per-category precision and recall.
4. **Guardrail tests**: PII detection (Aadhaar/PAN/API key filtering), hallucination flagging, dedup correctness, input validation against injection.

### CI integration

- GitHub Actions workflow `eval-suite.yml` runs weekly and on-demand
- Spins up ephemeral Docker Compose test stack
- Fails pipeline if metrics regress below threshold: retrieval precision@5 < 0.7, extraction recall < 0.8
- Posts Markdown summary as GitHub Actions summary

### Why not LangSmith/LangFuse for eval

Both are excellent but add another managed dependency. For a personal project, a custom eval harness against gold-standard datasets is more portable, more impressive in interviews ("I built the eval framework"), and zero additional cost. The eval code itself is part of the portfolio.

### Consequences

- **Positive:** Quantitative proof that the system works. Cross-LLM cost-vs-quality comparison is a concrete, reproducible result interviewers can examine. Guardrail tests prove security isn't just claimed but verified.
- **Negative:** Gold-standard datasets must be hand-labeled — initial effort of ~2 days. Datasets need periodic refresh as memories grow.

---
