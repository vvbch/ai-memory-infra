"""Thin REST client used by MCP tools."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://memory.chandrav.dev"
DEFAULT_USER_ID = "chrome-extension-user"


class MemoryApiConfigError(RuntimeError):
    """Raised when required local configuration is missing."""


@dataclass(frozen=True)
class MemoryApiConfig:
    base_url: str
    api_key: str
    user_id: str

    @classmethod
    def from_env(cls) -> MemoryApiConfig:
        api_key = os.environ.get("AI_MEMORY_API_KEY")
        if not api_key:
            raise MemoryApiConfigError("Set AI_MEMORY_API_KEY before starting the MCP server.")

        return cls(
            base_url=os.environ.get("AI_MEMORY_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            api_key=api_key,
            user_id=os.environ.get("AI_MEMORY_USER_ID", DEFAULT_USER_ID),
        )


class MemoryApiClient:
    def __init__(
        self,
        config: MemoryApiConfig,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._client = http_client or httpx.Client(timeout=30)

    def search_memories(
        self,
        query: str,
        *,
        user_id: str | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        selected_user = user_id or self._config.user_id
        payload: dict[str, Any] = {
            "query": query,
            "user_id": selected_user,
            "top_k": top_k,
        }
        return self._post("/search", payload)

    def add_memory(
        self,
        text: str,
        *,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messages": [{"role": "user", "content": text}],
            "user_id": user_id or self._config.user_id,
            "metadata": metadata,
            "infer": True,
        }
        return self._post("/memories", payload)

    def list_memories(self, *, user_id: str | None = None) -> Any:
        response = self._client.get(
            f"{self._config.base_url}/memories",
            params={"user_id": user_id or self._config.user_id},
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(
            f"{self._config.base_url}{path}",
            json=payload,
            headers=self._headers(),
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return {"results": data}
        return data

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self._config.api_key}
