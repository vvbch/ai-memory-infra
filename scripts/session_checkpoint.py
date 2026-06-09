#!/usr/bin/env python3
"""Build Agent session-checkpoint skill — canonical, editor-agnostic (ADR 027/030 family).

WHY THIS EXISTS
---------------
Closing a logical step is a Definition-of-Done event (AGENTS.md / tenet 16): the
agent must capture the *current work item, how it was verified, which repos it
touched (and the exact pushed commits), and the single next action* into the
durable repo docs — STATUS.md (snapshot), the private BUILD-LOG.md (history), and
the public BUILD-JOURNEY.md (curated) — WITHOUT dumping a long chat transcript.

That capture has two parts:
  * judgment (what the step was, how it was verified, what's next) — the agent's;
  * mechanism (which repos changed, are they clean/pushed, what are the commit
    ids, are all required fields present) — deterministic, and the job of THIS
    script. A prose-only checkpoint lets the agent hand-wave "pushed" or forget a
    touched repo; those are exactly the recurring handoff misses behind the COEs
    (atomic-handoff-failure, session-handoff-omission). The script reads git
    truth and validates the handoff contract so the checkpoint can't lie.

This is the soft, *capture* layer. The hard, *trigger* layer is
``scripts/completion_gate.py`` (the turn-end gate that refuses to let a dirty/
unpushed turn end). They are complementary: this one formats a correct, no-drift
checkpoint from real repo facts; the gate stops a missed one.

SKILL CONTRACT (docs/agent-personas.md)
---------------------------------------
* Owner persona  : Build Agent.
* Pain removed   : drifting / incomplete handoffs; "pushed" claims with no commit
                   id; touched repos forgotten; STATUS vs BUILD-LOG drift.
* May store/write : STATUS-ready snippet, a BUILD-LOG entry (private), repo git
                   facts (branch, clean/pushed, short commit id + subject).
* Must never write: secrets, raw vault values, or long chat transcripts. The
                   script only ever reads git metadata + the fields you pass it.
* Success cond.  : ``--check`` passes (every touched repo clean & pushed, all
                   required fields present) and the rendered entry names each
                   repo's latest pushed commit.
* Canonical truth: the repo files. If a memory disagrees with git/STATUS, the
                   files win (Memory Steward rule).

PORTABILITY (tenet 2) / CROSS-PLATFORM (tenet 3)
------------------------------------------------
Pure Python stdlib + ``git``; no shell-isms; UTF-8 forced so Windows consoles
never crash on em dashes / check marks. No editor coupling — any harness or a
human can run it.

USAGE
-----
  # Validate the handoff contract before a final response (exit 1 if not met):
  python scripts/session_checkpoint.py --check

  # Render a checkpoint (repo facts + STATUS snippet + BUILD-LOG entry):
  python scripts/session_checkpoint.py \
      --work "Built the session-checkpoint skill" \
      --verify "ran --check green; rendered entry; repo-health green" \
      --next "Build the Operator Assistant concierge action formatter" \
      --phase "Phase 4 — agent-owned skills"

  # Also append the BUILD-LOG entry to the private log (auto-located):
  python scripts/session_checkpoint.py --work ... --verify ... --next ... --write-log

  # Machine-readable:
  python scripts/session_checkpoint.py --json
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path

# <workspace>/ai-memory-infra/scripts/session_checkpoint.py
_HERE = Path(__file__).resolve()
INFRA_ROOT = _HERE.parents[1]
WORKSPACE_ROOT = _HERE.parents[2]


# --------------------------------------------------------------------------- #
# Git truth gathering (shared shape with completion_gate.py).
# --------------------------------------------------------------------------- #
def _run_git(repo: Path, *args: str) -> tuple[int, str]:
    """Run a git command in ``repo``; return (returncode, stdout-stripped)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode, proc.stdout.strip()
    except Exception:
        return 1, ""


def candidate_repos() -> list[Path]:
    """Union of AI_MEMORY_REPOS and discovered sibling repos (most-protective).

    A repo the agent touched but that isn't in the env var (e.g.
    ai-memory-extension) is still surfaced, so a checkpoint can't quietly omit it.
    """
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
        chunk = chunk.strip()
        if chunk:
            add(Path(chunk))

    with contextlib.suppress(IndexError, OSError):
        for child in WORKSPACE_ROOT.iterdir():
            if child.is_dir():
                add(child)

    return repos


def repo_state(repo: Path) -> dict | None:
    """Return the checkpoint-relevant git state for ``repo`` (None if not a repo)."""
    rc, _ = _run_git(repo, "rev-parse", "--is-inside-work-tree")
    if rc != 0:
        return None

    _, branch = _run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _, porcelain = _run_git(repo, "status", "--porcelain")
    dirty = bool(porcelain.strip())
    _, head = _run_git(repo, "log", "-1", "--format=%h %s")

    rc_up, _ = _run_git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if rc_up != 0:
        no_upstream = True
        ahead = behind = 0
    else:
        no_upstream = False
        rc_a, a = _run_git(repo, "rev-list", "--count", "@{u}..HEAD")
        rc_b, b = _run_git(repo, "rev-list", "--count", "HEAD..@{u}")
        ahead = int(a) if (rc_a == 0 and a.isdigit()) else 0
        behind = int(b) if (rc_b == 0 and b.isdigit()) else 0

    clean_pushed = (not dirty) and ahead == 0 and not no_upstream and behind == 0
    return {
        "name": repo.name,
        "path": str(repo),
        "branch": branch,
        "dirty": dirty,
        "ahead": ahead,
        "behind": behind,
        "no_upstream": no_upstream,
        "head": head,
        "clean_pushed": clean_pushed,
    }


def gather_states() -> list[dict]:
    return [s for repo in candidate_repos() if (s := repo_state(repo))]


# --------------------------------------------------------------------------- #
# Validation — the handoff contract.
# --------------------------------------------------------------------------- #
REQUIRED_FIELDS = ("work", "verify", "next")


def validate(states: list[dict], fields: dict, *, need_fields: bool) -> list[str]:
    """Return a list of contract violations (empty == checkpoint is sound)."""
    problems: list[str] = []

    if need_fields:
        for f in REQUIRED_FIELDS:
            if not (fields.get(f) or "").strip():
                problems.append(f"missing required field: --{f}")

    for s in states:
        if s["clean_pushed"]:
            continue
        bits = []
        if s["dirty"]:
            bits.append("uncommitted changes")
        if s["ahead"]:
            bits.append(f"{s['ahead']} unpushed commit(s)")
        if s["behind"]:
            bits.append(f"{s['behind']} commit(s) behind upstream")
        if s["no_upstream"]:
            bits.append("no upstream/never pushed")
        problems.append(f"{s['name']}: {', '.join(bits)}")

    return problems


# --------------------------------------------------------------------------- #
# Rendering.
# --------------------------------------------------------------------------- #
def _today() -> str:
    return _dt.date.today().isoformat()


def _repo_lines(states: list[dict]) -> list[str]:
    lines = []
    for s in states:
        mark = "OK" if s["clean_pushed"] else "NEEDS COMMIT/PUSH"
        lines.append(
            f"  - {s['name']} [{s['branch']}] @ {s['head']}  ({mark})"
        )
    return lines or ["  (no project repos found)"]


def render_human(states: list[dict], fields: dict) -> str:
    problems = validate(states, fields, need_fields=_has_any_field(fields))
    out = [
        f"SESSION CHECKPOINT — {_today()}",
        "",
        "Touched / project repos (git truth):",
        *_repo_lines(states),
        "",
        "Handoff contract: " + ("PASS ✅" if not problems else "OPEN ❌"),
    ]
    for p in problems:
        out.append(f"  - {p}")
    if _has_any_field(fields):
        out += ["", "--- STATUS-ready snippet ---", render_status(states, fields)]
        out += ["", "--- BUILD-LOG entry (private) ---", render_build_log(states, fields)]
    return "\n".join(out)


def render_status(states: list[dict], fields: dict) -> str:
    """A 'Done this session' + 'Next action' block ready to paste into STATUS.md."""
    repos = ", ".join(
        f"{s['name']} {s['head'].split(' ', 1)[0]}" for s in states if not s["dirty"]
    ) or "none"
    lines = [
        f"## Done this session ({_today()})",
        "",
        f"- {fields.get('work', '').strip()}",
    ]
    if fields.get("verify"):
        lines.append(f"  - Verified: {fields['verify'].strip()}")
    lines.append(f"  - Touched repos (latest pushed commit): {repos}")
    lines += ["", "## Next action", "", f"> {fields.get('next', '').strip()}"]
    return "\n".join(lines)


def render_build_log(states: list[dict], fields: dict) -> str:
    """A private BUILD-LOG.md entry matching the existing append-only format."""
    repo_facts = "\n".join(
        f"- `{s['name']}` [{s['branch']}] @ `{s['head']}`"
        + ("" if s["clean_pushed"] else "  **(NOT clean/pushed)**")
        for s in states
    )
    parts = [
        f"## {_today()} — Session: {fields.get('work', '').strip()}",
        "",
        f"**Phase:** {fields.get('phase', '').strip() or '(unspecified)'}",
        "",
        "### Steps executed",
        f"- {fields.get('work', '').strip()}",
        "",
        "### Verification",
        f"- {fields.get('verify', '').strip() or '(none recorded)'}",
        "",
        "### Touched repos (git truth at checkpoint)",
        repo_facts or "- (none)",
        "",
        "### Next action",
        f"- {fields.get('next', '').strip() or '(none recorded)'}",
    ]
    return "\n".join(parts)


def _has_any_field(fields: dict) -> bool:
    return any((fields.get(f) or "").strip() for f in REQUIRED_FIELDS) or bool(
        (fields.get("phase") or "").strip()
    )


# --------------------------------------------------------------------------- #
# Optional: append the BUILD-LOG entry to the private log.
# --------------------------------------------------------------------------- #
def _default_build_log() -> Path | None:
    """Locate the private BUILD-LOG.md (private repo first, then control plane)."""
    candidates = [
        WORKSPACE_ROOT / "ai-memory-infra-private" / "docs" / "planning" / "BUILD-LOG.md",
        INFRA_ROOT / "docs" / "planning" / "BUILD-LOG.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def append_build_log(entry: str, path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    path.write_text(text + sep + entry + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def _parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="session_checkpoint",
        description="Build Agent session-checkpoint skill (capture + validate a handoff).",
    )
    p.add_argument("--work", default="", help="what this logical step accomplished")
    p.add_argument("--verify", default="", help="how it was verified (commands + result)")
    p.add_argument("--next", dest="next", default="", help="the single next action")
    p.add_argument("--phase", default="", help="current phase (optional)")
    p.add_argument("--check", action="store_true",
                   help="only validate the handoff contract; exit 1 if not met")
    p.add_argument("--status", action="store_true", help="print only the STATUS-ready snippet")
    p.add_argument("--build-log", action="store_true",
                   help="print only the private BUILD-LOG entry")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--write-log", nargs="?", const="", default=None,
                   help="append the BUILD-LOG entry to the private log "
                        "(optionally pass an explicit path)")
    p.add_argument("--strict", action="store_true",
                   help="exit 1 when the handoff contract or required fields are unmet")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

    args = _parse(argv)
    fields = {"work": args.work, "verify": args.verify, "next": args.next, "phase": args.phase}
    states = gather_states()

    # --check is a pure gate: contract only, deterministic exit code.
    if args.check:
        problems = validate(states, fields, need_fields=_has_any_field(fields))
        if not problems:
            print("session-checkpoint: handoff contract PASS — all repos clean & pushed.")
            return 0
        print("session-checkpoint: handoff contract OPEN:")
        for p in problems:
            print(f"  - {p}")
        return 1

    if args.json:
        problems = validate(states, fields, need_fields=_has_any_field(fields))
        print(json.dumps({
            "date": _today(),
            "repos": states,
            "fields": fields,
            "contract_ok": not problems,
            "problems": problems,
        }, indent=2))
        return 0 if (problems == [] or not args.strict) else 1

    if args.status:
        print(render_status(states, fields))
    elif args.build_log:
        print(render_build_log(states, fields))
    else:
        print(render_human(states, fields))

    if args.write_log is not None:
        target = Path(args.write_log) if args.write_log else _default_build_log()
        if target is None:
            print("\n[write-log] could not locate BUILD-LOG.md — pass an explicit path.",
                  file=sys.stderr)
            return 1
        append_build_log(render_build_log(states, fields), target)
        print(f"\n[write-log] appended BUILD-LOG entry to {target}")

    if args.strict:
        problems = validate(states, fields, need_fields=_has_any_field(fields))
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
