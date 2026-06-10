#!/usr/bin/env python3
"""ADR 028 probe: verify ``metadata.source`` on pgvector writes and Neo4j reality.

WHY THIS EXISTS
---------------
ADR 028 requires ``source`` on every write. The pgvector path is live; Neo4j
graph propagation depends on whether Mem0 actually writes a graph (ADR 032: it
does not today — Neo4j is reserved for LifeGraph, Phase 6).

This script runs a repeatable live probe:
  1. Write (or re-check) a disposable fact with a known ``source`` tag.
  2. Confirm the tag round-trips via ``GET /memories/{id}``.
  3. Optionally SSH to the droplet and count Neo4j nodes (expect 0 — no Mem0 graph).

Exit 0 when pgvector propagation passes and Neo4j matches expectation (0 nodes
until LifeGraph lands). Exit 1 on failure or unexpected Neo4j writes.

USAGE
-----
  python scripts/verify_source_propagation.py
  python scripts/verify_source_propagation.py --memory-id <uuid> --source neo4j-probe
  python scripts/verify_source_propagation.py --no-ssh
  python scripts/verify_source_propagation.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig  # noqa: E402

DEFAULT_PROBE_SOURCE = "neo4j-probe"
DEFAULT_PROBE_TEXT = (
    "ADR-028 source propagation probe — disposable verification memory; safe to delete."
)
DEFAULT_SSH_HOST = "root@168.144.145.29"
DEFAULT_NEO4J_CONTAINER = "ai-memory-infra-neo4j-1"


@dataclass(frozen=True)
class ProbeResult:
    memory_id: str | None
    expected_source: str
    pgvector_source: str | None
    pgvector_ok: bool
    neo4j_node_count: int | None
    neo4j_ok: bool | None
    messages: list[str]


def _write_probe(
    client: MemoryApiClient,
    *,
    text: str,
    source: str,
) -> str:
    response = client.add_memory(
        text,
        metadata={"type": "fact", "source": source},
        infer=False,
    )
    results = response.get("results") if isinstance(response, dict) else None
    if not results or not isinstance(results, list):
        raise RuntimeError(f"unexpected add_memory response: {response!r}")
    first = results[0]
    if not isinstance(first, dict) or not first.get("id"):
        raise RuntimeError(f"add_memory returned no id: {response!r}")
    return str(first["id"])


def _read_source(client: MemoryApiClient, memory_id: str) -> str | None:
    record = client.get_memory(memory_id)
    metadata = record.get("metadata") if isinstance(record, dict) else None
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("source")
    return str(value) if value is not None else None


def _neo4j_node_count_ssh(
    ssh_host: str,
    container: str,
    *,
    timeout: int = 30,
) -> int:
    # Feed a tiny bash script on stdin — PowerShell cannot safely quote MATCH (n).
    # Password stays on the droplet — expand NEO4J_AUTH inside the container shell.
    remote_script = (
        f"docker exec {container} sh -c "
        f"'PASS=\"${{NEO4J_AUTH#neo4j/}}\"; "
        f"cypher-shell -u neo4j -p \"$PASS\" --format plain "
        f"\"MATCH (n) RETURN count(n) AS c\"'\n"
    )
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", ssh_host, "bash", "-s"],
        input=remote_script.replace("\r", ""),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"neo4j cypher-shell failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            return int(stripped)
    raise RuntimeError(f"could not parse neo4j count from stdout: {proc.stdout!r}")


def run_probe(
    *,
    client: MemoryApiClient,
    source: str = DEFAULT_PROBE_SOURCE,
    probe_text: str = DEFAULT_PROBE_TEXT,
    memory_id: str | None = None,
    ssh_host: str | None = DEFAULT_SSH_HOST,
    neo4j_container: str = DEFAULT_NEO4J_CONTAINER,
    expected_neo4j_nodes: int = 0,
) -> ProbeResult:
    messages: list[str] = []
    mid = memory_id
    if mid is None:
        mid = _write_probe(client, text=probe_text, source=source)
        messages.append(f"wrote probe memory id={mid}")

    pg_source = _read_source(client, mid)
    pg_ok = pg_source == source
    if pg_ok:
        messages.append(f"pgvector metadata.source={pg_source!r} OK")
    else:
        messages.append(
            f"pgvector metadata.source mismatch: expected {source!r}, got {pg_source!r}"
        )

    neo_count: int | None = None
    neo_ok: bool | None = None
    if ssh_host:
        try:
            neo_count = _neo4j_node_count_ssh(ssh_host, neo4j_container)
            neo_ok = neo_count == expected_neo4j_nodes
            if neo_ok:
                messages.append(
                    f"neo4j node_count={neo_count} (expected {expected_neo4j_nodes}; "
                    "Mem0 does not write graph — ADR 032)"
                )
            else:
                messages.append(
                    f"neo4j node_count={neo_count} UNEXPECTED "
                    f"(expected {expected_neo4j_nodes})"
                )
        except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
            messages.append(f"neo4j ssh probe failed: {exc}")
            neo_ok = False
    else:
        messages.append("neo4j ssh probe skipped (--no-ssh)")

    overall_neo_ok = neo_ok if ssh_host else None
    return ProbeResult(
        memory_id=mid,
        expected_source=source,
        pgvector_source=pg_source,
        pgvector_ok=pg_ok,
        neo4j_node_count=neo_count,
        neo4j_ok=overall_neo_ok,
        messages=messages,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="machine-readable report")
    p.add_argument("--source", default=DEFAULT_PROBE_SOURCE)
    p.add_argument("--memory-id", help="re-check an existing memory instead of writing")
    p.add_argument("--no-ssh", action="store_true", help="skip droplet Neo4j count")
    p.add_argument("--ssh-host", default=DEFAULT_SSH_HOST)
    p.add_argument("--neo4j-container", default=DEFAULT_NEO4J_CONTAINER)
    p.add_argument(
        "--expected-neo4j-nodes",
        type=int,
        default=0,
        help="expected Neo4j node count (0 until LifeGraph/Mem0 graph)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    client = MemoryApiClient(MemoryApiConfig.from_env())
    result = run_probe(
        client=client,
        source=args.source,
        memory_id=args.memory_id,
        ssh_host=None if args.no_ssh else args.ssh_host,
        neo4j_container=args.neo4j_container,
        expected_neo4j_nodes=args.expected_neo4j_nodes,
    )

    ok = result.pgvector_ok and (result.neo4j_ok is not False)
    payload: dict[str, Any] = {**asdict(result), "ok": ok}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for line in result.messages:
            print(line)
        print("RESULT:", "PASS" if ok else "FAIL")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
