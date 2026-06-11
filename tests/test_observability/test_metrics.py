"""Unit tests for Prometheus metrics helpers."""

from __future__ import annotations

from prometheus_client import REGISTRY

from observability.metrics import (
    observe_extraction_latency,
    observe_retrieval_latency,
    record_search,
    record_write,
    set_memory_counts,
)


def test_record_write_and_search_increment() -> None:
    before_writes = REGISTRY.get_sample_value("memory_writes_total", {"status": "success"})
    record_write(status="success")
    after_writes = REGISTRY.get_sample_value("memory_writes_total", {"status": "success"})
    assert after_writes == (before_writes or 0) + 1

    before_search = REGISTRY.get_sample_value("memory_searches_total", {"status": "success"})
    record_search(status="success")
    after_search = REGISTRY.get_sample_value("memory_searches_total", {"status": "success"})
    assert after_search == (before_search or 0) + 1


def test_observe_latencies_and_gauges() -> None:
    observe_retrieval_latency(0.12)
    observe_extraction_latency(0.45)
    set_memory_counts(total=10, by_venture={"career": 3, "personal": 7})
    assert REGISTRY.get_sample_value("total_memories") == 10.0
    assert REGISTRY.get_sample_value("memories_by_venture", {"venture": "career"}) == 3.0
