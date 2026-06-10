"""Tests for the secrets-catalog coverage gate (DoD dod-10 promotion to enforced)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_secrets_catalog as gate  # noqa: E402

ENV_EXAMPLE = """\
DOMAIN=example.com
JWT_SECRET=REPLACE_ME                    # openssl rand -base64 48
OPENAI_API_KEY=sk-REPLACE_ME             # OpenAI key
#   DEEPSEEK_API_KEY=sk-REPLACE_ME
MEM0_TELEMETRY=false
#HEALTHCHECK_URL=https://hc-ping.com/your-uuid-here
"""

TFVARS_EXAMPLE = """\
do_token         = "REPLACE_ME"
domain_name      = "example.com"
ssh_public_key   = "ssh-ed25519 AAAA... you@host"
spaces_secret_key = "REPLACE_ME"
"""

WORKFLOW = """\
jobs:
  scan:
    steps:
      - run: echo scan
        env:
          CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.PRIVATE_REPO_PAT }}
"""


def test_env_example_keys_are_replace_me_only() -> None:
    keys = gate.keys_from_env_example(ENV_EXAMPLE)
    assert keys == {"JWT_SECRET", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"}


def test_tfvars_keys_are_replace_me_only() -> None:
    keys = gate.keys_from_tfvars(TFVARS_EXAMPLE)
    assert keys == {"do_token", "spaces_secret_key"}


def test_workflow_keys_exclude_builtin_github_token() -> None:
    keys = gate.keys_from_workflows([WORKFLOW])
    assert keys == {"CURSOR_API_KEY", "PRIVATE_REPO_PAT"}


def test_missing_key_is_reported() -> None:
    catalog = "| `JWT_SECRET` | ... |\n| `do_token` | ... |"
    missing = gate.missing_keys(catalog, {"JWT_SECRET", "do_token", "NEW_TOKEN"})
    assert missing == ["NEW_TOKEN"]


def test_all_keys_present_passes() -> None:
    catalog = "`JWT_SECRET` row\n`OPENAI_API_KEY` row\n`do_token` row"
    assert gate.missing_keys(catalog, {"JWT_SECRET", "OPENAI_API_KEY", "do_token"}) == []


def test_main_fails_when_catalog_misses_a_key(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    catalog = tmp_path / "catalog.md"
    catalog.write_text("only `JWT_SECRET` is here", encoding="utf-8")

    rc = gate.main(["--repo", str(repo), "--catalog", str(catalog)])
    assert rc == 1


def test_main_passes_when_catalog_covers_everything(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    catalog = tmp_path / "catalog.md"
    catalog.write_text(
        "`JWT_SECRET` `OPENAI_API_KEY` `DEEPSEEK_API_KEY` `do_token` "
        "`spaces_secret_key` `CURSOR_API_KEY` `PRIVATE_REPO_PAT`",
        encoding="utf-8",
    )

    rc = gate.main(["--repo", str(repo), "--catalog", str(catalog)])
    assert rc == 0


def test_main_skips_when_private_clone_absent(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    rc = gate.main(["--repo", str(repo), "--catalog", str(tmp_path / "nope.md")])
    assert rc == 0


def test_main_require_catalog_fails_when_absent(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    rc = gate.main(
        ["--repo", str(repo), "--catalog", str(tmp_path / "nope.md"), "--require-catalog"]
    )
    assert rc == 1


def _fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "infra" / "terraform").mkdir(parents=True)
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / "infra" / ".env.example").write_text(ENV_EXAMPLE, encoding="utf-8")
    (repo / "infra" / "terraform" / "terraform.tfvars.example").write_text(
        TFVARS_EXAMPLE, encoding="utf-8"
    )
    (repo / ".github" / "workflows" / "scan.yml").write_text(WORKFLOW, encoding="utf-8")
    return repo


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
