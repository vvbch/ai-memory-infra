# ADR 006: Two-repo separation

**Status:** Accepted (amended 2026-06-11, ADR 038)
**Date:** 2026-06-04

### Context

The project serves two purposes: (1) a production memory platform, and (2) keeping
firm-specific logic private. These conflict when proprietary venture logic lives in
the same repo as public infrastructure.

### Decision

Two-repo pattern from day one:

| Repo | Visibility | Contents |
|---|---|---|
| `ai-memory-infra` | Public | Platform infrastructure + LifeGraph POC (synthetic fixtures) |
| `ai-memory-infra-private` | Private | Operator profile, venture definitions, secrets catalog, interview materials |
| Domain venture repos | Private | Firm-specific graph logic (trading, content, advisory, etc.) |

Private repos consume the public REST API or client library. Domain teams own their
code; the platform team owns shared infra.

### Why not a monorepo with access controls

GitHub does not support per-directory visibility. Splitting later is painful; starting
separated is cheap.

### Consequences

- **Positive:** public repo is always safe to share. IP boundaries are clean.
- **Negative:** cross-repo testing needs mocks or a shared test stack. Mitigated by a
  stable REST contract.
