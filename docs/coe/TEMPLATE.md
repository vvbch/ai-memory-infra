# COE: <title>

- **Date:** YYYY-MM-DD
- **Author(s):**
- **Severity:** <low | medium | high>  *(by blast radius, not effort spent)*
- **Status:** <open | actions-in-progress | closed>
- **Related:** <ADR / tenet / PR / commit links>

## Summary

<2–3 sentences: what happened and why it matters.>

## Impact

<Who/what was affected, scope, and duration. "No production/customer impact, but
the risk was X" is a valid and useful impact statement.>

## Timeline

- `<timestamp>` — <event>
- `<timestamp>` — <detected>
- `<timestamp>` — <fixed>

## Detection

<How was it caught — monitoring, a test, or a human? A **human catch** is itself a
detection gap → add a Detect action below.>

## Industry benchmark

<Compare against external operating standards. At minimum check: AWS/Amazon COE
practice (blame-free 5 Whys, action owners, prevent recurrence) and Google SRE
postmortem practice (written impact/timeline/root cause, blamelessness, action
items that improve prevention, detection, mitigation, coordination, or
communication). State where this incident response meets the benchmark and where
it falls short.>

## Root cause — 5 Whys

1. Why …? →
2. Why …? →
3. Why …? →
4. Why …? →
5. Why …? → **Root cause (systemic):** …

## Corrective actions

| Action | Type (Prevent / Detect / Mitigate) | Owner | Due | Status |
|---|---|---|---|---|
| | | | | |

## Lessons learned

<The transferable principle. If interview-worthy, mirror into
`../interview_packet.md`. Park follow-ups in `../planning/BACKLOG.md`.>
