# COE: Completed session work was not atomically committed and pushed

- **Date:** 2026-06-08
- **Author(s):** Chandra (detected), agent (analysis + fix)
- **Severity:** medium *(no production/customer/data impact; high governance and handoff risk because the next stateless session would resume from stale remote state)*
- **Status:** actions-in-progress
- **Related:** tenets 1, 11, 14, 16, 17 · `AGENTS.md` Working model + Completion gate · `docs/planning/STATUS.md`

## Summary

After Phase 3 Chrome extension work, the agent verified the ChatGPT sidebar and updated
control-plane docs, but ended the session with completed reversible work still local.
The first correction committed/pushed only the control-plane repos and still missed the
actual package repo (`ai-memory-extension`), which was `ahead 3` and had uncommitted
background-relay source changes. This violated the atomic session handoff model: GitHub
is the handoff boundary, not the local working tree.

## Impact

- The next stateless session would have read `STATUS.md` and seen a green sidebar proof,
  while the extension code needed to reproduce that state was not fully on remote.
- `ai-memory-extension` was left `ahead 3` with additional uncommitted source changes,
  creating a split-brain between control-plane truth and package-repo truth.
- No production/customer/data impact. The installed local Chrome extension worked, but
  the remote source of truth was stale, undermining tenet 1 and tenet 11.

## Timeline

- 2026-06-08 23:20–23:28 IST — Agent ran repo-health, reloaded OpenMemory in Chrome,
  verified ChatGPT sidebar Recent Memories loaded, and updated `STATUS.md`,
  `BUILD-JOURNEY.md`, and private `BUILD-LOG.md`.
- 2026-06-08 23:29 IST — Operator caught that the agent had not committed/pushed the
  completed work.
- 2026-06-08 23:31 IST — Agent sharpened `AGENTS.md`, committed/pushed
  `ai-memory-infra` and `ai-memory-infra-private`, but failed to check/push the
  extension package repo.
- 2026-06-08 23:32 IST — Operator caught the second miss: `ai-memory-extension` was
  still not pushed and no COE existed.
- 2026-06-08 — Agent verified the extension repo state, committed/pushed the package
  (`97530f8`), and created this COE plus control-plane updates.

## Detection

**A human caught both misses.** The first miss was noticed because the final answer said
"I did not commit." The second miss was caught by the operator asking whether the
extension package had also been pushed. There was no mandatory final all-repo status
gate checking every touched repo for clean `main...origin/main`, so the agent could
declare handoff complete with a stale package remote.

## Root cause — 5 Whys

1. **Why was completed session work not committed and pushed?** The agent followed the
   generic "do not commit unless explicitly asked" tool policy and ignored the repo's
   stronger standing completion gate.
2. **Why did the first correction still miss the extension repo?** The agent treated
   `ai-memory-infra` as "the repo" because it is the control plane, and did not enumerate
   every touched workspace repo before handoff.
3. **Why was a package repo easy to miss?** The workspace discipline said package repos
   are targeted data-plane workspaces, but the completion gate did not explicitly say
   package repos are first-class touched repos that must be committed/pushed too.
4. **Why did documentation and package truth diverge?** The handoff check was narrative:
   update `STATUS.md` and final-answer summary. It did not require a mechanical
   cross-repo clean/ahead-behind check after all commits and pushes.
5. **Why was there no mechanical check?** **Root cause (systemic):** the stateless-session
   model externalized state to the repo, but its Definition of Done depended on agent
   memory/judgment to identify all touched repos. There was no explicit touched-repo
   inventory and no final "all touched repos are clean and aligned with remote" gate.

## Corrective actions

| Action | Type | Owner | Due | Status |
|---|---|---|---|---|
| Push the missed extension package work (`ai-memory-extension`) including the background-relay fix | Mitigate | agent | 2026-06-08 | ✅ done (`97530f8`) |
| Sharpen `AGENTS.md`: package repos are first-class touched repos; completion gate covers every touched repo, not just control-plane docs | Prevent | agent | 2026-06-08 | ✅ done |
| Update `STATUS.md` next-action reminder: next session must verify all touched repos clean/aligned after commit+push | Prevent | agent | 2026-06-08 | ✅ done |
| Record this COE and index it | Prevent | agent | 2026-06-08 | ✅ done |
| Add a final handoff checklist or script that enumerates touched repos and fails if any are dirty/ahead/behind before final response | Detect | Chandra+agent | P2 governance hardening | ⏳ backlog |
| Until automated, final response must name every touched repo and latest pushed commit | Detect/Mitigate | agent | every session | ⏳ in effect |

## Lessons learned

**A stateless handoff is only real when every touched repo is on remote.** Control-plane
docs can describe the work, but they do not carry the package implementation. The
handoff unit is the whole workspace change set: package code, public docs, private logs,
and control-plane status. The minimum reliable closeout is mechanical, not narrative:
list touched repos, verify each is clean and aligned with `origin/main`, and report the
latest pushed commit for each.
