"""Alert rule evaluation for production metrics (Phase 8)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Alert:
    name: str
    severity: str
    message: str


DEFAULT_RULES = {
    "retrieval_p95_ms": 500.0,
    "extraction_quality_min": 0.85,
    "disk_usage_percent_max": 80.0,
    "write_errors_per_hour_max": 5.0,
}


def evaluate_alerts(metrics: dict[str, Any], rules: dict[str, float] | None = None) -> list[Alert]:
    """Evaluate metric snapshot against static alert thresholds."""
    limits = rules or DEFAULT_RULES
    alerts: list[Alert] = []

    retrieval_p95 = float(metrics.get("retrieval_p95_ms", 0.0))
    if retrieval_p95 > limits["retrieval_p95_ms"]:
        alerts.append(
            Alert(
                "retrieval_latency",
                "warning",
                f"retrieval p95 {retrieval_p95:.0f}ms exceeds {limits['retrieval_p95_ms']:.0f}ms",
            )
        )

    extraction_quality = float(metrics.get("extraction_quality", 1.0))
    if extraction_quality < limits["extraction_quality_min"]:
        alerts.append(
            Alert(
                "extraction_quality",
                "critical",
                f"extraction quality {extraction_quality:.2f} below "
                f"{limits['extraction_quality_min']:.2f}",
            )
        )

    disk_usage = float(metrics.get("disk_usage_percent", 0.0))
    if disk_usage > limits["disk_usage_percent_max"]:
        alerts.append(
            Alert(
                "disk_usage",
                "warning",
                f"disk usage {disk_usage:.0f}% exceeds {limits['disk_usage_percent_max']:.0f}%",
            )
        )

    write_errors = float(metrics.get("write_errors_per_hour", 0.0))
    if write_errors > limits["write_errors_per_hour_max"]:
        alerts.append(
            Alert(
                "write_errors",
                "critical",
                f"write errors {write_errors:.0f}/hr exceeds "
                f"{limits['write_errors_per_hour_max']:.0f}/hr",
            )
        )

    return alerts
