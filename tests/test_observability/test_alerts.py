"""Unit tests for alert rule evaluation."""

from __future__ import annotations

from observability.alerts import evaluate_alerts


def test_no_alerts_when_metrics_healthy() -> None:
    assert evaluate_alerts(
        {
            "retrieval_p95_ms": 120,
            "extraction_quality": 0.92,
            "disk_usage_percent": 40,
            "write_errors_per_hour": 0,
        }
    ) == []


def test_fires_latency_and_disk_alerts() -> None:
    alerts = evaluate_alerts(
        {
            "retrieval_p95_ms": 900,
            "extraction_quality": 0.9,
            "disk_usage_percent": 90,
            "write_errors_per_hour": 0,
        }
    )
    names = {alert.name for alert in alerts}
    assert "retrieval_latency" in names
    assert "disk_usage" in names
