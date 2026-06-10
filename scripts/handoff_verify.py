#!/usr/bin/env python3
"""Final all-repo handoff verifier (BACKLOG P1 [governance]; ADR 033 backlog #1).

WHY THIS EXISTS
---------------
Repeat handoff COEs (2026-06-08-atomic-handoff-failure,
2026-06-09-session-handoff-omission, 2026-06-09-concierge-handoff-regression)
share one root cause: the final response claimed a clean handoff that git could
have disproven. The turn-end ``completion_gate.py`` already refuses to end a
turn with dirty/unpushed repos; this script is the richer, *agent-run* check for
the AGENTS.md **Final response gate** — run it before the final answer (and
before emitting any Resume prompt) and report what it says.

WHAT IT CHECKS (per repo)
-------------------------
- working tree clean (no uncommitted changes)
- an upstream exists, and the branch is neither ahead (unpushed) nor behind
  (stale clone — Drive-synced repos, tenet 11) after an optional ``git fetch``
- the latest **pushed** commit (sha + subject) — printed so the final response
  can cite real push evidence instead of asserting it
- ``docs/planning/STATUS.md`` (where present) is the checkpoint of record: no
  commit newer than the last commit touching STATUS — i.e. work was not
  committed *after* the last checkpoint (tenet 16 / DoD "every logical step").

EXIT: 0 = handoff-ready; 1 = at least one repo fails (report says why).
CROSS-PLATFORM (tenet 3): pure Python + git.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

STATUS_REL = Path("docs") / "planning" / "STATUS.md"


def _run_git(repo: Path, *args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return proc.returncode, proc.stdout.strip()
    except Exception:
        return 1, ""


def discover_repos() -> list[Path]:
    """AI_MEMORY_REPOS entries plus sibling git repos of the workspace root."""
    repos: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        try:
            rp = p.resolve()
        except OSError:
            return
        key = str(rp).lower()
        if key not in seen and (rp / ".git").exists():
            seen.add(key)
            repos.append(rp)

    for chunk in os.environ.get("AI_MEMORY_REPOS", "").split(";"):
        if chunk.strip():
            add(Path(chunk.strip()))

    here = Path(__file__).resolve()
    try:
        workspace = here.parents[2]
        for child in sorted(workspace.iterdir()):
            if child.is_dir():
                add(child)
    except (IndexError, OSError):
        pass
    return repos


def status_is_checkpoint(repo: Path) -> bool:
    """True if STATUS.md is the checkpoint of record (or repo has none).

    Rule: the newest commit in the repo must be no newer than the newest commit
    that touched STATUS.md — work committed *after* the last STATUS update means
    the checkpoint is stale (DoD "every logical step"; tenet 16).
    """
    if not (repo / STATUS_REL).exists():
        return True
    rc_s, status_ts = _run_git(repo, "log", "-1", "--format=%ct", "--", str(STATUS_REL))
    rc_h, head_ts = _run_git(repo, "log", "-1", "--format=%ct")
    if rc_s != 0 or rc_h != 0 or not status_ts.isdigit() or not head_ts.isdigit():
        return False  # STATUS exists but was never committed, or git failed
    return int(head_ts) <= int(status_ts)


def verify_repo(repo: Path, *, fetch: bool = True) -> dict[str, object]:
    """Full handoff state for one repo; ``ok`` means handoff-ready."""
    if fetch:
        _run_git(repo, "fetch", "--quiet")

    _, porcelain = _run_git(repo, "status", "--porcelain")
    dirty = bool(porcelain.strip())

    rc_up, upstream = _run_git(
        repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"
    )
    no_upstream = rc_up != 0
    ahead = behind = 0
    pushed_commit = ""
    if not no_upstream:
        rc_c, counts = _run_git(repo, "rev-list", "--left-right", "--count", "@{u}...HEAD")
        if rc_c == 0 and counts:
            parts = counts.split()
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                behind, ahead = int(parts[0]), int(parts[1])
        _, pushed_commit = _run_git(repo, "log", "-1", "--format=%h %s", upstream)

    status_ok = status_is_checkpoint(repo)
    ok = not dirty and not no_upstream and ahead == 0 and behind == 0 and status_ok
    return {
        "name": repo.name,
        "path": str(repo),
        "ok": ok,
        "dirty": dirty,
        "no_upstream": no_upstream,
        "ahead": ahead,
        "behind": behind,
        "pushed_commit": pushed_commit,
        "status_checkpointed": status_ok,
    }


def _describe(s: dict[str, object]) -> str:
    if s["ok"]:
        return f"OK    {s['name']}: clean + pushed (origin tip: {s['pushed_commit']})"
    problems = []
    if s["dirty"]:
        problems.append("uncommitted changes")
    if s["no_upstream"]:
        problems.append("no upstream / never pushed")
    if s["ahead"]:
        problems.append(f"{s['ahead']} unpushed commit(s)")
    if s["behind"]:
        problems.append(f"{s['behind']} commit(s) behind origin (stale clone — tenet 11)")
    if not s["status_checkpointed"]:
        problems.append("STATUS.md is stale (work committed after the last checkpoint)")
    return f"FAIL  {s['name']}: {', '.join(problems)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="handoff_verify",
        description="Final all-repo handoff verifier (AGENTS.md Final response gate).",
    )
    parser.add_argument("--no-fetch", action="store_true", help="skip git fetch (offline)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    states = [verify_repo(r, fetch=not args.no_fetch) for r in discover_repos()]
    ready = all(s["ok"] for s in states)

    if args.json:
        print(json.dumps({"handoff_ready": ready, "repos": states}, indent=2))
    else:
        for s in states:
            print(_describe(s))
        print("")
        if ready:
            print("HANDOFF READY — every repo clean, pushed, in sync; STATUS checkpointed.")
        else:
            print(
                "HANDOFF NOT READY — fix the FAIL lines above (commit/push/pull or "
                "checkpoint STATUS.md) before the final response. Do NOT emit a "
                "Resume prompt in this state."
            )
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
