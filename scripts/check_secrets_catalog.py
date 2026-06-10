#!/usr/bin/env python3
"""Deterministic secrets-catalog coverage gate (DoD dod-10, promoted from prose).

WHY THIS EXISTS
---------------
The credential-custody DoD row says a new/rotated secret is *not done* until
(1) the value is in Bitwarden and (2) an index row exists in the private
``docs/security/secrets-catalog.md``. Until 2026-06-10 that rule was prose —
executed by LLM diligence, so a future session could mint a secret and forget
the catalog row with nothing blocking it (the same failure class as the STATUS
snapshot drift; see ``check_status_snapshot.py``).

This gate makes half of the rule mechanical: every secret *placeholder* the
public repo declares must have a matching row in the private catalog —
otherwise the commit introducing it is blocked. Sources of required keys
(mirrors the catalog's own "How to audit" section):

1. ``infra/.env.example`` — any ``KEY=`` line whose value contains REPLACE_ME
   (commented swap examples count: they document a provisionable secret).
2. ``infra/terraform/terraform.tfvars.example`` — any ``key = "...REPLACE_ME..."``.
3. ``.github/workflows/*.yml`` — every ``${{ secrets.X }}`` except the
   built-in ``GITHUB_TOKEN``.

The check is a substring match for the key name in the catalog text — it
verifies an *index row exists*, not its quality. The Bitwarden half cannot be
machine-checked (the vault is external) and stays operator-verified prose.

The catalog lives in the PRIVATE sibling repo. On this workspace (and any
correctly bootstrapped clone) it is present and the gate enforces. On public
CI runners the private clone is absent → the gate SKIPs with a notice (pass
``--require-catalog`` to fail instead). Pre-commit is the enforcement point.

CROSS-PLATFORM (tenet 3): pure Python stdlib.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ENV_KEY_RE = re.compile(r"^\s*#?\s*([A-Z][A-Z0-9_]*)=(.*)$")
TFVARS_KEY_RE = re.compile(r"^\s*([a-z][a-z0-9_]*)\s*=\s*\"[^\"]*REPLACE_ME[^\"]*\"")
WORKFLOW_SECRET_RE = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}")
PLACEHOLDER = "REPLACE_ME"
BUILTIN_SECRETS = {"GITHUB_TOKEN"}


def keys_from_env_example(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        match = ENV_KEY_RE.match(line)
        if match and PLACEHOLDER in match.group(2):
            keys.add(match.group(1))
    return keys


def keys_from_tfvars(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        match = TFVARS_KEY_RE.match(line)
        if match:
            keys.add(match.group(1))
    return keys


def keys_from_workflows(texts: list[str]) -> set[str]:
    keys: set[str] = set()
    for text in texts:
        keys.update(WORKFLOW_SECRET_RE.findall(text))
    return keys - BUILTIN_SECRETS


def missing_keys(catalog_text: str, required: set[str]) -> list[str]:
    return sorted(key for key in required if key not in catalog_text)


def collect_required_keys(repo: Path) -> set[str]:
    required: set[str] = set()

    env_example = repo / "infra" / ".env.example"
    if env_example.is_file():
        required |= keys_from_env_example(env_example.read_text(encoding="utf-8"))

    tfvars_example = repo / "infra" / "terraform" / "terraform.tfvars.example"
    if tfvars_example.is_file():
        required |= keys_from_tfvars(tfvars_example.read_text(encoding="utf-8"))

    workflows_dir = repo / ".github" / "workflows"
    if workflows_dir.is_dir():
        texts = [
            p.read_text(encoding="utf-8") for p in sorted(workflows_dir.glob("*.yml"))
        ]
        required |= keys_from_workflows(texts)

    return required


def _default_repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_catalog(repo: Path) -> Path:
    return (
        repo.parent / "ai-memory-infra-private" / "docs" / "security" / "secrets-catalog.md"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=None, help="public repo root")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="path to the private secrets-catalog.md (default: sibling private clone)",
    )
    parser.add_argument(
        "--require-catalog",
        action="store_true",
        help="fail (instead of skip) when the private catalog is absent",
    )
    args = parser.parse_args(argv)

    repo = (args.repo or _default_repo()).resolve()
    catalog_path = args.catalog or _default_catalog(repo)

    required = collect_required_keys(repo)

    if not catalog_path.is_file():
        if args.require_catalog:
            print(f"SECRETS CATALOG GATE: FAIL — catalog not found at {catalog_path}.")
            return 1
        print(
            "SECRETS CATALOG GATE: SKIP — private catalog not present "
            f"({catalog_path}); enforced where the private clone exists (pre-commit)."
        )
        return 0

    missing = missing_keys(catalog_path.read_text(encoding="utf-8"), required)
    if missing:
        print(f"SECRETS CATALOG GATE: FAIL — {len(missing)} secret(s) have no catalog row:")
        for key in missing:
            print(f"  - {key}")
        print(
            "\nFix: add a row (purpose · lives where · rotation · blast radius — NO value) "
            f"to {catalog_path} and store the value in Bitwarden (ADR 017; DoD dod-10)."
        )
        return 1

    print(
        f"SECRETS CATALOG GATE: OK — all {len(required)} declared secrets have catalog rows."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
