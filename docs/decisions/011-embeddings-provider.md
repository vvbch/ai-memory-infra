# ADR 011: OpenAI text-embedding-3-small for embeddings

**Status:** Accepted
**Date:** 2026-06-05
**Deciders:** the operator

### Context

Mem0 has two model-backed stages: an LLM for fact *extraction* and an *embedder*
that vectorizes facts and queries for pgvector similarity search. ADR 002 picked
DeepSeek V4 Flash for extraction — but DeepSeek ships **no embeddings endpoint**
(the community feature requests are closed not-planned), so a separate embeddings
provider is required. This is the explicit exception in tenet 9 ("one provider
unless the gap is vast" — here a single provider is impossible).

### Decision

Use OpenAI **`text-embedding-3-small`** for embeddings in Phase 1.

This is also Mem0's built-in default embedder (verified in
`mem0ai/mem0` `server/.env.example`: `MEM0_DEFAULT_EMBEDDER_MODEL=text-embedding-3-small`),
so there is zero integration risk — no config beyond an `OPENAI_API_KEY`.

### Cost

~₹15/mo at this workload (1536-dim vectors; embeddings are cheap relative to the
extraction LLM). See `docs/architecture.md` → Components & cost.

### Consequences

- **Positive:** Trivial setup (Mem0 default), tiny cost, high-quality vectors,
  keeps the 4GB VPS lean — no local embedding model to host in Phase 1.
- **Negative:** A second provider/key alongside the extraction LLM, and OpenAI
  sees the (already-extracted) fact text it embeds.
- **Swap path (tenet 2):** steady state (post-Alienware, Dec 2026+) moves
  embeddings to local Ollama (`nomic-embed-text`, 768-dim) for ₹0 and full
  locality. Note: changing embedding dimensions requires re-indexing pgvector
  (`embedding_model_dims` + re-add memories), so the swap is a planned migration,
  not a hot config flip.
- **Interaction with ADR 013:** if extraction consolidates onto OpenAI, this same
  `OPENAI_API_KEY` covers both stages with no extra moving parts.

---
