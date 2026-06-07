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
2. Fill it in: **impact, timeline, detection, 5-whys to a *systemic* root cause,**
   and corrective actions split **Prevent / Detect / Mitigate** (owner · date ·
   status).
3. **Fix the control plane before the data plane** — the rule / spec / mechanism
   that *allowed* it, before the instance, or the instance regenerates.
4. Land the systemic fix in a **tenet or ADR**; land the lesson in
   `../interview_packet.md`; rank follow-ups in `../planning/BACKLOG.md`.
5. **Blameless** — the target is the system, never the person or the agent.

## Index

| Date | COE | Summary | Systemic fix |
|---|---|---|---|
| 2026-06-07 | `2026-06-07-cursor-rule-drift.md` | A Cursor rules file drifted into a duplicated rules summary (tenets 2/10) | ADR 018 + tenet 2 boundary + DoD row |
