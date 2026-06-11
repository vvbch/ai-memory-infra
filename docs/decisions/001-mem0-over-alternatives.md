# ADR 001: Mem0 over alternatives

**Status:** Accepted
**Date:** 2026-06-04
**Deciders:** the operator

### Context

Needed a persistent memory layer that works across Claude, ChatGPT, Gemini, and DeepSeek — on desktop and mobile — with full data portability (export/import without vendor lock-in). The current approach of manually maintaining .md context files and asking Claude to update them at end of session was hitting race conditions and consuming bandwidth better spent elsewhere.

### Candidates evaluated

| Tool | Cross-LLM | Device portable | Data portable | Self-host | License | Monthly cost |
|---|---|---|---|---|---|---|
| **Mem0** | ✅ Chrome extension covers 7+ LLMs | ✅ Cloud-hosted API | ✅ pg_dump + JSON API | ✅ Apache 2.0 | Apache 2.0 | ₹0 self-hosted |
| **Hindsight** | ❌ MCP-only (Claude-centric) | ✅ Cloud Postgres | ✅ pg_dump | ✅ MIT | MIT | ₹0 self-hosted |
| **TrueMemory** | ❌ Claude-only (MCP + hooks) | ❌ SQLite = local-only | ✅ cp the .db file | ❌ AGPL-3.0 | AGPL-3.0 | ₹0 |
| **Zep** | ❌ SDK/MCP | ✅ Cloud | ⚠️ Graphiti OSS partial | ❌ Cloud-only platform | Proprietary | ₹2K-8K/mo (credit-based) |
| **Supermemory** | ✅ Plugin support | ✅ Cloud | ❌ No self-host, API export only | ❌ Closed source | Proprietary | ₹0-1,600/mo |
| **Letta (MemGPT)** | ❌ Own runtime | ✅ Postgres backend | ✅ pg_dump | ✅ Apache 2.0 | Apache 2.0 | ₹0-1,700/mo |

### Decision

Mem0 self-hosted. The decisive factor was the **OpenMemory Chrome Extension** — the only tool that auto-injects memory into ChatGPT, Claude, Gemini, Perplexity, Grok, and DeepSeek simultaneously via the browser. No other tool provides cross-LLM portability at the browser level.

### Why alternatives were rejected

- **Hindsight** was the initial #1 pick. Dropped when cross-LLM portability became a hard constraint. MCP is Claude-centric — no browser extension for ChatGPT/Gemini web UIs. Excellent tool, wrong fit.
- **TrueMemory** has the best data portability story (single SQLite file), but SQLite on cloud doesn't support concurrent access from multiple devices. Also AGPL-3.0 blocks commercial use in the trading firm without a separate license.
- **Zep** has strong temporal reasoning (Graphiti engine) but credit-based pricing is hostile to budgeting — auto-tops up when balance drops below 20%. Self-hosting Graphiti alone requires Neo4j + significant setup without the managed platform features.
- **Supermemory** is closed source with no self-hosting. Fails data portability hard constraint.
- **Letta** is an agent runtime that happens to have memory, not a memory layer you plug into existing tools. Overengineered for "remember my context across LLMs."

### Consequences

- **Positive:** Cross-LLM memory on desktop + Android. Self-hosted = zero per-memory charges. Apache 2.0 = no commercial restrictions. Full pg_dump portability.
- **Negative:** iOS non-Claude LLMs remain a gap (no Chrome extensions on iOS). OpenMemory extension needs forking to point at self-hosted server. Self-hosted means self-maintained (backups, updates, monitoring).
- **Accepted risk:** Mem0 is YC-backed with 48K+ GitHub stars — unlikely to abandon, but if they do, the self-hosted version is Apache 2.0 and the data is in Postgres.

---
