# Operational Runbook

> Operational procedures for running and recovering the system. Sections are
> added as each phase lands. See `docs/setup.md` for first-time deploy.

## Drive-sync integrity (Tenet 11 / ADR 015)

**Why this exists.** Both repos (including `.git/`) live inside a Google Drive
"Mirror" folder. Drive can corrupt a `.git/` it syncs mid-write — conflicted-copy
files inside `.git/`, half-synced packs/refs, or a stale `index.lock`. We can't
exclude `.git/` from Mirror, so we **detect and recover** instead. Full rationale:
**Tenet 11** (`docs/tenets.md`) and **ADR 015** (`docs/decisions/015-...`).

### The integrity check

`scripts/check-repo-health.ps1` (configurable repo list via env var — **not**
hardcoded machine paths) runs, per repo:

- `git fsck --full` — object/pack/ref corruption;
- a scan for Drive **conflicted-copy** files inside `.git/`
  (e.g. `* (… conflicted copy …) *`, `* (1).lock`);
- a **stale `index.lock`** check (lock present with no live git process);
- **ahead/behind vs remote** — surfaces un-pushed local-only work.

It **exits non-zero and writes a log file** on any failure. A **fast subset**
(conflict-copy + `index.lock` only, no `fsck`) is used on the pre-commit path so
commits stay quick.

### When it fires (three layers)

1. **Soft (human/agent):** run it **at session start and before every commit**
   (   AGENTS.md working-model line). Manual command (Windows PowerShell 5.1 — no
   `pwsh` 7 on this box, so invoke via `powershell` with a bypassed policy):
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\check-repo-health.ps1
   ```
2. **Fast (pre-commit hook):** `make install-hooks` installs the fast subset as
   `.git/hooks/pre-commit`. Re-run after any re-clone (hooks live in `.git/`,
   which isn't versioned).
3. **Scheduled (daily, unattended):** a register-task script wires the **full**
   check into Windows Task Scheduler; failures land in a log the operator/agent
   reviews.

### On a RED check — re-clone, do NOT hand-repair

In-place repair of a Drive-corrupted `.git/` has no guaranteed-clean end state.
Instead:

1. **Stash/copy uncommitted work** out of the repo (to `_inbox/` or a temp path)
   — diff first so you know exactly what's un-pushed.
2. **Re-clone fresh from GitHub** into a clean path:
   ```powershell
   git clone git@github.com:<you>/ai-memory-infra.git ai-memory-infra-fresh
   ```
3. **Re-apply** the uncommitted work into the fresh clone, run the integrity
   check to confirm green, then commit + push.
4. **Replace** the corrupt working copy with the fresh clone (and re-run
   `make install-hooks`).

### Standing habits (bound the blast radius)

- **Commit + push every session — never batch.** Un-pushed work is the only
  thing a local corruption can lose; keep that window tiny.
- **Quit Drive while actively working in the repo** when practical, so a sync
  pass can't race a `git` write.
- **Never commit large firm artifacts into git history** — one-way door; they
  stay gitignored and Drive-backed, outside git.

---

> _Remaining runbook sections (deploy recovery, backup/restore, model swap,
> rollback) land with Phases 2+._
