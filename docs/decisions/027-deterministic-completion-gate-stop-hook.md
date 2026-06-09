# ADR 027: Deterministic completion gate via a Cursor `stop` hook

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** Chandra (operator), Cursor agent
**Related:** Tenets 1, 2, 11, 14, 16, 17; ADR 015 (git pre-commit hook / repo
integrity); COE `2026-06-09-model-dependent-completion-gate.md` (and the three
prior handoff COEs). Implements the long-promised **repo handoff verifier**
(promoted P2 → P1 in `2026-06-09-concierge-handoff-regression.md`).

## Context

The completion gate — *commit and push every touched repo before the turn ends,
or name the blocker* (tenet 11.2, `AGENTS.md` Working model + Final response
gate) — lived only as **prose**. Prose is executed by the LLM's judgment, so its
adherence is **model-dependent**. Switching to GPT-5.5 (reasoning = high) produced
a session that ended with work uncommitted/unpushed, the fourth human-caught
instance of this class. Cursor's own team confirms git-rule adherence is a known,
model-dependent weakness, not a config error
([forum](https://forum.cursor.com/t/cannot-instruct-agent-to-auto-commit/155811)).

The systemic root cause (COE 5-whys) is a **wrong-layer** problem. Ranking the
candidate mechanisms by *who executes them*:

| Mechanism | Executed by | Deterministic? | Can it *trigger* a commit/push? |
|---|---|---|---|
| Rules / `AGENTS.md` / Skills / slash-workflows | the LLM | No — model-dependent | only if the model chooses to |
| Git hooks (`pre-commit`, `pre-push`) | git | Yes, but only *during* a commit/push | No — they **validate**, they don't initiate |
| **Cursor `stop` hook** | **the harness (Cursor)** | **Yes — fires on every turn-end, any model** | **Yes** |

A git hook cannot fix "the agent never ran git" because it only runs once a commit
is already in flight. Only a harness lifecycle hook runs independently of the
model. This matches the convergent industry pattern (tenet 8, web-verified):
GitButler uses Cursor's `stop` hook as its commit signal and states that *hooks
are deterministic while rules/MCP are non-deterministic because the LLM runs them*
([GitButler](https://blog.gitbutler.com/cursor-hooks-deep-dive)); Claude Code's
canonical auto-commit is a `Stop` hook
([BleepingSwift](https://bleepingswift.com/blog/claude-code-auto-commit)); and
`agent-better-checkpoint` ships the layered model — soft SKILL + `stop`-hook
safety net ([repo](https://github.com/alienzhou/agent-better-checkpoint)).

## Decision

Add a project-level Cursor **`stop` hook** that makes the completion gate
deterministic and model-independent:

- **`.cursor/hooks.json`** registers `python .cursor/hooks/completion_gate.py` on
  the `stop` event with `loop_limit: 4`.
- **`.cursor/hooks/completion_gate.py`** (Python, tenet 3 — cross-platform; no
  shell dialect split) reads the `stop` hook JSON (`status`, `loop_count`) and:
  1. Only acts on `status == "completed"` (no nagging on abort/error).
  2. Determines repos to guard = **union** of the `AI_MEMORY_REPOS` env var (the
     existing `install-hooks.ps1` convention) and discovered sibling git repos, so
     a touched-but-unlisted repo (e.g. `ai-memory-extension`) is still caught.
  3. For each repo, checks `git status --porcelain` (dirty) and `@{u}..HEAD`
     (unpushed / no-upstream).
  4. **Clean + pushed → `{}`** (allow the turn to stop).
  5. **Dirty/ahead → `{"followup_message": ...}`** that forces the agent to finish
     the Definition of Done itself (stage → Conventional-Commit → push each repo →
     update `STATUS.md`/logs). The script does **not** commit for the agent.
  6. **After `FAIL_LOUD_AT` (3) loops still dirty → a fail-loud `followup_message`**
     telling the agent to stop auto-retrying and surface a plain operator-facing
     blocker report (no false resume prompt). `loop_limit: 4` caps total
     follow-ups so the agent can never deadlock.

### Why enforce-the-DoD, not blind auto-commit (Design B over A)

A blind `stop`-hook `git add -A && commit && push` (the simplest Claude Code
recipe) was **rejected**: our "Done" is more than a commit — it requires
`STATUS.md` refreshed, `BUILD-LOG`/`BUILD-JOURNEY` appended, an ADR for major
choices, and no drift (DoD trigger table). A dumb script cannot satisfy that, and
it would push half-finished mid-turn work to a *public* portfolio repo. So the
deterministic layer **forces the agent to complete the DoD** (keeping good commit
messages, staging judgment, and docs) while making only the *trigger* mechanical.
This is precisely the existing prose — *"the safeguard against agent error is the
Definition-of-Done verification gate"* — finally turned into a mechanism
(tenet 14: fix the control plane).

## Consequences (reversible — tenet 17)

- **Model-independent guarantee.** Any model (GPT-5.5-high included) is now forced
  back to finish commit/push; the prose gate becomes the happy path, not the
  guarantee.
- **Versioned, unlike git hooks.** `.cursor/hooks.json` + the script live in the
  repo (tenet 1), so — unlike `.git/hooks` (ADR 015, re-installed per clone) — the
  completion gate survives a re-clone with no install step.
- **Hard layer named.** Tenet 11 + `AGENTS.md` now name the `stop` hook as the
  *hard* completion-gate layer (the git pre-commit hook remains the *validation*
  layer: repo-integrity + gitleaks).
- **Reversible.** Deleting `.cursor/hooks.json` (or the `stop` entry) removes the
  gate; no destructive effect. Two-way door.

### Limitations / operating notes

- **Cursor-only.** Fires inside Cursor, not VS Code/Claude Code (tenet 2). Those
  surfaces still rely on the prose gate + the git validation hook; revisit if they
  become primary. The git pre-commit hook (ADR 015) remains the editor-agnostic
  validation backstop.
- **Requires `python` on PATH** (present on this Windows box; Mac may expose
  `python3` — adjust the command if the surface changes).
- **Fires per turn, not per task.** Scoped to only act when work is actually dirty/
  unpushed, so routine read-only turns are not nagged; with short single-task
  sessions (tenet 16) turn-end ≈ task-end.
- Cursor reloads `hooks.json` on save (restart if it doesn't load); verify in the
  **Hooks** settings tab / output channel.

## Alternatives considered

- **Reword the prose rule / add a skill (status quo+).** Same non-deterministic
  layer that already failed four times across models. Rejected as the *guarantee*;
  kept as the soft happy-path layer.
- **Git `pre-commit`/`pre-push` hook only.** Validates content but cannot trigger a
  commit/push the agent never starts. Already in place for integrity + secrets
  (ADR 015); complementary, not a substitute.
- **Blind auto-commit `stop` hook (Design A).** Maximally deterministic but cannot
  satisfy the DoD (STATUS/docs/no-drift) and would push unfinished public work.
  Rejected; see above.
- **Hybrid (enforce, then blind auto-commit after the cap).** Considered; rejected
  in favor of fail-loud-to-operator, because an unresolved gate usually means a
  real blocker (pre-commit/gitleaks rejection, push auth, conflict) that a blind
  commit would paper over.
