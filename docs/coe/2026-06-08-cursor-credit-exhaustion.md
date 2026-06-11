# COE: A long-lived Cursor session exhausted a month's plan credits in half a day

- **Date:** 2026-06-08
- **Author(s):** the operator (detected — credit balance), agent (analysis + fix)
- **Severity:** medium *(no production/customer/data impact; operational + budget blast radius — the agent-tooling budget that funds the whole build was spent ~60× faster than planned)*
- **Status:** actions-in-progress
- **Related:** tenet 16 (new) · tenets 1, 13, 15 · `docs/coe/README.md` · `AGENTS.md` Working model + DoD

## Summary

The whole build was being run as a **single, long-lived, stateful Cursor session**.
Because an LLM agent re-sends the *entire conversation transcript* as input tokens on
every turn, cumulative token spend grows **roughly quadratically** with session length
(*context-window amplification*). One ~half-day session exhausted the entire **$60/month
Cursor plan credit** allotment. No code, data, or production impact — but the budget that
funds the build was drained ~60× faster than a month's pace.

## Impact

- A full month's Cursor plan credits gone in ~half a day's work → further agent work this
  cycle is blocked or must move to costlier usage-based billing until reset/upgrade.
- Threatens **build cadence** and the project's cost discipline: the agent tooling is now
  itself a "runaway variable cost" — exactly the failure mode tenets 6/15 guard against for
  cloud/LLM-API spend, but which had **never been applied to the agent tooling itself**.
- No production, customer, security, or data impact. This is an operational/FinOps incident.

## Timeline

- (ongoing) — sessions had been run as long, continuous threads (planning + execution in
  one chat), accumulating large context windows over hours.
- 2026-06-08 — operator observed the **$60/mo plan credits were exhausted** after roughly
  half a day of work.
- 2026-06-08 — root-caused to context-window amplification from monolithic sessions;
  control plane fixed first (tenet 16 + AGENTS Working model + DoD resume-token gate),
  then this COE recorded.

## Detection

**A human caught it via the credit balance** — i.e. *after* the spend, with no proactive
signal. There was **no token/cost guardrail, no context-size awareness, and no Cursor
usage alert**; the only feedback was the depleted balance. A human catch on a billing
surprise is itself a detection gap → see the Detect action below.

## Industry benchmark

- **AWS/Amazon COE benchmark:** the COE should identify why the operating system
  allowed the event, not stop at the immediate operator behavior. This COE meets
  that bar: the root cause is the missing cost model for agent sessions, not "used
  Cursor too long."
- **Google SRE postmortem benchmark:** action items should improve prevention,
  detection, mitigation, coordination, or communication and should feed back into
  the backlog. This COE added prevention through tenet 16 and parked detection
  work for context/cost alerts.
- **Benchmark gap:** the mitigation introduced an over-broad "resume prompt every
  response" rule. The 2026-06-09 recurrence showed the rule needs a checkpoint
  precondition: a resume token is only safe after repo state is current.

## Root cause — 5 Whys

1. **Why were the plan credits exhausted so fast?** The agent re-processed an
   ever-growing transcript on every turn, so token cost per turn kept rising — cumulative
   cost grew ~quadratically with session length (*context-window amplification*).
2. **Why was the session so long?** The working model said "everything runs in a single
   Cursor session" — read (and operated) as *one continuous thread*, not *one short task
   per chat*.
3. **Why a single continuous thread?** State-persistence (checkpointing to `STATUS.md`)
   was specified **only at end-of-session** (the DoD), so there was no mechanism that made
   *starting a fresh chat mid-task* cheap and lossless — continuing the thread was the path
   of least resistance.
4. **Why no cost guardrail on the tooling?** The cost tenets (6 "justify every rupee",
   15 "cap variable cost") had only ever been pointed at **cloud + LLM-API** spend. The
   **agent session itself was never modelled as a metered, usage-based resource**, so no
   cap, alert, or bounding discipline was applied to it.
5. **Why was the tooling outside the cost model?** **Root cause (systemic):** the working
   model optimized for *context continuity* (one session knows everything) and treated the
   chat as free. It never recognised that a stateful conversation **is** a usage-based
   resource with a quadratic cost curve — so the cheapest correctness mechanism (externalize
   state to the repo, keep the live context bounded) was absent, and the expensive default
   (accumulate everything in-context) won.

## Corrective actions

| Action | Type | Owner | Due | Status |
|---|---|---|---|---|
| Add **tenet 16** — stateless, disposable, single-task sessions; checkpoint to the repo; resume token (the systemic control) | Prevent | agent | 2026-06-08 | ✅ done |
| Rewrite the AGENTS **Working model** ("single session" → one surface, short disposable sessions) | Prevent | agent | 2026-06-08 | ✅ done |
| Add a **DoD gate**: checkpoint `STATUS.md` per logical step + emit a Resume prompt only after the checkpoint exists | Prevent | agent | 2026-06-08 | ✅ done; tightened 2026-06-09 after over-broad wording caused a false handoff token |
| Apply the cost model to the tooling: frame the agent session as a metered resource (tenet 16 ties to tenet 15) | Prevent | agent | 2026-06-08 | ✅ done |
| Operator watches the Cursor usage meter; consider a periodic context-size / cost check-in | Detect | the operator | next sessions | ⏳ |
| Automated context-budget / "session getting expensive → checkpoint & restart" signal | Detect | the operator+agent | backlog P2 | ⏳ backlog |
| Mitigate the live incident: from now, one task per chat, resume from `STATUS.md` (cost per session bounded) | Mitigate | agent | 2026-06-08 | ✅ in effect |

## Lessons learned

**A stateful conversation is a metered, usage-based resource with a quadratic cost curve —
treat it like one.** The cheap, correct mechanism is the **Twelve-Factor stateless-process +
backing-store** pattern: keep the live context bounded, externalize state to durable storage
(here, the repo — tenet 1), and resume via a **continuation token** rather than by replaying
an ever-growing transcript. The anti-pattern is the **monolithic long-lived session**; the
pattern is **stateless single-task sessions + checkpoint/restore**. Also: a cost discipline
is only as good as its *scope* — tenets 6/15 were sound but had never been pointed at the
agent tooling itself, so the one unmetered resource is the one that spiralled. Mirrored into
`interview_packet.md`; detection-layer follow-up parked in `BACKLOG.md` (P2).
