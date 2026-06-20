"""Thin REST client used by MCP tools."""



from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from mcp_proxy.idempotent_write import (
    add_memory_idempotent,
    find_by_external_id,
    write_timeout_seconds,
)

DEFAULT_BASE_URL = "https://memory.example.com"

# ADR 028: one user_id for the person across every source; identity is never the
# discriminator. Override via AI_MEMORY_USER_ID / AI_MEMORY_BASE_URL for deploy.

DEFAULT_USER_ID = "primary-user"





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





def _default_timeout() -> httpx.Timeout:

    return httpx.Timeout(write_timeout_seconds(), connect=10.0)





class MemoryApiClient:

    def __init__(

        self,

        config: MemoryApiConfig,

        http_client: httpx.Client | None = None,

    ) -> None:

        self._config = config

        self._client = http_client or httpx.Client(timeout=_default_timeout())



    def search_memories(

        self,

        query: str,

        *,

        user_id: str | None = None,

        top_k: int = 5,

        filters: dict[str, Any] | None = None,

    ) -> dict[str, Any]:

        selected_user = user_id or self._config.user_id

        payload: dict[str, Any] = {

            "query": query,

            "user_id": selected_user,

            "top_k": top_k,

        }

        # ADR 029 / Phase 0: the live `/search` supports server-side metadata

        # filtering (e.g. {"type": "open_item"}). Only sent when provided so the

        # plain-search request shape is unchanged.

        if filters is not None:

            payload["filters"] = filters

        return self._post("/search", payload)



    def add_memory(

        self,

        text: str,

        *,

        user_id: str | None = None,

        metadata: dict[str, Any] | None = None,

        infer: bool = True,

    ) -> dict[str, Any]:

        # `infer=True` (default) runs Mem0's fact-extraction pipeline; `infer=False`

        # stores the text verbatim — required for authored open items / decisions so

        # they are not reworded (ADR 029, Phase 0 de-risk).

        payload: dict[str, Any] = {

            "messages": [{"role": "user", "content": text}],

            "user_id": user_id or self._config.user_id,

            "metadata": metadata,

            "infer": infer,

        }

        return self._post("/memories", payload)



    def add_memory_idempotent(

        self,

        text: str,

        *,

        external_id: str,

        user_id: str | None = None,

        metadata: dict[str, Any] | None = None,

        infer: bool = True,

    ) -> dict[str, Any]:

        """Idempotent write with verify-then-skip on timeout (ADR 037)."""

        return add_memory_idempotent(

            self,

            text,

            external_id=external_id,

            user_id=user_id,

            metadata=metadata,

            infer=infer,

        )



    def find_by_external_id(

        self,

        external_id: str,

        *,

        user_id: str | None = None,

        cache: list[dict[str, Any]] | None = None,

    ) -> dict[str, Any] | None:

        return find_by_external_id(self, external_id, user_id=user_id, cache=cache)



    def list_memories(

        self,

        *,

        user_id: str | None = None,

        limit: int | None = None,

    ) -> Any:

        params: dict[str, Any] = {"user_id": user_id or self._config.user_id}

        if limit is not None:

            params["limit"] = limit

        response = self._client.get(

            f"{self._config.base_url}/memories",

            params=params,

            headers=self._headers(),

        )

        response.raise_for_status()

        return response.json()



    def get_memory(self, memory_id: str) -> dict[str, Any]:

        response = self._client.get(

            f"{self._config.base_url}/memories/{memory_id}",

            headers=self._headers(),

        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):

            return {"results": data}

        return data



    def update_memory(

        self,

        memory_id: str,

        text: str,

        *,

        metadata: dict[str, Any] | None = None,

    ) -> dict[str, Any]:

        # Live Mem0 OSS `PUT /memories/{id}` requires `text`; `metadata` is optional

        # (verified against mem0ai/mem0 server/main.py MemoryUpdate schema).

        payload: dict[str, Any] = {"text": text}

        if metadata is not None:

            payload["metadata"] = metadata

        response = self._client.put(

            f"{self._config.base_url}/memories/{memory_id}",

            json=payload,

            headers=self._headers(),

        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):

            return {"results": data}

        return data



    def delete_memory(self, memory_id: str) -> dict[str, Any]:

        response = self._client.delete(

            f"{self._config.base_url}/memories/{memory_id}",

            headers=self._headers(),

        )

        response.raise_for_status()

        if not response.content:

            return {"message": "deleted"}

        data = response.json()

        if not isinstance(data, dict):

            return {"results": data}

        return data



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


