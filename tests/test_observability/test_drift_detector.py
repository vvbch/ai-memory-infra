"""Unit tests for drift detection."""

from __future__ import annotations

from observability.drift_detector import aggregate_score, detect_drift, sample_recent_scores


def test_detect_drift_when_below_threshold() -> None:
    result = detect_drift(0.7, baseline_score=0.9, threshold=0.85)
    assert result.drift_detected is True
    assert "below threshold" in result.message


def test_no_drift_when_healthy() -> None:
    result = detect_drift(0.92, baseline_score=0.9, threshold=0.85)
    assert result.drift_detected is False


def test_sample_recent_scores() -> None:
    sampled = sample_recent_scores(list(range(100)), sample_rate=0.1)
    assert len(sampled) >= 1
    assert aggregate_score([0.8, 1.0]) == 0.9
