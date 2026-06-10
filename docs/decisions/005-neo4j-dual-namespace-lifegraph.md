# ADR 005: Neo4j dual namespace with LifeGraph

**Status:** Accepted — **partially corrected by ADR 032 (2026-06-10).** The
LifeGraph namespace (decision #2) remains the plan (Phase 6, not yet built). The
premise behind decision #1 — that the deployed **Mem0 auto-manages a graph** in the
same Neo4j instance — is **wrong for the current stack**: the deployed Mem0 server
ships no graph store and never writes Neo4j (ADR 032). So today Neo4j is a single
(future) namespace, not a live dual namespace.
**Date:** 2026-06-04

### Context

Need a knowledge graph alongside vector-based semantic memory. Mem0 has built-in graph support via Neo4j, but we also want a custom domain graph. The domain graph (market world model for the trading firm) contains proprietary IP. The public portfolio repo cannot contain firm IP.

### Decision

Neo4j with two namespaces on the same instance, separated by node labels:

1. **Mem0 namespace** (auto-managed): `:Entity`, `:Memory`, `:Relationship` — Mem0 creates and manages these automatically during fact extraction.
2. **LifeGraph namespace** (managed by public repo code): `:Person`, `:Venture`, `:Skill`, `:Decision`, `:Milestone`, `:Goal`, `:Tool` — a temporal knowledge graph of professional life.

Domain-specific graphs (market world model, social media metrics, RIA compliance) live in separate private repos with their own node labels, connecting to the same Neo4j instance.

### Why LifeGraph instead of market graph in the public repo

- Market graph contains firm IP (instruments, strategies, backtest results, SEBI compliance logic). Can't be in a public portfolio repo.
- LifeGraph is personal and relatable in interviews. Demonstrates the same temporal graph capability (timestamped edges, entity relationships, cross-namespace queries) without leaking proprietary data.
- Self-referential: "I built a system that models my own professional journey." Interviewers remember this.
- Cross-namespace queries still work as a demo: "JOIN Mem0 memories with LifeGraph entities — what decisions did I make about X venture this month?"

### Consequences

- **Positive:** Public repo demonstrates graph capability without IP leakage. LifeGraph is a stronger interview story than a generic sample. Domain repos can evolve independently.
- **Negative:** LifeGraph is a POC, not production-critical. The real value is in the private domain graphs. The public repo demonstrates capability but not the actual business application.

---
