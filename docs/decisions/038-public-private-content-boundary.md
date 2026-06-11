# ADR 038: Public/private content boundary (operator sanitization)

Date: 2026-06-11

## Status

Accepted

## Context

Tenet 5 requires the public `ai-memory-infra` repo to contain **platform
infrastructure and LifeGraph POC only** — no firm IP, operator identity, venture
details, job-search framing, or personal ops facts. `AGENTS.md` and many docs had
drifted: operator biography, concierge collaboration rules, venture names, live
domain/`user_id`, Bitwarden folder paths, interview packet references, and real
names in seed/eval fixtures were all visible to strangers browsing the public repo.

Git history retains prior content until explicitly rewritten (one-way door).

## Decision

1. **Public repo carries engineering context only:** tenets, architecture, ADRs,
   contracts, generic operator-delegation *patterns*, build status, and **synthetic**
   POC fixtures (LifeGraph seed, eval gold, test data).

2. **Private `ai-memory-infra-private` carries operator context:**
   - `OPERATOR.md` — identity, collaboration style, live `user_id`/domain overrides
   - `ventures.md` — venture tag definitions and import keyword hints
   - `docs/interview_packet.md` and `docs/interviews/` — portfolio narrative
   - `docs/automation/interview-refresh-prompt.md` — moved from public repo
   - `docs/security/secrets-catalog.md`, `docs/financial-decisions.md` (unchanged)

3. **Public code defaults are generic:** `DEFAULT_USER_ID=primary-user`,
   `memory.example.com` / `mcp.example.com`. Operators set `AI_MEMORY_USER_ID` and
   `AI_MEMORY_BASE_URL` in private env (documented in `OPERATOR.md`).

4. **DoD interview_packet triggers** point at the private repo path; public docs
   never require updating interview materials for engineering-only changes.

5. **Entity-collision examples** use synthetic names (`Jordan`, `project contact`)
   not real family or contacts.

## Consequences

- **Positive:** public repo is safe to share with recruiters/OSS visitors; agent
  workflow preserved for operators with private-repo access; contract checks stay
  mechanical on `primary-user`.
- **Negative:** live deployment must keep env overrides aligned with the bank already
  seeded under the operator's real `user_id` (documented privately). Extension and
  MCP clients need matching env until a migration ADR is accepted.
- **History:** prior commits still contain personal data until operator chooses
  filter-repo, delete-and-recreate, or accept (see session handoff list).

## Propagation / conformance

- [x] `AGENTS.md`, `contract/dod.yaml`, `contract/tenets.yaml`
- [x] `src/mcp_proxy/client.py`, `scripts/check_memory_contract.py`
- [x] `ai-memory-extension` `DEFAULT_USER_ID` / default server URL
- [x] LifeGraph seed, eval gold, acceptance probe fixtures
- [x] Private `OPERATOR.md`, `ventures.md`, interview automation prompt
