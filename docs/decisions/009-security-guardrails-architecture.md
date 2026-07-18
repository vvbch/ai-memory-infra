# ADR 009: Security guardrails architecture

**Status:** Accepted — **partially implemented** (see Implementation status below)
**Date:** 2026-06-04

### Context

The memory system stores personal facts, venture details, financial information, and potentially sensitive data extracted from conversations. Security needs to be built in, not bolted on. Additionally, "safety/guardrails" is on the 2026 AI hiring checklist.

### Decision

Defense-in-depth across five layers:

1. **Network**: UFW firewall (80/443/22 only). Postgres, Neo4j, Prometheus on Docker internal network only — not exposed to public internet. Only Caddy faces the internet.
2. **Transport**: HTTPS everywhere via Caddy auto-provisioned Let's Encrypt TLS. HSTS headers. No plaintext HTTP.
3. **Authentication**: JWT-based auth on all Mem0 API endpoints. Admin API key for privileged operations (bulk delete, export). Basic auth on Neo4j Browser and Grafana via Caddy.
4. **Data safety**: Input validation rejects memory writes containing API keys, passwords, credit card number patterns (regex filter). PII detection flags Aadhaar, PAN numbers during extraction — flagged for review, not stored.
5. **Access control**: CORS policy allows only the self-hosted domain + Chrome extension ID. Rate limiting on API endpoints via Caddy.

### Implementation status (honest — weekly scan 2026-07-18)

| Layer | Status |
|---|---|
| 1 Network, 2 Transport, 3 Auth | **In place** on the live stack |
| 4 PII / secret regex on write path | **[target]** — helpers exist in `src/eval/guardrails.py` (eval-only today); not wired into Mem0/proxy writes |
| 5 CORS allowlist + Caddy rate limit | **[target]** — Caddy CORS rules commented; rate limit needs custom Caddy build (see `infra/Caddyfile`) |

Canonical tags: `AGENTS.md` / `contract/practices.yaml` security practice.

### What this does NOT cover

- End-to-end encryption of memories at rest (Postgres standard encryption is sufficient for personal use)
- Multi-user access control (single user system)
- SOC 2 / HIPAA compliance (not needed)

### Consequences

- **Positive:** Prevents accidental secret leakage into knowledge graph. Prevents unauthorized access. PII filtering is particularly important given Indian financial data (Aadhaar, PAN). Demonstrates security awareness in portfolio.
- **Negative:** Regex-based PII detection has false positives/negatives. Not a substitute for proper data classification. Mitigated by the guardrail eval tests that verify filter accuracy *once the filter is on the write path*.
