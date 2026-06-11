#!/usr/bin/env python3
"""Memory write-contract conformance check (ADR 028 + ADR 031 detect control).

WHY THIS EXISTS
---------------
ADR 028 settled the memory write contract: one ``user_id="primary-user"`` for the
person, and ``source`` is a mandatory discriminator carried in **metadata**
(so it reaches both pgvector and the Neo4j graph). That decision was committed
in the control plane but was silently *false* in the Chrome extension and the
MCP proxy for a day — see COE ``2026-06-09-extension-memory-identity-drift.md``.
Our other gates police a repo's git *hygiene* (completion gate, gitleaks,
repo-health); none policed cross-repo *conformance* to a shared contract.

ADR 031 makes a cross-cutting decision a contract that must hold in every
consumer repo, enforced mechanically. This script is that mechanism: it fails
when a consumer repo violates the contract, so drift is caught by a check, not
by a human noticing months later.

WHAT IT CHECKS (invariants, not payload-grepping)
-------------------------------------------------
Rather than try to parse every write payload, it enforces the *structural*
invariants that make the contract impossible to violate at runtime:

  Extension (``ai-memory-extension``)
    1. The canonical constants are declared once: ``DEFAULT_USER_ID='primary-user'``
       and ``SOURCE='extension'`` in ``src/types/api.ts``.
    2. There is a single normalizing write path: ``normalizeMemoryWriteBody`` is
       the body of ``postMemory`` (``src/utils/api.ts``) and the background relay
       (``src/background.ts``) applies it to every ``POST /memories``.
    3. No write BYPASSES that path: a direct ``fetch(apiUrl('/memories')`` may
       appear ONLY inside ``postMemory``. Any other occurrence is a bypass that
       would skip identity/source healing -> FAIL. (Legacy ``chrome-extension-
       user`` / ``OPENMEMORY_CHROME_EXTENSION`` literals in content scripts are
       fine precisely because they are healed at this chokepoint.)

  MCP proxy (``ai-memory-infra/src/mcp_proxy/``)
    4. ``client.py``: ``DEFAULT_USER_ID = "primary-user"`` and no legacy
       ``"chrome-extension-user"`` default.
    5. ``server.py``: ``add_memory`` tags every write ``metadata.source = "mcp"``
       before delegating to the client (the tool surface is the single write path).

Exit 0 = contract holds in every consumer repo present; exit 1 = a violation
(printed). Missing a consumer repo is reported, not failed (it may not be
checked out), unless --strict is passed.

CROSS-PLATFORM (tenet 3): pure Python; no shell-isms.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CANONICAL_USER_ID = "primary-user"
LEGACY_USER_ID = "chrome-extension-user"


def _workspace_root() -> Path:
    # <workspace>/ai-memory-infra/scripts/check_memory_contract.py
    return Path(__file__).resolve().parents[2]


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _is_code_line(line: str) -> bool:
    """True if the line is live code (not a // or * comment)."""
    s = line.strip()
    return bool(s) and not s.startswith("//") and not s.startswith("*")


def check_extension(repo: Path) -> tuple[list[str], list[str]]:
    """Return (violations, notes) for the extension repo."""
    violations: list[str] = []
    notes: list[str] = []
    src = repo / "src"
    if not src.is_dir():
        notes.append(f"{repo.name}: src/ not found — repo not checked out, skipped")
        return violations, notes

    # 1. canonical constants declared once
    api_ts = _read(src / "types" / "api.ts") or ""
    if not re.search(r"DEFAULT_USER_ID\s*=\s*['\"]primary-user['\"]", api_ts):
        violations.append(
            "ai-memory-extension/src/types/api.ts: "
            "missing canonical DEFAULT_USER_ID = 'primary-user' (ADR 028)"
        )
    if not re.search(r"\bSOURCE\s*=\s*['\"]extension['\"]", api_ts):
        violations.append(
            "ai-memory-extension/src/types/api.ts: "
            "missing canonical SOURCE = 'extension' (ADR 028)"
        )

    # 2. single normalizing write path exists
    utils_api = _read(src / "utils" / "api.ts") or ""
    if "normalizeMemoryWriteBody" not in utils_api or "function postMemory" not in utils_api:
        violations.append(
            "ai-memory-extension/src/utils/api.ts: "
            "expected normalizeMemoryWriteBody + postMemory single write path (ADR 028/031)"
        )
    background = _read(src / "background.ts") or ""
    if "normalizeMemoryWriteBody" not in background:
        violations.append(
            "ai-memory-extension/src/background.ts: "
            "background relay must apply normalizeMemoryWriteBody to every POST /memories (ADR 028)"
        )

    # 3. no write bypasses the chokepoint
    bypass_re = re.compile(r"fetch\(\s*apiUrl\(\s*['\"]/memories")
    for ts_file in sorted(src.rglob("*.ts")):
        text = _read(ts_file)
        if text is None:
            continue
        rel = ts_file.relative_to(repo).as_posix()
        for n, line in enumerate(text.splitlines(), start=1):
            if not _is_code_line(line):
                continue
            if bypass_re.search(line) and rel != "src/utils/api.ts":
                violations.append(
                    f"{rel}:{n}: direct fetch to /memories bypasses postMemory "
                    "(ADR 031 single write path) — route this write through postMemory"
                )

    return violations, notes


def check_mcp_proxy_client(repo: Path) -> tuple[list[str], list[str]]:
    violations: list[str] = []
    notes: list[str] = []
    client = repo / "src" / "mcp_proxy" / "client.py"
    text = _read(client)
    if text is None:
        notes.append(f"{repo.name}: src/mcp_proxy/client.py not found — skipped")
        return violations, notes

    if re.search(rf'DEFAULT_USER_ID\s*=\s*["\']{re.escape(LEGACY_USER_ID)}["\']', text):
        violations.append(
            "ai-memory-infra/src/mcp_proxy/client.py: "
            f"DEFAULT_USER_ID still set to legacy '{LEGACY_USER_ID}' (ADR 028)"
        )
    if not re.search(rf'DEFAULT_USER_ID\s*=\s*["\']{CANONICAL_USER_ID}["\']', text):
        violations.append(
            "ai-memory-infra/src/mcp_proxy/client.py: "
            f"missing canonical DEFAULT_USER_ID = '{CANONICAL_USER_ID}' (ADR 028)"
        )
    return violations, notes


def check_mcp_proxy_server(repo: Path) -> tuple[list[str], list[str]]:
    """ADR 028: the MCP tool surface must tag every add with metadata.source=mcp."""
    violations: list[str] = []
    notes: list[str] = []
    server = repo / "src" / "mcp_proxy" / "server.py"
    text = _read(server)
    if text is None:
        notes.append(f"{repo.name}: src/mcp_proxy/server.py not found — skipped")
        return violations, notes

    if "def add_memory" not in text:
        violations.append(
            "ai-memory-infra/src/mcp_proxy/server.py: "
            "missing add_memory tool (ADR 028 write path)"
        )
        return violations, notes

    tags_mcp = re.search(r'["\']source["\']\s*:\s*["\']mcp["\']', text) or re.search(
        r'get\("source"\)\s+or\s+["\']mcp["\']', text
    )
    if not tags_mcp:
        violations.append(
            "ai-memory-infra/src/mcp_proxy/server.py: "
            'add_memory must default metadata.source to "mcp" (ADR 028)'
        )
    if "metadata=metadata" not in text and "metadata={" not in text:
        violations.append(
            "ai-memory-infra/src/mcp_proxy/server.py: "
            "add_memory must pass metadata into client.add_memory (ADR 028)"
        )
    return violations, notes


def check_memory_helper(repo: Path) -> tuple[list[str], list[str]]:
    """ADR 037: memory.py must expose contract metadata on capture_fact."""
    violations: list[str] = []
    notes: list[str] = []
    helper = repo / "scripts" / "memory.py"
    text = _read(helper)
    if text is None:
        notes.append(f"{repo.name}: scripts/memory.py not found — skipped")
        return violations, notes

    required_params = (
        "event_date",
        "source_doc_id",
        "namespace",
        "external_id",
    )
    for param in required_params:
        if param not in text:
            violations.append(
                f"ai-memory-infra/scripts/memory.py: "
                f"capture_fact must accept {param} (ADR 037 metadata contract)"
            )

    if "from memory.contract import" not in text:
        violations.append(
            "ai-memory-infra/scripts/memory.py: "
            "must import shared memory.contract helpers (ADR 037)"
        )
    return violations, notes


def check_mcp_proxy(repo: Path) -> tuple[list[str], list[str]]:
    client_v, client_n = check_mcp_proxy_client(repo)
    server_v, server_n = check_mcp_proxy_server(repo)
    helper_v, helper_n = check_memory_helper(repo)
    return client_v + server_v + helper_v, client_n + server_n + helper_n


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat a missing consumer repo as a failure (default: report and skip)",
    )
    args = parser.parse_args(argv[1:])

    root = _workspace_root()
    all_violations: list[str] = []
    all_notes: list[str] = []

    ext_v, ext_n = check_extension(root / "ai-memory-extension")
    proxy_v, proxy_n = check_mcp_proxy(root / "ai-memory-infra")
    all_violations += ext_v + proxy_v
    all_notes += ext_n + proxy_n

    for note in all_notes:
        print(f"note: {note}")
        if args.strict:
            all_violations.append(note)

    if all_violations:
        print("\nMEMORY CONTRACT CONFORMANCE: FAIL (ADR 028/031)\n")
        for v in all_violations:
            print(f"  - {v}")
        print(
            "\nFix: route every write through the single normalizing path and keep "
            "the canonical constants. See ADR 028, ADR 031."
        )
        return 1

    print(
        "MEMORY CONTRACT CONFORMANCE: OK — every checked consumer upholds "
        "the contract (ADR 028/031)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
