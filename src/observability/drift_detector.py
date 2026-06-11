"""Weekly extraction quality drift detection (Phase 8)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DriftResult:
    current_score: float
    baseline_score: float
    threshold: float
    drift_detected: bool
    message: str


def detect_drift(
    current_score: float,
    baseline_score: float,
    *,
    threshold: float = 0.85,
) -> DriftResult:
    """Alert when current extraction quality falls below threshold or baseline."""
    drift = current_score < threshold or current_score < baseline_score
    if drift:
        message = (
            f"extraction quality {current_score:.3f} below threshold {threshold:.3f} "
            f"or baseline {baseline_score:.3f}"
        )
    else:
        message = "no drift detected"
    return DriftResult(
        current_score=current_score,
        baseline_score=baseline_score,
        threshold=threshold,
        drift_detected=drift,
        message=message,
    )


def sample_recent_scores(
    scores: list[float],
    *,
    sample_rate: float = 0.05,
    min_samples: int = 1,
) -> list[float]:
    """Return a deterministic subset for weekly drift sampling."""
    if not scores:
        return []
    step = max(1, int(1 / sample_rate)) if sample_rate > 0 else len(scores)
    sampled = scores[::step]
    return sampled[: max(min_samples, len(sampled))]


def aggregate_score(samples: list[float]) -> float:
    """Mean score for sampled extractions."""
    if not samples:
        return 0.0
    return sum(samples) / len(samples)
