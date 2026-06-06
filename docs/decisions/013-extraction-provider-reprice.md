# ADR 013: Re-evaluate the extraction provider (DeepSeek vs single-provider)

**Status:** Accepted (supersedes ADR 002)
**Date:** 2026-06-05
**Deciders:** Chandra

### Context

ADR 002 chose DeepSeek V4 Flash for fact extraction, justified mainly by cost:
~₹30/mo vs ~₹400/mo for **`gpt-4o-mini`**. Since then two things changed:

1. We adopted tenet 7 (fewer moving parts) and **tenet 9** (one provider across
   pipeline stages unless the cost/capability gap is *vast*).
2. OpenAI shipped **`gpt-4.1-nano`** — now Mem0's default extraction LLM — which
   is far cheaper than `gpt-4o-mini`.

A 2026 re-price (verified via web search, June 2026) at this workload
(~1,500 interactions/mo):

| Stage | DeepSeek V4 Flash | OpenAI gpt-4.1-nano | gpt-4o-mini (old ADR 002 baseline) |
|---|---|---|---|
| Input /M | $0.14 | $0.10 | $0.15 |
| Output /M | $0.28 | $0.40 | $0.60 |
| Est. extraction cost | ~₹37/mo | ~₹35/mo | ~₹400/mo |

The original "₹30 vs ₹400" gap was against `gpt-4o-mini`. Against `gpt-4.1-nano`
the gap is **~zero** — i.e. *not vast* by tenet 9.

There is also an integration cost to the split: Mem0 uses a single OpenAI client
for both the LLM and the embedder, so DeepSeek-for-extraction +
OpenAI-for-embeddings cannot be done by repointing `OPENAI_BASE_URL` (the embedder
would hit DeepSeek, which has no embeddings endpoint). It requires a per-component
Mem0 config (mounted `config.json`), a second key, and a second bill. DeepSeek
also routes conversation snippets through a Chinese API (the privacy note in
ADR 002).

### Decision

**Consolidate extraction onto OpenAI `gpt-4.1-nano`**, so a single provider/key
serves both stages (extraction + `text-embedding-3-small` embeddings, ADR 011).
At ~the same cost this satisfies tenets 7 and 9, removes the per-component-config
burden, removes the second bill, and removes the China-data path. This is now the
active config in `.env.example`; **ADR 002 is superseded.**

Keep DeepSeek (and Qwen/DashScope as a cheaper single-provider Chinese option)
documented as swappable alternatives behind the OpenAI-compatible interface
(tenet 2). `.env.example` carries the alternative wiring + a one-line switch.

### Validation

The choice stands on the re-price above; the **Phase 7 eval framework** still
runs the quantitative `gpt-4.1-nano` vs DeepSeek vs Gemini Flash extraction-
quality comparison as a backstop. If gpt-4.1-nano ever regresses materially, the
swap back is one env var (tenet 2).

---
