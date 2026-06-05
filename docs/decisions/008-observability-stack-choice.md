# ADR 008: Observability stack choice

**Status:** Accepted
**Date:** 2026-06-04

### Context

Production systems need monitoring. The 2026 AI hiring checklist includes "production observability" as one of 10 required skills. Market fit analysis identified this as the #2 gap after eval.

### Options

1. **Prometheus + Grafana** — self-hosted, open source, industry standard. Already runs in Docker.
2. **LangFuse** — open source LLM observability. Traces, scores, sessions. More LLM-aware.
3. **Custom logging** — roll own metrics into Postgres, build dashboards.

### Decision

Prometheus + Grafana for infrastructure metrics. Custom drift detection for LLM-specific quality monitoring.

### Reasoning

- Prometheus + Grafana is the industry standard that interviewers recognize immediately. "I use Prometheus" requires no explanation.
- LangFuse adds another Docker container + Postgres database. On a 4GB VPS already running Mem0 + Postgres + Neo4j + Grafana, RAM is tight. Can add later on Alienware.
- Custom drift detection (sample 5% of extractions weekly, score against gold standard) gives LLM-specific observability without another dependency.

### Metrics tracked

- Retrieval latency: p50, p95, p99 histograms
- Write/search throughput: request counters
- Memory counts: gauge by category
- Graph stats: node/edge counts
- Extraction quality drift: weekly comparison against Phase 7 baseline
- System: VPS disk, memory, CPU

### Consequences

- **Positive:** Industry-standard monitoring. Grafana dashboards are visual proof in interviews. Drift detection catches quality regressions before they compound.
- **Negative:** Prometheus + Grafana add ~500MB RAM overhead. On 4GB VPS, this is significant. May need to upgrade to 8GB ($48/mo) or defer Grafana to Alienware.

---
