from __future__ import annotations

import asyncio
import json
from typing import Any

from fastmcp import Client

from backend.app.config import settings


def _content_to_json(result: Any) -> Any:
    if hasattr(result, "data") and result.data is not None:
        return result.data
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    texts: list[str] = []
    content = getattr(result, "content", None) or []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            texts.append(text)
    if not texts:
        return {"ok": False, "error": "Empty tool response", "code": "invalid_tool_response", "retryable": False}
    joined = "\n".join(texts)
    try:
        return json.loads(joined)
    except json.JSONDecodeError:
        return {"ok": True, "data": joined}


class McpGateway:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or settings.mcp_url
        self._client: Client | None = None
        self._tools: list[dict[str, Any]] | None = None

    async def connect(self) -> Client:
        if self._client is None:
            self._client = Client(self.url)
            await self._client.__aenter__()
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None

    async def list_anthropic_tools(self) -> list[dict[str, Any]]:
        if self._tools is not None:
            return self._tools
        client = await self.connect()
        tools = await client.list_tools()
        mapped = []
        for tool in tools:
            mapped.append(
                {
                    "name": tool.name,
                    "description": tool.description or tool.name,
                    "input_schema": tool.inputSchema or {"type": "object", "properties": {}},
                }
            )
        self._tools = mapped
        return mapped

    async def call_tool(self, name: str, arguments: dict[str, Any], timeout: float) -> Any:
        client = await self.connect()
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                result = await asyncio.wait_for(client.call_tool(name, arguments), timeout=timeout)
                return _content_to_json(result)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt == 0:
                    await asyncio.sleep(0.3)
                    continue
        return {
            "ok": False,
            "error": f"Tool '{name}' failed: {last_error}",
            "code": "tool_failure",
            "retryable": True,
        }


gateway = McpGateway()
