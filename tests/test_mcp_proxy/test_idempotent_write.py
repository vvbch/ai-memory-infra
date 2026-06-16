"""Unit tests for idempotent write cache helpers."""

from __future__ import annotations

from typing import Any

from mcp_proxy.idempotent_write import (
    append_cache_record,
    cache_record_from_write,
    find_by_external_id,
    update_cache_after_write,
)


def test_cache_record_from_write_builds_list_shape() -> None:
    record = cache_record_from_write(
        "hello",
        external_id="seed:a",
        metadata={"source": "test", "event_date": "2026-06-01"},
        add_result={"results": [{"event": "ADD", "id": "m-1"}]},
    )
    assert record == {
        "id": "m-1",
        "memory": "hello",
        "metadata": {
            "source": "test",
            "event_date": "2026-06-01",
            "external_id": "seed:a",
        },
    }


def test_append_cache_record_dedupes_external_id() -> None:
    cache = [{"id": "m1", "metadata": {"external_id": "seed:a"}}]
    append_cache_record(
        cache,
        {"id": "m2", "metadata": {"external_id": "seed:a"}},
    )
    assert len(cache) == 1


class _SearchOnlyClient:
    def search_memories(
        self,
        query: str,
        *,
        user_id: str | None = None,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "results": [
                {
                    "id": "found",
                    "memory": query,
                    "metadata": {"external_id": filters.get("external_id")},
                }
            ]
        }


def test_update_cache_after_write_uses_search_fallback() -> None:
    cache: list[dict[str, Any]] = []
    update_cache_after_write(
        _SearchOnlyClient(),
        cache,
        external_id="seed:b",
        user_id=None,
        text="payload",
        metadata={"source": "test", "event_date": "2026-06-01"},
        add_result={"results": [{"event": "ADD"}]},
    )
    assert len(cache) == 1
    assert cache[0]["id"] == "found"


def test_find_by_external_id_uses_cache_before_search() -> None:
    cache = [{"id": "m1", "metadata": {"external_id": "seed:c"}}]

    class _NoSearchClient:
        def list_memories(self, **_: Any) -> list[dict[str, Any]]:
            raise AssertionError("list_memories should not run when cache is provided")

        def search_memories(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise AssertionError("search_memories should not run on cache hit")

    found = find_by_external_id(_NoSearchClient(), "seed:c", cache=cache)
    assert found is not None
    assert found["id"] == "m1"
