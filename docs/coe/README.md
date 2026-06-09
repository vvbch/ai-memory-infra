# Corrections of Errors (COE)

> How we learn from failure — defects, incidents, tenet/rule violations, security
> near-misses, or the agent not adhering to guidance. **Mechanism over blame**
> (tenet 14).

## When to open a COE

- Any tenet/rule violation, shipped defect, incident, security/data near-miss, or
  repeated agent non-adherence — anything **beyond trivial**.
- Trivial issues: a one-line note in the relevant doc/PR is enough. Match depth to
  blast radius (tenets 13 & 8).

## How

1. Copy `TEMPLATE.md` → `docs/coe/YYYY-MM-DD-short-slug.md`.
2. Fill it in: **impact, timeline, detection, industry benchmark, 5-whys to a
   *systemic* root cause,** and corrective actions split **Prevent / Detect /
   Mitigate** (owner · date · status). Benchmark at least against AWS/Amazon COE
   practice and Google SRE blameless postmortem practice so we know whether the
   response is merely documented or actually operationally strong.
3. **Fix the control plane before the data plane** — the rule / spec / mechanism
   that *allowed* it, before the instance, or the instance regenerates.
4. Land the systemic fix in a **tenet or ADR**; land the lesson in
   `../interview_packet.md`; rank follow-ups in `../planning/BACKLOG.md`.
5. **Blameless** — the target is the system, never the person or the agent.

## Index

| Date | COE | Summary | Systemic fix |
|---|---|---|---|
| 2026-06-07 | `2026-06-07-cursor-rule-drift.md` | A Cursor rules file drifted into a duplicated rules summary (tenets 2/10) | ADR 018 + tenet 2 boundary + DoD row |
| 2026-06-08 | `2026-06-08-cursor-credit-exhaustion.md` | A long-lived stateful Cursor session burned a month's plan credits in half a day (context-window amplification) | tenet 16 (stateless/checkpointed sessions) + AGENTS Working model + DoD resume-token gate |
| 2026-06-08 | `2026-06-08-atomic-handoff-failure.md` | Completed Phase 3 work was documented locally but not atomically committed/pushed across every touched repo | AGENTS completion gate now explicitly covers every touched repo incl. package repos; final all-repo handoff check parked |
| 2026-06-09 | `2026-06-09-session-handoff-omission.md` | Phase 4 work was verified but final response omitted commit/push and a fresh-session resume prompt | AGENTS final-response gate sharpened: pushed commits or named blockers + copy-paste resume prompt |
| 2026-06-09 | `2026-06-09-concierge-handoff-regression.md` | The next session repeated the handoff pattern and added cognitive load with vague MCP-check instructions plus an uncheckpointed resume prompt | Concierge action template + checkpoint-gated resume prompt + final handoff verifier promoted from P2 to P1 |
| 2026-06-09 | `2026-06-09-model-dependent-completion-gate.md` | Switching to GPT-5.5 (reasoning=high) ended a session without commit/push; proved the prose completion gate is model-dependent, not deterministic | ADR 027 — harness-level Cursor `stop` hook (`completion_gate.py`) enforces commit/push for any model; closes the long-promised P1 repo handoff verifier |
| 2026-06-09 | `2026-06-09-ide-coupled-completion-gate.md` | The ADR 027 fix introduced a *new* tenet-2 violation: the gate was written into `ai-memory-infra/.cursor/`, coupling it to Cursor — and worse, that path is not the open workspace root, so the "hard layer" was likely never loading | ADR 030 — portable script (`scripts/`) + thin per-IDE adapters generated at the workspace root by `install_ide_hooks.py`; same pattern carries the `sessionStart` bootstrap |
| 2026-06-10 | `2026-06-10-status-snapshot-log-drift.md` | STATUS.md (a snapshot, overwritten each session) accreted ~25 "Prior update" blocks across ~20 sessions and became a second log duplicating BUILD-LOG (tenets 10/16) — manual process drift, caught by the operator | Doc contracts get deterministic validators like code: `scripts/check_status_snapshot.py` shape gate in pre-commit + CI; STATUS trimmed to snapshot; DoD row clarified |
| 2026-06-09 | `2026-06-09-extension-memory-identity-drift.md` | ADR 028 (one `user_id`, `source` is the discriminator) was committed in the control plane but never propagated to the Chrome extension or MCP proxy — the busiest write surface kept the legacy `chrome-extension-user` + top-level (dropped) `source`. Operator caught both the defect and the meta-pattern: aggressive on infra/private, absent on the plugin | ADR 031 — a cross-cutting decision is a contract across every consumer repo: conformance section in the ADR + DoD row + `scripts/check_memory_contract.py` detect gate |
