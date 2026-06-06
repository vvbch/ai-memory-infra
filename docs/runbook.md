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

- `git fsck --full --strict` — object/pack/ref corruption (HARD fail);
- a scan for Drive **conflicted-copy** files inside `.git/` (name contains
  `conflicted copy`) — the signature of a bad sync (HARD fail);
- a **stale `index.lock`** check (present and older than `-StaleLockMinutes`,
  default 5) (HARD fail);
- **ahead/behind vs the upstream** — surfaces un-pushed local-only work (INFO).

Repo list comes from the **`AI_MEMORY_REPOS`** env var or a `-RepoList` arg —
**never** hardcoded paths. It **exits non-zero and writes a timestamped log** on
any HARD problem. A **fast subset** (`-Fast`: conflicted-copy + `index.lock`
only) runs on the pre-commit path so commits stay quick.

**One-time setup — point it at your repos** (a User env var; survives reboots):
```powershell
setx AI_MEMORY_REPOS "C:\path\to\ai-memory-infra;C:\path\to\ai-memory-infra-private"
```
Open a new shell after `setx` (or pass `-RepoList "<path>","<path>"` each call).

### When it fires (three layers)

1. **Soft (human/agent):** run it **at session start and before every commit**
   (AGENTS.md working-model line). Windows PowerShell 5.1 (no `pwsh` 7 here):
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\check-repo-health.ps1
   ```
2. **Fast (pre-commit hook):** installs the fast subset as `.git/hooks/pre-commit`
   (a **copy**, not a symlink — tenet 3). Re-run after any re-clone (hooks live in
   `.git/`, which isn't versioned). Bypass a known-safe block with
   `git commit --no-verify`:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\install-hooks.ps1
   ```
3. **Scheduled (daily, unattended):** registers the **full** check in Windows
   Task Scheduler (per-user, S4U — runs even when locked); failures go to a log
   under `%LOCALAPPDATA%\ai-memory-repo-health\logs` plus a non-zero
   Last-Run-Result:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\register-repo-health-task.ps1
   ```
   On Unix/WSL the three are `make repo-health` / `make install-hooks` /
   `make register-health-task`.

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
