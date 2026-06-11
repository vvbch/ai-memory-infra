"""Eval report rendering (Phase 7)."""

from __future__ import annotations

import json
from typing import Any


def render_markdown_report(results: dict[str, Any]) -> str:
    """Human-readable Markdown summary for PRs and CI."""
    lines = ["# Eval report", ""]
    for suite, payload in results.items():
        if not isinstance(payload, dict):
            continue
        lines.append(f"## {suite}")
        metrics = payload.get("metrics") or {}
        if metrics:
            for key, value in sorted(metrics.items()):
                if isinstance(value, float):
                    lines.append(f"- **{key}**: {value:.3f}")
                else:
                    lines.append(f"- **{key}**: {value}")
        lines.append(f"- cases: {payload.get('cases', 0)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json_report(results: dict[str, Any]) -> str:
    """Machine-readable JSON for CI artifacts."""
    return json.dumps(results, indent=2, sort_keys=True) + "\n"
