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

### Note (2026-06-06) — RAG-quality mitigations are mostly native to Mem0; gate the rest on this eval

A review of recommended RAG-quality mitigations (raised in a Gemini design
critique) found that **most are already built into Mem0**, so we build nothing
and instead *verify* them through this framework:

- **Multi-signal retrieval = Mem0 hybrid search, on by default.** Mem0 v3's
  search combines **vector similarity + BM25 keyword + entity-graph boosting**
  automatically, no configuration. So "add hybrid/keyword retrieval" is already
  satisfied; the retrieval eval (suite 1) measures whether it's good enough.
  *(Source: `mem0ai/mem0` `skills/mem0/references/{architecture,features}.md`.)*
- **Reranker = a config flag, left OFF by default.** Mem0 exposes a reranker
  (`rerank=True` / a configurable `llm_reranker` or specialized provider); v3's
  default is `rerank=False` (it was `True` in v2). It adds ~150–200 ms latency.
  **Decision: leave it OFF and enable it only if this eval shows retrieval
  precision@5 < 0.7** (the existing CI threshold). Don't pay the latency until
  the numbers justify it.
- **"Lost-in-the-middle" / long-context synthesis hallucination = misapplied
  here.** That failure mode is about a *generator* LLM synthesizing a long answer
  over many retrieved chunks. In this system the extraction model (`gpt-5-mini`,
  ADR 013) only does **short-input fact extraction** (a snippet in, small JSON
  out) — it never synthesizes long answers. Synthesis happens in the **native
  LLMs** (Claude/ChatGPT/Gemini/DeepSeek), which own their own context handling.
  So this mitigation doesn't apply to our pipeline; noting it here so it isn't
  re-raised.

**Net:** hybrid retrieval is free and already on; the reranker is a deferred,
eval-gated toggle; the synthesis-hallucination concern is out of scope for the
extraction stage. The portfolio narrative is "evaluated the critique, verified
the platform already covers it natively, deferred the one optional knob behind a
measured gate" — not "bolted on retrieval machinery we didn't need."

---
