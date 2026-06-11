#!/usr/bin/env python3
"""Offline near-duplicate memory clustering for human review (ADR 037).

Clusters memories by Mem0 search score (cosine-similarity proxy) above a
threshold. Default mode is **review-only** — it writes a JSON report and never
mutates the bank. Auto-merge is intentionally gated behind an explicit flag and
still requires human review on the first production pass (see COE
2026-06-10-mcp-timeout-semantic-duplicates).

Usage::

    python scripts/memory_compaction.py --report compaction-2026-06-10.json
    python scripts/memory_compaction.py --threshold 0.88 --user-id primary-user
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig  # noqa: E402


class CompactionError(RuntimeError):
    pass


def _client(user_id: str | None) -> MemoryApiClient:
    config = MemoryApiConfig.from_env()
    if user_id:
        config = MemoryApiConfig(
            base_url=config.base_url, api_key=config.api_key, user_id=user_id
        )
    return MemoryApiClient(config)


def _normalize_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        items = raw.get("results", raw.get("memories"))
        if isinstance(items, list):
            return [r for r in items if isinstance(r, dict)]
    return []


def list_all_memories(client: MemoryApiClient, *, user_id: str | None = None) -> list[dict[str, Any]]:
    raw = client.list_memories(user_id=user_id, limit=1000)
    return _normalize_list(raw)


def _record_id(rec: dict[str, Any]) -> str:
    return str(rec.get("id") or rec.get("memory_id") or "")


def _record_text(rec: dict[str, Any]) -> str:
    return str(rec.get("memory") or rec.get("text") or "").strip()


def _score(hit: dict[str, Any]) -> float:
    for key in ("score", "similarity", "distance"):
        val = hit.get(key)
        if isinstance(val, (int, float)):
            return float(val)
    return 0.0


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, node: str) -> None:
        self.parent.setdefault(node, node)

    def find(self, node: str) -> str:
        self.parent.setdefault(node, node)
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def clusters(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for node in self.parent:
            groups[self.find(node)].append(node)
        return dict(groups)


def find_near_duplicate_edges(
    client: MemoryApiClient,
    memories: list[dict[str, Any]],
    *,
    threshold: float,
    user_id: str | None,
    top_k: int,
) -> list[dict[str, Any]]:
    """Return undirected edges between memories with search score >= threshold."""
    by_id = {_record_id(m): m for m in memories if _record_id(m)}
    edges: list[dict[str, Any]] = []
    seen_pairs: set[frozenset[str]] = set()

    for mid, rec in by_id.items():
        text = _record_text(rec)
        if not text:
            continue
        hits = client.search_memories(text, user_id=user_id, top_k=top_k)
        for hit in _normalize_list(hits):
            other_id = _record_id(hit)
            if not other_id or other_id == mid:
                continue
            score = _score(hit)
            if score < threshold:
                continue
            pair = frozenset({mid, other_id})
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            edges.append(
                {
                    "a": mid,
                    "b": other_id,
                    "score": round(score, 4),
                    "a_text": _record_text(by_id[mid])[:160],
                    "b_text": _record_text(by_id.get(other_id, hit))[:160],
                }
            )
    return edges


def cluster_memories(
    client: MemoryApiClient,
    *,
    user_id: str | None = None,
    threshold: float = 0.85,
    top_k: int = 10,
) -> dict[str, Any]:
    memories = list_all_memories(client, user_id=user_id)
    uf = _UnionFind()
    for rec in memories:
        mid = _record_id(rec)
        if mid:
            uf.add(mid)

    edges = find_near_duplicate_edges(
        client, memories, threshold=threshold, user_id=user_id, top_k=top_k
    )
    for edge in edges:
        uf.union(edge["a"], edge["b"])

    by_id = {_record_id(m): m for m in memories if _record_id(m)}
    clusters: list[dict[str, Any]] = []
    for members in uf.clusters().values():
        if len(members) < 2:
            continue
        members_sorted = sorted(
            members,
            key=lambda mid: str(by_id.get(mid, {}).get("created_at", "")),
        )
        clusters.append(
            {
                "canonical_id": members_sorted[0],
                "member_ids": members_sorted,
                "texts": [
                    {"id": mid, "text": _record_text(by_id[mid])[:240]}
                    for mid in members_sorted
                    if mid in by_id
                ],
            }
        )

    clusters.sort(key=lambda c: (-len(c["member_ids"]), c["canonical_id"]))
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "user_id": user_id or MemoryApiConfig.from_env().user_id,
        "threshold": threshold,
        "memory_count": len(memories),
        "edge_count": len(edges),
        "cluster_count": len(clusters),
        "edges": edges,
        "clusters": clusters,
        "review_required": True,
        "auto_merge_allowed": False,
    }


def auto_merge_clusters(
    client: MemoryApiClient,
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Merge clusters — only call after explicit human review (ADR 037)."""
    outcomes: list[dict[str, Any]] = []
    for cluster in report.get("clusters", []):
        canonical = cluster["canonical_id"]
        dupes = [mid for mid in cluster["member_ids"] if mid != canonical]
        if not dupes:
            continue
        raw = client.get_memory(canonical)
        rec = _normalize_list(raw)[0] if _normalize_list(raw) else raw
        text = _record_text(rec)
        meta = dict(rec.get("metadata") or {})
        merged_from = list(meta.get("merged_from") or [])
        merged_from.extend(dupes)
        meta["merged_from"] = sorted(set(merged_from))
        client.update_memory(canonical, text or " ", metadata=meta)
        for mid in dupes:
            client.delete_memory(mid)
            outcomes.append({"deleted": mid, "merged_into": canonical})
    return outcomes


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Offline memory near-duplicate clustering (ADR 037).")
    p.add_argument("--user-id", default=None)
    p.add_argument("--threshold", type=float, default=0.85)
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--report", default=None, help="write JSON report to this path")
    p.add_argument(
        "--auto-merge",
        action="store_true",
        help="DANGER: merge clusters after review — refused without --i-reviewed-clusters",
    )
    p.add_argument(
        "--i-reviewed-clusters",
        action="store_true",
        help="confirm you reviewed cluster report and accept merge risk",
    )
    p.add_argument("--merge-from", default=None, help="apply auto-merge from a saved report JSON")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    client = _client(args.user_id)

    if args.merge_from:
        if not args.i_reviewed_clusters:
            raise CompactionError(
                "refusing auto-merge without --i-reviewed-clusters "
                "(first pass is review-only; see ADR 037 / COE 2026-06-10-mcp-timeout-semantic-duplicates)"
            )
        report = json.loads(open(args.merge_from, encoding="utf-8").read())
        outcomes = auto_merge_clusters(client, report)
        print(json.dumps({"merged": outcomes}, indent=2))
        return 0

    report = cluster_memories(
        client,
        user_id=args.user_id,
        threshold=args.threshold,
        top_k=args.top_k,
    )

    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"Wrote {report['cluster_count']} clusters ({report['edge_count']} edges) to {args.report}")
    else:
        print(json.dumps(report, indent=2))

    if args.auto_merge:
        raise CompactionError(
            "auto-merge from a fresh scan is disabled; generate a report, review clusters, "
            "then run with --merge-from <report> --i-reviewed-clusters"
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CompactionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
