from __future__ import annotations

import json

import httpx
import pytest

from mcp_proxy.client import MemoryApiClient, MemoryApiConfig, MemoryApiConfigError


def test_config_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_MEMORY_API_KEY", raising=False)

    with pytest.raises(MemoryApiConfigError):
        MemoryApiConfig.from_env()


def test_config_reads_env_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_MEMORY_API_KEY", "test-key")
    monkeypatch.delenv("AI_MEMORY_BASE_URL", raising=False)
    monkeypatch.delenv("AI_MEMORY_USER_ID", raising=False)

    config = MemoryApiConfig.from_env()

    assert config == MemoryApiConfig(
        base_url="https://memory.chandrav.dev",
        api_key="test-key",
        user_id="chandrav",
    )


def test_search_memories_posts_to_live_search_shape() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["api_key"] = request.headers["X-API-Key"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"results": [{"memory": "hello"}]})

    client = MemoryApiClient(
        MemoryApiConfig(
            base_url="https://memory.example.test",
            api_key="test-key",
            user_id="default-user",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.search_memories("hello?", top_k=3)

    assert result == {"results": [{"memory": "hello"}]}
    assert captured == {
        "url": "https://memory.example.test/search",
        "api_key": "test-key",
        "body": {"query": "hello?", "user_id": "default-user", "top_k": 3},
    }


def test_array_post_responses_are_wrapped_as_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"memory": "hello"}])

    client = MemoryApiClient(
        MemoryApiConfig(
            base_url="https://memory.example.test",
            api_key="test-key",
            user_id="default-user",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.search_memories("hello?") == {"results": [{"memory": "hello"}]}


def test_add_memory_posts_message_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"message": "ok"})

    client = MemoryApiClient(
        MemoryApiConfig(
            base_url="https://memory.example.test",
            api_key="test-key",
            user_id="default-user",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.add_memory(
        "remember this",
        user_id="override-user",
        metadata={"source": "test"},
    )

    assert result == {"message": "ok"}
    assert captured == {
        "url": "https://memory.example.test/memories",
        "body": {
            "messages": [{"role": "user", "content": "remember this"}],
            "user_id": "override-user",
            "metadata": {"source": "test"},
            "infer": True,
        },
    }


def _client_with(handler: object) -> MemoryApiClient:
    return MemoryApiClient(
        MemoryApiConfig(
            base_url="https://memory.example.test",
            api_key="test-key",
            user_id="default-user",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),  # type: ignore[arg-type]
    )


def test_search_with_filters_sends_filters_only_when_present() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"results": []})

    client = _client_with(handler)

    client.search_memories("todos", filters={"type": "open_item"})

    assert captured["body"] == {
        "query": "todos",
        "user_id": "default-user",
        "top_k": 5,
        "filters": {"type": "open_item"},
    }


def test_add_memory_supports_infer_false_for_verbatim_writes() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"results": [{"event": "ADD"}]})

    client = _client_with(handler)

    client.add_memory(
        "Follow up with recruiter Acme Corp",
        metadata={"type": "open_item", "source": "cursor"},
        infer=False,
    )

    assert captured["body"] == {
        "messages": [{"role": "user", "content": "Follow up with recruiter Acme Corp"}],
        "user_id": "default-user",
        "metadata": {"type": "open_item", "source": "cursor"},
        "infer": False,
    }


def test_get_memory_fetches_by_id() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        return httpx.Response(200, json={"id": "m1", "memory": "hello"})

    client = _client_with(handler)

    result = client.get_memory("m1")

    assert result == {"id": "m1", "memory": "hello"}
    assert captured == {
        "url": "https://memory.example.test/memories/m1",
        "method": "GET",
    }


def test_update_memory_puts_text_and_optional_metadata() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"message": "updated"})

    client = _client_with(handler)

    result = client.update_memory(
        "m1",
        "Follow up with recruiter Acme Corp",
        metadata={"status": "done", "resolution": "they passed"},
    )

    assert result == {"message": "updated"}
    assert captured == {
        "url": "https://memory.example.test/memories/m1",
        "method": "PUT",
        "body": {
            "text": "Follow up with recruiter Acme Corp",
            "metadata": {"status": "done", "resolution": "they passed"},
        },
    }


def test_delete_memory_handles_empty_body() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        return httpx.Response(204)

    client = _client_with(handler)

    assert client.delete_memory("m1") == {"message": "deleted"}
    assert captured == {"method": "DELETE"}


def test_list_memories_uses_default_user_and_api_key() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["api_key"] = request.headers["X-API-Key"]
        return httpx.Response(200, json=[{"memory": "hello"}])

    client = MemoryApiClient(
        MemoryApiConfig(
            base_url="https://memory.example.test",
            api_key="test-key",
            user_id="default-user",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.list_memories()

    assert result == [{"memory": "hello"}]
    assert captured == {
        "url": "https://memory.example.test/memories?user_id=default-user",
        "api_key": "test-key",
    }
