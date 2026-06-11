# ADR 013: Re-evaluate the extraction provider (DeepSeek vs single-provider)

**Status:** Accepted (supersedes ADR 002)
**Date:** 2026-06-05 · **Corrected:** 2026-06-06 (model id + rationale; see below)
**Deciders:** the operator

### Context

ADR 002 chose DeepSeek V4 Flash for fact extraction, justified mainly by cost:
~₹30/mo vs ~₹400/mo for **`gpt-4o-mini`**. Since then two things changed:

1. We adopted tenet 7 (fewer moving parts) and **tenet 9** (one provider across
   pipeline stages unless the cost/capability gap is *vast*).
2. OpenAI's small models got far cheaper than the old `gpt-4o-mini` baseline,
   collapsing the cost gap that originally justified the DeepSeek split.

A 2026 re-price (verified via web search, June 2026) at this workload
(~1,500 interactions/mo), against the old baseline:

| Stage | DeepSeek V4 Flash | OpenAI small models | gpt-4o-mini (old ADR 002 baseline) |
|---|---|---|---|
| Input /M | $0.14 | $0.05 (nano) · $0.25 (5-mini) | $0.15 |
| Output /M | $0.28 | $0.40 (nano) · $2.00 (5-mini) | $0.60 |
| Est. extraction cost | ~₹37/mo | ~₹35/mo (nano) · ~₹90/mo (5-mini) | ~₹400/mo |

The original "₹30 vs ₹400" gap was against `gpt-4o-mini`. Against any current
OpenAI small model the gap is small in **absolute** rupees — i.e. *not vast* by
tenet 9 — so consolidating onto OpenAI wins on simplicity.

There is also an integration cost to the split: Mem0 uses a single OpenAI client
for both the LLM and the embedder, so DeepSeek-for-extraction +
OpenAI-for-embeddings cannot be done by repointing `OPENAI_BASE_URL` (the embedder
would hit DeepSeek, which has no embeddings endpoint). It requires a per-component
Mem0 config (mounted `config.json`), a second key, and a second bill. DeepSeek
also routes conversation snippets through a Chinese API (the privacy note in
ADR 002).

### Decision

**Consolidate extraction onto OpenAI, using `gpt-5-mini`**, so a single
provider/key serves both stages (extraction + `text-embedding-3-small`
embeddings, ADR 011). This satisfies tenets 7 and 9, removes the
per-component-config burden, removes the second bill, and removes the China-data
path. This is the active config in `.env.example`; **ADR 002 is superseded.**

Keep DeepSeek (and Qwen/DashScope as a cheaper single-provider Chinese option)
documented as swappable alternatives behind the OpenAI-compatible interface
(tenet 2). `.env.example` carries the alternative wiring + a one-line switch.

### Correction (2026-06-06) — why `gpt-5-mini`, not `gpt-4.1-nano`

This ADR originally selected **`gpt-4.1-nano`**, justified partly as "Mem0's
default extraction LLM." On 2026-06-06 that claim was **re-verified against the
`mem0ai/mem0` repo and SDK changelog and found stale**: Mem0's **current default
LLM is `gpt-5-mini`** (PR #4829 — default across `OpenAILLM`,
`OpenAIStructuredLLM`, `AzureOpenAILLM`, and the `LiteLLM` fallback). The default
embedder is still `text-embedding-3-small`. *(Source: `github.com/mem0ai/mem0`
README + `docs.mem0.ai/changelog/sdk`.)*

Given the default moved, the choice was re-made on **capability, not the stale
default**:

- **Cost is noise at this volume.** `gpt-5-mini` extraction ≈ **~₹90/mo**
  (~2–3× the `gpt-4.1-nano` figure; extraction is input-dominated — a snippet in,
  small JSON out — so the blend sits nearer the 2.5× input ratio than the 5×
  output ratio). At ~50 interactions/day the absolute delta vs nano is tens of
  rupees — below the threshold where cost should drive the decision (tenet 6).
- **Structured-output reliability is what matters here.** Mem0 extraction (and
  our venture categorizer) depend on the model emitting **valid, schema-conformant
  JSON** and on **nuanced classification** of facts into venture tags. The `nano`
  tier has a measurably higher JSON-schema error rate and weaker nuanced
  classification than the `mini` tier; those failures land exactly on our two
  most sensitive paths. Paying tens of rupees/mo to reduce extraction/categorizer
  errors is an obviously correct trade at this scale.
- **Embeddings are unchanged:** `text-embedding-3-small` (ADR 011).

`gpt-4.1-nano` remains a documented fallback if cost ever becomes material; the
swap is one env var (tenet 2).

### Validation

The choice stands on the reliability argument above; the **Phase 7 eval
framework** still runs the quantitative `gpt-5-mini` vs `gpt-4.1-nano` vs DeepSeek
vs Gemini Flash extraction-quality comparison as a backstop. If `gpt-5-mini` ever
regresses materially or the cheaper tier closes the reliability gap, the swap is
one env var (tenet 2).

---
