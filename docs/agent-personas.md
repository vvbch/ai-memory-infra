# Agent Personas

This is the product-design gate before building more skills/tools. The memory
layer is shared infrastructure, but agents need clear jobs. A skill without an
agent owner is just a command with no success criteria.

## Design Inputs From COEs

The recent COEs shaped this design:

- `2026-06-08-cursor-credit-exhaustion.md`: agents must keep context bounded,
  checkpoint durable state, and avoid long stateful threads.
- `2026-06-08-atomic-handoff-failure.md`: a handoff is only real when every
  touched repo or system of record is updated, verified, and pushed.
- `2026-06-09-session-handoff-omission.md`: final responses need an explicit
  checkpoint contract, not agent memory.
- `2026-06-09-concierge-handoff-regression.md`: operator-facing work must be
  concierge-formatted: purpose, exact action, visible success, and wait point.

So the first build rule is: every skill must declare its owning persona, what it
may store, what it may retrieve, and what proves success.

## Primary Personas

### 1. Build Agent

**Job:** implement and maintain the code, infrastructure, tests, docs, and
deployment workflow.

**Uses the memory layer for:**

- Prior build decisions, ADR outcomes, known gotchas, and environment quirks.
- Error patterns, failed fixes, recovery steps, and verification commands.
- Cross-repo handoff facts: which repo was touched, what was pushed, and what
  remains next.

**May store:**

- Durable technical facts: "PowerShell needs `npm.cmd` here", "content scripts
  must call the background relay for cross-origin API fetches", "repo-health was
  green before commit".
- Concise lessons from COEs and debugging sessions.
- Pushed commit identifiers and verification outcomes.

**Must not store:**

- Secrets, API keys, passwords, private key material, or raw vault values.
- Long transcripts that duplicate `STATUS.md`, ADRs, or build logs.
- Unverified hypotheses as durable facts.

**Success criteria:**

- A fresh session can resume from repo files plus targeted memories without
  replaying a long chat.
- Completed reversible work is verified, committed, pushed, and checkpointed.
- Any operator step is delegated only when the agent cannot do it itself.

### 2. Research and Strategy Agent

**Job:** evaluate product direction, vendors, models, architecture trade-offs,
costs, and roadmap sequencing before implementation.

**Uses the memory layer for:**

- Dated external facts and source summaries.
- Prior trade-off decisions, rejected paths, and revisit triggers.
- Portfolio/interview framing: what decision demonstrates which competency.

**May store:**

- Short research conclusions with date, source class, and confidence.
- Decision rationale that will later become an ADR or backlog item.
- Explicit revisit conditions, such as "re-check Claude remote MCP when HTTP
  endpoint work starts".

**Must not store:**

- Full web dumps, article copies, or stale source text.
- Firm IP, trading strategy details, or private financial specifics that belong
  outside this public repo.
- Decisions that have not been accepted or checkpointed.

**Success criteria:**

- The next build step is clear, scoped, and tied to an owner.
- Vendor/model choices are reversible or have an ADR before adoption.
- Research memories are dated so stale facts are easy to challenge.

### 3. Operator Assistant

**Job:** reduce Chandra's cognitive load for console work, account setup,
routine checks, reminders, and personal operating context.

**Uses the memory layer for:**

- Preferences: concierge mode, one step at a time, plain English.
- Non-secret account custody facts: which Bitwarden folder holds project
  credentials, which checks exist, which UI path was last verified.
- Pending operator actions and visible success conditions.

**May store:**

- Stable preferences and working agreements.
- Non-secret task state: "Cursor lists workspace MCP server `ai-memory`".
- Reminder-style facts with dates and trigger conditions.

**Must not store:**

- Passwords, API keys, recovery codes, or copied secret values.
- Medical, financial, or family details unless Chandra explicitly asks and the
  detail is necessary for the task.
- Multi-step instruction dumps when a single next action is required.

**Success criteria:**

- Chandra gets exactly one action when action is needed.
- The action includes purpose, exact UI path or command, visible success, and
  "tell me what you see".
- No resume prompt is emitted while waiting on Chandra inside the same active
  flow.

## Supporting Role: Memory Steward

This is not a fourth user-facing agent at first. It is a governance role that can
later become skills under the Build Agent.

**Job:** keep memories useful, scoped, deduplicated, and safe.

**Responsibilities:**

- Enforce metadata: persona owner, source surface, date, sensitivity, and
  venture tag where relevant.
- Detect conflicts between memory and repo truth; repo files win.
- Prefer small durable facts over transcript-sized memories.
- Surface stale memories for refresh instead of silently trusting them.

**Success criteria:**

- Search returns actionable facts, not duplicated chat debris.
- Sensitive values are absent from memory.
- Memory can explain why a fact is believed and where canonical truth lives.

## First Skill Build Order

1. **Build Agent: session checkpoint skill.** Capture the current work item,
   verification, touched repos, and next action in the right repo docs.
2. **Build Agent: repo handoff verifier.** Mechanically check dirty/ahead/behind
   state for touched repos before final response.
3. **Operator Assistant: concierge action formatter.** Turn an unavoidable
   operator step into purpose + exact action + visible success + wait point.
4. **Research and Strategy Agent: decision capture skill.** Convert a researched
   choice into an ADR/backlog-ready summary with source dates and revisit trigger.
5. **Memory Steward: memory hygiene checks.** Flag secrets, oversized memories,
   missing owner metadata, and stale facts.

This order directly follows the COEs: first fix handoff and operator-action
mechanics, then expand capability.

## Acceptance Criteria For Future Skills

Before a skill is built, it must answer:

- Which persona owns it?
- What exact user pain does it remove?
- What may it store and retrieve?
- What must it never store?
- What is the visible success condition?
- Which repo/doc is canonical if memory and files disagree?

If any answer is unclear, do not build the skill yet.
