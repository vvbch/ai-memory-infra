# ADR 002: DeepSeek V4 Flash for extraction

**Status:** Accepted
**Date:** 2026-06-04

### Context

Mem0 uses an LLM to extract facts from conversations. The default is OpenAI GPT-4o-mini. Need to minimize extraction cost without sacrificing quality, especially since this is a personal/small-business workload.

### Decision

DeepSeek V4 Flash as the extraction LLM. The DeepSeek API is OpenAI-compatible (same request format, just change `OPENAI_BASE_URL` to `https://api.deepseek.com`). Two environment variable changes, zero code changes.

### Cost comparison

| Model | Input cost | Output cost | Monthly cost @50 interactions/day |
|---|---|---|---|
| GPT-4o | $5.00/M | $15.00/M | ~₹4,000 |
| GPT-4o-mini | $0.15/M | $0.60/M | ~₹400 |
| DeepSeek V4 Flash | $0.14/M | $0.28/M | ~₹30 |
| Gemini Flash | $0.10/M | $0.40/M | ~₹25 |

### Why not Gemini Flash (cheapest)?

Gemini's API is not OpenAI-compatible. Mem0 reads `OPENAI_BASE_URL` and `OPENAI_API_KEY` environment variables. DeepSeek's API speaks the same protocol — literal drop-in. Gemini would require code changes to the Mem0 client. Not worth it for ₹5/month difference.

### Consequences

- **Positive:** Extraction cost drops from ~₹400/month (GPT-4o-mini) to ~₹30/month. Near-free.
- **Negative:** DeepSeek is a Chinese company — data passes through their API during extraction. Mitigated: extraction payloads are conversation snippets, not full strategy documents. For maximum privacy, Phase 3 (post-Alienware) switches to local Ollama with zero API dependency.
- **Eval required:** Phase 7 eval framework will quantitatively compare DeepSeek vs GPT-4o-mini vs Gemini Flash extraction quality. If DeepSeek quality is significantly lower, we switch. The architecture makes switching trivial (two env vars).

---
