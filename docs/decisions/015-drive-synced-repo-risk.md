# ADR 015: Repos live under Google Drive — accept the risk, instrument the integrity

**Status:** Accepted (ratifies Tenet 11)
**Date:** 2026-06-06
**Deciders:** Chandra

### Context

Both repos — `ai-memory-infra` (public) and `ai-memory-infra-private` — live,
**including their `.git` directories**, inside a Google Drive "Mirror" folder on
the operator's Windows machine:

```
…/My Drive (…)/workplace/ai-memory/
  ├─ ai-memory-infra/          (public, Apache-2.0)
  ├─ ai-memory-infra-private/  (private companion)
  └─ _inbox/                   (landing zone, outside both repos)
```

This was a deliberate operator choice, not an accident. It buys:

- a **second, always-on, off-machine copy** of all work (Drive), independent of
  GitHub;
- one place for **large gitignored firm artifacts** (interview material, firm
  IP) to be backed up alongside the code without ever entering git history;
- zero extra tooling — the backup is the filesystem the operator already uses.

It also carries a **known, non-trivial risk**.

### The risk

Google Drive Mirror syncs files as they change on disk, with no understanding of
git's internal consistency. `git` mutates many small files under `.git/`
(objects, packs, refs, `index`, `HEAD`, lock files) as a set that must stay
mutually consistent. A sync pass that races a `git` write, or that resolves a
two-machine edit, can leave the local repo in a corrupt state:

- **conflicted-copy files inside `.git/`** — e.g.
  `HEAD (1).lock`, `index (vvbch's conflicted copy 2026-06-06).` — which confuse
  or break git;
- **half-synced pack/ref files** — `git fsck` reports missing/!corrupt objects;
- **a stale `index.lock`** left behind, blocking all writes until removed.

There is **no reliable way to exclude `.git/` from a Mirror-mode sync** (Mirror
mirrors the whole folder; selective exclusion is a Streaming/Backup-and-Sync
feature, not Mirror). So the risk cannot be *engineered away* at the Drive layer
— it must be *managed*.

### Decision

**Keep the repos under Drive, and manage the risk with a four-part contract**
(this is Tenet 11; this ADR is its rationale + the mitigation it ratifies):

1. **GitHub is the source of truth.** The Drive copy is convenience + backup, not
   the canonical record. Anything not on GitHub does not "really" exist (Tenet 1).
2. **Commit and push every session — never batch.** This keeps the window of
   un-pushed, local-only work small, so a local `.git` corruption can cost at
   most one session's worth of un-pushed changes.
3. **Instrument integrity (don't assume it).** `scripts/check-repo-health.*`
   (BUILD task) runs, per repo: `git fsck --full`, a scan for Drive
   conflicted-copy files inside `.git/`, a stale-`index.lock` check, and an
   ahead/behind-vs-remote check. It exits non-zero and writes a log on failure.
   It fires in three layers:
   - **soft:** AGENTS.md tells the agent to run it at session start + before commit;
   - **fast/pre-commit:** the conflict-copy + `index.lock` subset is wired as a
     git `pre-commit` hook (via `make install-hooks`, so it survives a re-clone);
   - **scheduled:** Windows Task Scheduler runs the full check daily, unattended,
     writing failures to a log the operator/agent will see.
4. **On any red check, re-clone — do not hand-repair.** Clone fresh from GitHub
   into a clean path and re-apply uncommitted work. In-place repair of a
   Drive-corrupted `.git` has no guaranteed-clean end state and is a time sink.

Supporting rules: **never commit large firm artifacts into git history** (a
one-way door — history rewrites break every clone; large files stay gitignored +
Drive-backed, outside git), and **quit Drive while actively working in the repo**
when practical so a sync pass can't race a `git` write.

### Alternatives considered

- **Move repos out of Drive (e.g. plain `C:\src\`).** Removes the risk entirely
  but loses the always-on off-machine backup and the co-located firm-artifact
  backup, and adds a separate backup chore. Rejected: the operator wants the
  Drive backup; the risk is acceptable once instrumented.
- **Streaming/selective-sync to exclude `.git/`.** Not available on Mirror; would
  also defeat the "whole working tree is backed up" benefit and is fragile across
  machines. Rejected.
- **A bare mirror remote on Drive instead of the live working copy.** More
  correct in theory, but adds a manual push-to-Drive step and operator overhead
  for little gain over "GitHub is truth + integrity checks." Rejected for Tenet 7
  (fewer moving parts); GitHub already is the durable remote.

### Consequences

- **Positive:** keep the Drive backup; corruption is *detected early* (three
  firing layers) and *recovered cleanly* (re-clone), so it degrades to "lose at
  most one un-pushed session," which (2) already bounds. Portfolio-wise this is a
  concrete risk-management story (named risk → mitigation contract → automated
  enforcement).
- **Negative:** an integrity script + a hook + a scheduled task to build and
  maintain (BUILD task); the operator must actually act on a red check rather
  than ignore it; "commit+push every session" is a discipline, not a guarantee.
- **Cross-refs:** Tenet 11 (`docs/tenets.md`), AGENTS.md (tenet summary +
  working-model repo-health line), `docs/runbook.md` ("Drive-sync integrity"),
  BUILD task (`scripts/check-repo-health.*`, `make install-hooks`, Task Scheduler
  register script).

---
