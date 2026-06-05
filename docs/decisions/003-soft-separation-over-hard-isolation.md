# ADR 003: Soft separation over hard isolation

**Status:** Accepted
**Date:** 2026-06-04

### Context

Memory system serves four ventures (trading firm, social media firm, RIA, personal/career) plus cross-cutting concerns. Need to decide whether memories are isolated per venture or pooled with metadata tags.

### Options

**Option A: Hard isolation** — separate `agent_id` per venture in Mem0. Trading firm memories never appear in social media conversations.

**Option B: Soft separation** — single `user_id`, all memories in one pool, tagged with category metadata (`trading_firm`, `social_media`, `ria`, `personal`, `career`, `migration`). Semantic search serves relevant context naturally.

### Decision

Option B — soft separation with metadata categories.

### Reasoning

The ventures are deeply interlinked:
- Vijaya is co-founder of the trading firm AND involved in the social media firm
- Financial runway calculations affect ALL ventures simultaneously
- The LLP structure decision touches trading AND RIA
- Career decisions (international migration) constrain all venture timelines
- Skills (Python, distributed systems) are shared across all domains

Hard isolation would break these cross-domain connections. When asking "how does the Germany migration timeline affect the firm launch?", memories from both `career` and `trading_firm` need to surface together.

### Consequences

- **Positive:** Cross-domain queries work naturally. Memory serves the right context via semantic relevance, not manual scope switching.
- **Negative:** Possible noise — a social media memory might surface during a trading conversation if keywords overlap. Mitigated by Mem0's relevance scoring and the option to filter by category metadata in queries.

---
