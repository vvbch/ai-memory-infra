# Architecture

Self-hosted, cross-platform AI memory infrastructure. A persistent memory layer
plus knowledge graph that sits underneath native LLM interfaces — no custom chat
UI, no per-conversation API cost. See `docs/decisions/` for the reasoning behind
each choice and `docs/tenets.md` for the principles that constrain them.

## System overview

```mermaid
flowchart TB
    subgraph Devices["Devices — native LLM UIs, unchanged"]
        D1["Desktop / ChromeOS Chromium<br/>OpenMemory extension — FULL coverage"]
        D2["Android<br/>best-effort (Kiwi archived Jan-2025;<br/>Edge Canary / Quetta) — see ADR 004"]
        D3["iOS<br/>Claude app via MCP only;<br/>other LLMs = known gap"]
        D4["Claude Code / Cursor / VS Code<br/>via MCP"]
        D5["Future tools<br/>via REST API"]
    end

    subgraph VPS["VPS — Bangalore (DO BLR1)"]
        CADDY["Caddy<br/>auto-HTTPS reverse proxy"]
        subgraph Compose["Docker Compose"]
            API["mem0-api<br/>FastAPI: REST + MCP"]
            PG[("PostgreSQL 16<br/>+ pgvector")]
            NEO[("Neo4j<br/>dual namespace:<br/>Mem0 graph + LifeGraph")]
            DASH["mem0-dash"]
            PROM["prometheus"]
            GRAF["grafana"]
        end
        BACKUP["Daily backup:<br/>pg_dump + neo4j dump → object storage"]
    end

    LLM["DeepSeek V4 Flash<br/>fact extraction (OpenAI-compatible)"]

    D1 & D2 & D3 & D4 & D5 --> CADDY
    CADDY --> API
    API --> PG
    API --> NEO
    API --> DASH
    API -.extraction.-> LLM
    PROM --> GRAF
    API --> PROM
    PG --> BACKUP
    NEO --> BACKUP
```

## Subdomains (behind Caddy, HTTPS)

| Subdomain | Service | Notes |
|---|---|---|
| `memory.{domain}` | Mem0 API (REST + MCP) | JWT auth; CORS allowlist |
| `dash.{domain}`   | Mem0 dashboard | basic auth |
| `graph.{domain}`  | Neo4j Browser | basic auth |
| `monitor.{domain}`| Grafana | basic auth |

Only Caddy faces the internet; Postgres, Neo4j, and Prometheus stay on the
Docker internal network (ADR 009).

## Coverage matrix

| Surface | Memory path | Status |
|---|---|---|
| Desktop / ChromeOS | OpenMemory Chrome extension | Full |
| Android | Edge Canary / Quetta + extension | Best-effort (ADR 004) |
| iOS — Claude | Remote MCP connector | Full |
| iOS — ChatGPT/Gemini/DeepSeek | none | Known gap |
| Claude Code / Cursor / VS Code | MCP client | Full |
| Any future tool | REST API | Full |

## Degradation

VPS down ⇒ every LLM still works with its own native memory; the extension
fails silently, the MCP connector degrades gracefully. No data loss (Postgres
persists to disk + daily backups). Enrichment resumes on recovery (tenet 4).
