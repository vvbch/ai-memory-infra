"""Prometheus metrics for memory operations (Phase 8)."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

MEMORY_WRITES = Counter(
    "memory_writes_total",
    "Total memory write attempts",
    ["status"],
)
MEMORY_SEARCHES = Counter(
    "memory_searches_total",
    "Total memory search requests",
    ["status"],
)
RETRIEVAL_LATENCY = Histogram(
    "retrieval_latency_seconds",
    "Memory retrieval latency in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
EXTRACTION_LATENCY = Histogram(
    "extraction_latency_seconds",
    "Fact extraction latency in seconds",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)
TOTAL_MEMORIES = Gauge("total_memories", "Current memory count in the bank")
MEMORIES_BY_VENTURE = Gauge(
    "memories_by_venture",
    "Memories tagged with a venture label",
    ["venture"],
)


def record_write(*, status: str = "success") -> None:
    MEMORY_WRITES.labels(status=status).inc()


def record_search(*, status: str = "success") -> None:
    MEMORY_SEARCHES.labels(status=status).inc()


def observe_retrieval_latency(seconds: float) -> None:
    RETRIEVAL_LATENCY.observe(seconds)


def observe_extraction_latency(seconds: float) -> None:
    EXTRACTION_LATENCY.observe(seconds)


def set_memory_counts(*, total: int, by_venture: dict[str, int] | None = None) -> None:
    TOTAL_MEMORIES.set(total)
    for venture, count in (by_venture or {}).items():
        MEMORIES_BY_VENTURE.labels(venture=venture).set(count)
