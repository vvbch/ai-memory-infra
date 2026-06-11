# Acceptance probe results

**Overall:** FAIL

## backdated_recency — FAIL
- Expected: max event_date -> implementation started (2026-06-10)
- latest_text: 
- candidate_count: 0

## structured_filter — PASS
- Expected: open_item metadata filter returns probe follow-up
- metadata_filter_hit: True
- pure_vector_hit: False
- note: Pure vector search alone may miss open items — metadata filter required (documented contract limit).

## entity_collision — FAIL
- Expected: Among Jordan hits, inline qualifier rerank picks project contact, not team lead's sibling
- best_jordan_text: 
- top_texts: ["ADR 034: Remote MCP HTTP endpoint for Claude mobile\n\n**Status:** Accepted — **§2 (auth v1 = static bearer) superseded by ADR 035**\n(claude.ai's connector UI accepts only OAuth/no-auth; see COE\n2026-06-10-claude-connector-auth-assumption). Endpoint architecture stands.\n**Date:** 2026-06-10\n**Deciders:** the operator (operator goal 2 of 2026-06-10 day plan)\n**Supersedes / extends:** ADR 025 (local stdio proxy only)", 'ADR 037: Write-path idempotency & dedup contract\n\nDate: 2026-06-10', "ADR 024: Phase 3 — fork mem0's OpenMemory Chrome extension (rewire to our self-hosted server) > Consequences (reversible — tenet 12 / 17)\n\n- **Exit path:** it's MIT and isolated in its own repo — archive/delete that repo or remove\n  any browser-store listing to back it out. No new paid vendor, no account, no lock-in.\n- **We own maintenance.** Upstream is archived, and chat sites change their DOM, so the\n  per-site selectors will rot — but that is true of *any* browser-injection extension and is\n  exactly the work the fork saves us from writing in the first place. Mitigation: keep the\n  per-site config centralized; fix selectors as sites change (a known, bounded chore).\n- **No firm IP (tenet 5):** this is public platform code only.\n- **Docs/DoD:** `architecture.md` already lists the Chrome extension; `STATUS.md` Phase/Next\n  action updated. The infra repo keeps only a pointer under `extension/`; source lives in the\n  new private extension repo.\n\n*(Pairs with ADR 004 — ChromeOS as the first-class mobile path for this extension; Android is\nbest-effort only since Kiwi's Jan-2025 archival.)*", 'ADR 017: Password manager + nominee (emergency-access) strategy > Context\n\nThe estate/exit path (tenet 12, `docs/decommission.md`) assumes credentials live\nin a password manager — *not* in either git repo — and that a **nominee** can get\nin if the operator can\'t. Three billable accounts must be reachable to stop all spend:\nDigitalOcean, Cloudflare, OpenAI; plus the SSH private-key passphrase.\n\nHard constraints:\n\n- **No secret ever enters a repo** (public or private). Git history is permanent,\n  both repos are Google-Drive-synced (tenet 11 → many copies), and `AGENTS.md`\n  forbids secrets in code/commits/logs. The private repo is therefore the right\n  home for the *runbook*, never the *credentials*.\n- A repo\'s access model (clone + share) is the opposite of what a secret needs, so\n  "grant the nominee access via the private repo" is rejected for credentials. The\n  nominee gets the **runbook** from the repo and the **credentials** from the\n  password manager\'s emergency-access channel.\n\nThis is a tenet-12 vendor decision, so candidates are weighed on total cost (incl.\nexit cost), portability/lock-in, reliability/track record, company viability, and\necosystem. Facts below verified 2026-06-07 from each vendor\'s docs/pricing pages\n(tenet 8).', "ADR 007: Eval framework design > Consequences\n\n- **Positive:** Quantitative proof that the system works. Cross-LLM cost-vs-quality comparison is a concrete, reproducible result interviewers can examine. Guardrail tests prove security isn't just claimed but verified.\n- **Negative:** Gold-standard datasets must be hand-labeled — initial effort of ~2 days. Datasets need periodic refresh as memories grow."]
- jordan_hit_count: 0

Deleted 0 probe memories.