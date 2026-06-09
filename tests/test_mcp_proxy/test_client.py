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
