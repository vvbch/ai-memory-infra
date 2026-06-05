# ADR 006: Two-repo separation

**Status:** Accepted
**Date:** 2026-06-04

### Context

The project serves two purposes: (1) a production tool for multiple ventures, and (2) a public portfolio showcase. These purposes conflict when the production tool contains proprietary firm logic.

### Decision

Two-repo pattern from day one:

| Repo | Visibility | Owner | Contents |
|---|---|---|---|
| `ai-memory-infra` | Public | Chandra (personal) | Platform infrastructure + LifeGraph POC |
| `trading-firm-graph` | Private | LLP entity | Market world model, strategies, backtest results |
| `social-media-graph` | Private | Content firm | Audience analytics, content strategy |
| `ria-graph` | Private | RIA entity | Advisory compliance, client data |

### How they connect

Private repos import the public repo's API client as a dependency (or hit the REST API directly). They create their own Neo4j node labels in the shared instance. Clean separation — platform team ships infrastructure, domain teams build on it.

### Why not a monorepo with access controls

- GitHub doesn't support per-directory visibility. A monorepo is either all public or all private.
- Making the whole thing private kills the portfolio value.
- Splitting later (after code is intertwined) is painful. Starting separated is cheap.

### Consequences

- **Positive:** Public repo is always safe to share. Each firm owns only its code. IP boundaries are clean from day one. Vijaya can work on `trading-firm-graph` without access to RIA code.
- **Negative:** Two repos to maintain. Cross-repo testing is harder (need to mock the API or run integration tests against a shared test stack). Mitigated by the REST API contract being simple and stable.

---
