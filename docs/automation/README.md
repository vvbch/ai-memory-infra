# Scheduled & reactive automation (agents in CI)

> Design stance (tenet 2): **orchestration is plain GitHub Actions, prompts are
> versioned markdown in this folder, and the agent CLI is a swappable detail.**
> Nothing here depends on any IDE. To change agent vendor, edit only the two
> "Install agent CLI" / "run agent" lines in each workflow; schedules, prompts,
> and guardrails survive unchanged.

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | every push/PR | ruff + mypy + pytest + memory-contract gate + STATUS snapshot gate |
| `ci-autofix.yml` | CI fails on main | agent reproduces, root-causes, and fixes (two-way doors only) → PR |
| `weekly-scan.yml` (scan) | Sat 09:00 IST | redundancy/inconsistency pass, tests, architecture benchmark vs industry standards → report in `docs/reports/weekly-scan/` + two-way-door fixes as a PR |
| `weekly-scan.yml` (interview) | Sat 09:00 IST | regenerates the five per-track interview packets in the private repo from current repo state → PR there |

## Guardrails (all agent jobs)

- **Two-way doors only** (tenet 17): everything an automated job changes must be
  fully undone by `git revert`. One-way doors (data, spend, retention, deletion,
  lock-in) are *reported with a recommendation*, never applied.
- **No live-system access:** the runners have no droplet SSH key, no
  `AI_MEMORY_API_KEY`, no Terraform credentials. The blast radius is a PR.
- **Everything lands as a PR**, never a push to main.

## One-time setup (operator)

1. **`CURSOR_API_KEY`** repo secret on `vvbch/ai-memory-infra` — from
   cursor.com → Dashboard → API keys.
2. **`PRIVATE_REPO_PAT`** repo secret on `vvbch/ai-memory-infra` — GitHub
   fine-grained PAT (named "ai-memory-interview-refresh" on GitHub) scoped to
   `vvbch/ai-memory-infra-private` with **Contents: Read and write** AND
   **Pull requests: Read and write** (checkout + push the branch needs
   Contents; opening the PR needs Pull requests). Used only by the interview
   job. Bitwarden: `ai-memory-infra` folder →
   "PRIVATE_REPO_PAT / ai-memory-interview-refresh".

## Known caveat

PRs opened with the default `GITHUB_TOKEN` (scan + autofix jobs) do not
themselves trigger CI — re-run checks from the PR page or push an empty commit
if you want a green tick before merging.
