# COE: STATUS.md drifted from snapshot to a second log

- **Date:** 2026-06-10
- **Author(s):** Build Agent (session with operator)
- **Severity:** medium *(no data loss; but the resume surface — read at every session start — bloated ~9x and began duplicating BUILD-LOG, the exact context-cost + drift failure tenets 16 and 10 exist to prevent)*
- **Status:** actions-in-progress
- **Related:** tenet 10 (no drift), tenet 16 (stateless sessions / checkpoint to files), AGENTS.md DoD "End of any working session" row, COE 2026-06-09-model-dependent-completion-gate (same systemic class), `scripts/check_status_snapshot.py`

## Summary

`docs/planning/STATUS.md` is contractually a **resumable snapshot, overwritten each
session** (its own header says so); the append-only journal is the private
`BUILD-LOG.md`. In practice, sessions *prepended* new "Last updated" blocks while
keeping the old ones as `**Prior update:**` blocks, and appended new dated
`## Last decisions` / `## Done this session` sections instead of replacing them.
By 2026-06-10 STATUS.md was ~1,343 lines / ~112 KB with ~25 prior-update blocks —
a second, partially-duplicated log. No hook or script writes STATUS.md (verified:
`session_bootstrap.py` only reads it; `completion_gate.py` only instructs the
agent to update it; `session_checkpoint.py` writes BUILD-LOG only) — this was
agent-by-hand process drift against a prose-only rule.

## Impact

- **Token/context cost (tenet 16):** every resume path ("read STATUS.md first")
  pulls a 112 KB file whose useful snapshot content is <20% of it — the same
  context-amplification failure mode that burned a month of credits in COE
  2026-06-08, reintroduced at the file layer.
- **Drift risk (tenet 10):** the same session history now exists in three shapes
  (STATUS prior-update blocks, BUILD-LOG entries, BUILD-JOURNEY summaries) that
  nothing keeps in agreement.
- **Resume quality:** the "read this first" file buried *current* state under
  history; "Plain English — where we are" still carried completed 2026-06-07
  setup checklists.
- No production, data, or customer impact.

## Timeline

- `2026-06-06..07` — STATUS.md created as snapshot + DoD row written ("overwrite:
  current phase, last decisions, open blockers, next action").
- `2026-06-07..08` — first sessions keep superseded narrative as "Prior update"
  blocks "for safety"; dated `## Last decisions (…)` sections start accumulating.
- `2026-06-08..10` — pattern compounds across ~20 sessions; file reaches ~1,343
  lines. Each session's agent reasonably mimics the inherited file shape.
- `2026-06-10` — **operator detects it** ("the status file has become a log in
  addition to build_log") and asks whether automation is writing it; investigation
  confirms it is manual process drift; this COE + gate shipped same session.

## Detection

**Human catch (operator), ~3 days and ~20 sessions after onset.** Nothing watched
document shape: pre-commit validates integrity + secrets, the completion gate
validates commit/push, CI was a stub. A shape violation that compounds slowly is
exactly what a deterministic gate should catch → Detect action below.

## Industry benchmark

- **Amazon COE practice:** blame-free, 5-Whys to a systemic cause, actions with
  owners — met by this document. Amazon's "mechanisms, not good intentions"
  maxim is the core lesson: the overwrite rule was an intention, not a mechanism.
- **Google SRE postmortem practice:** written impact/timeline/root cause and
  action items spanning prevention/detection — met. SRE would additionally note
  the *detection gap* (human catch) as its own action item — adopted below.
- **Industry doc-as-code practice:** docs that carry contracts get linted in CI
  (markdownlint, Vale, custom checkers) exactly like code. We lint code (ruff,
  mypy, gitleaks) but had zero doc-shape checks — below benchmark until now.

## Root cause — 5 Whys

1. Why did STATUS.md become a log? → Sessions prepended "Prior update" blocks and
   appended dated section copies instead of overwriting.
2. Why did they prepend instead of overwrite? → Loss-aversion under a prose rule:
   deleting prior narrative *feels* like destroying information, so each agent kept
   it — even though BUILD-LOG and git history already preserve all of it.
3. Why did loss-aversion win repeatedly? → The inherited file shape *taught* each
   new session the wrong convention (agents mimic what they read), and the DoD row
   "STATUS.md last-decisions" reads as an append target if you don't hold the
   overwrite contract in mind.
4. Why did nothing stop the compounding? → No mechanism asserted document shape;
   our deterministic gates (pre-commit, completion gate) covered commit hygiene
   and secrets, never doc contracts.
5. Why no mechanism for docs? → **Root cause (systemic):** the control plane
   treated *code* contracts as needing deterministic validators but *document*
   contracts as self-policing prose. Any contract that matters decays under model
   variance unless a machine checks it (same root as COE
   2026-06-09-model-dependent-completion-gate, now applied to docs).

## Corrective actions

| Action | Type (Prevent / Detect / Mitigate) | Owner | Due | Status |
|---|---|---|---|---|
| Trim STATUS.md back to a pure snapshot (history already lives in BUILD-LOG + git; nothing deleted from the record) | Mitigate | Build Agent | 2026-06-10 | done |
| `scripts/check_status_snapshot.py` — deterministic shape gate (no "Prior update", one "Last updated", singleton session sections, 400-line cap), TDD'd | Prevent | Build Agent | 2026-06-10 | done |
| Wire the gate into pre-commit (gate 3) and CI so drift cannot land | Detect | Build Agent | 2026-06-10 | done |
| Clarify the AGENTS.md DoD row: STATUS = overwrite; superseded narrative goes to BUILD-LOG *in the same step* | Prevent | Build Agent | 2026-06-10 | done |
| Weekly repo-scan automation reviews doc shape + redundancy across all docs (catches the *next* slow-compounding drift class) | Detect | Weekly scan workflow | 2026-06-13 (first run) | in progress |

## Lessons learned

A document with a contract is code: lint it. Prose rules executed by LLM judgment
decay one harmless-looking exception at a time, and each session inherits the
previous session's exceptions as the new normal. The fix is never "remind the
agent harder" — it is a deterministic validator at the choke point (pre-commit/CI),
plus making the *correct* shape the inherited example. Interview-worthy: mirrored
into the private `interview_packet.md`.
