# Agent Personas

Product-design gate before building more skills/tools. The memory layer is shared
infrastructure, but agents need clear jobs. A skill without an agent owner is just a
command with no success criteria.

## Design Inputs From COEs

Recent COEs shaped this design: bounded sessions (2026-06-08), atomic handoff
(2026-06-08), explicit checkpoint contract (2026-06-09), and delegated-action
formatting (2026-06-09). Every skill must declare its owning persona, what it may
store, what it may retrieve, and what proves success.

## Primary Personas

### 1. Build Agent

**Job:** implement and maintain code, infrastructure, tests, docs, and deployment.

**Uses memory for:** ADR outcomes, gotchas, verification commands, cross-repo handoff
facts.

**Must not store:** secrets, long transcripts duplicating `STATUS.md`/ADRs.

**Success:** fresh session resumes from repo files; reversible work verified,
committed, pushed, checkpointed.

### 2. Research and Strategy Agent

**Job:** evaluate vendors, models, architecture trade-offs, roadmap sequencing.

**Uses memory for:** dated external facts, rejected paths, revisit triggers.

**Must not store:** full web dumps, firm IP, private financial specifics.

**Success:** next build step is clear, scoped, and tied to an owner; choices are
reversible or ADR-backed.

### 3. Operator Assistant

**Job:** reduce operator cognitive load for console work, account setup, reminders,
and personal operating context.

**Uses memory for:** stable preferences, non-secret task state, reminder facts.

**Must not store:** passwords, API keys, medical/financial/family details unless
explicitly required for the task.

**Success:** one delegated action at a time with purpose, path, success condition,
and wait point. Operator-specific collaboration rules live in private `OPERATOR.md`.

## Supporting Role: Memory Steward

Governance role (future skills under Build Agent): enforce metadata, detect
conflicts with repo truth, flag stale or oversized memories.

## First Skill Build Order

1. ✅ Session checkpoint (`scripts/session_checkpoint.py`)
2. ✅ Repo handoff verifier (`scripts/completion_gate.py`, ADR 027/030)
3. ✅ Delegated-action formatter (`scripts/operator_action.py`)
4. ✅ Memory Daily Driver (`scripts/memory.py`)
5. **Deferred:** memory hygiene checks
6. ✅ Credential handoff (`scripts/ssh_unlock.py`)

## Acceptance Criteria For Future Skills

Before building: owning persona, pain removed, store/retrieve bounds, success
condition, canonical doc if memory and files disagree.
