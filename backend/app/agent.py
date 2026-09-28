from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import anthropic

from backend.app.config import settings
from backend.app.mcp_client import gateway
from backend.app.memory import extract_memories, memory_block
from backend.app.security import SYSTEM_RULES, extract_citations, wrap_untrusted
from backend.app.stores import add_message, get_session, list_messages, touch_session
from backend.app.users import require_user


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=True)}\n\n"


def _history_messages(user_id: str, session_id: str) -> list[dict[str, Any]]:
    rows = list_messages(user_id, session_id)
    trimmed = rows[-settings.max_history_messages :]
    messages: list[dict[str, Any]] = []
    for row in trimmed:
        if row["role"] not in {"user", "assistant"}:
            continue
        messages.append({"role": row["role"], "content": row["content"]})
    return messages


def _maybe_summarize(user_id: str, session_id: str) -> str:
    session = get_session(user_id, session_id)
    return (session or {}).get("summary") or ""


async def run_turn(
    user_id: str,
    session_id: str,
    user_text: str,
    fail_mode: str | None = None,
) -> AsyncIterator[str]:
    require_user(user_id)
    if get_session(user_id, session_id) is None:
        yield _sse("error", {"error": "Session not found for this user.", "code": "forbidden"})
        return

    add_message(user_id, session_id, "user", user_text)
    if fail_mode in {"tools", "db"}:
        message = (
            "I could not complete that request because a required tool or data store failed. "
            "I will not invent Nexora facts to fill the gap."
        )
        add_message(user_id, session_id, "assistant", message)
        yield _sse("token", {"text": message})
        yield _sse("done", {"citations": [], "tool_trace": [{"name": "forced_failure", "error": fail_mode}]})
        return

    user = require_user(user_id)
    history = _history_messages(user_id, session_id)
    summary = _maybe_summarize(user_id, session_id)
    system = (
        f"{SYSTEM_RULES}\n\n"
        f"Authenticated user: {user['name']} ({user_id}), {user['role']}, team {user['team']}.\n"
        f"{memory_block(user_id)}\n"
    )
    if summary:
        system += f"\nSession summary: {summary}\n"

    try:
        tools = await gateway.list_anthropic_tools()
    except Exception as exc:  # noqa: BLE001
        message = f"The tool service is unavailable, so I cannot look up Nexora data. ({exc})"
        add_message(user_id, session_id, "assistant", message)
        yield _sse("error", {"error": message, "code": "mcp_unavailable"})
        return

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages: list[dict[str, Any]] = history
    citations: list[dict[str, Any]] = []
    tool_trace: list[dict[str, Any]] = []
    assistant_text = ""

    for _hop in range(settings.max_tool_hops):
        try:
            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=1600,
                system=system,
                tools=tools,
                messages=messages,
            )
        except Exception as exc:  # noqa: BLE001
            message = "The language model request failed. No additional facts were generated."
            add_message(user_id, session_id, "assistant", message)
            yield _sse("error", {"error": f"{message} ({exc})", "code": "llm_failure"})
            return

        assistant_blocks = []
        tool_uses = []
        for block in response.content:
            if block.type == "text" and block.text:
                assistant_text += block.text
                yield _sse("token", {"text": block.text})
                assistant_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                tool_uses.append(block)
                assistant_blocks.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
                yield _sse("tool_start", {"name": block.name, "input": block.input})

        messages.append({"role": "assistant", "content": assistant_blocks})

        if response.stop_reason != "tool_use" or not tool_uses:
            break

        tool_results = []
        for block in tool_uses:
            payload = await gateway.call_tool(
                block.name,
                block.input if isinstance(block.input, dict) else {},
                timeout=settings.tool_timeout_seconds,
            )
            found = extract_citations(payload)
            citations.extend(found)
            tool_trace.append({"name": block.name, "input": block.input, "result": payload})
            yield _sse("tool_result", {"name": block.name, "result": payload, "citations": found})
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": wrap_untrusted("tool", block.name, payload),
                }
            )
        messages.append({"role": "user", "content": tool_results})
    else:
        note = " I stopped after the maximum number of tool hops to avoid an unbounded loop."
        assistant_text += note
        yield _sse("token", {"text": note})

    if not assistant_text.strip():
        assistant_text = "I could not produce an answer from the available tools."

    unique_citations = []
    seen = set()
    for citation in citations:
        path = citation.get("path")
        if path and path not in seen:
            seen.add(path)
            unique_citations.append(citation)

    add_message(
        user_id,
        session_id,
        "assistant",
        assistant_text,
        citations=unique_citations,
        tool_trace=tool_trace,
    )
    first_line = user_text.strip().splitlines()[0][:80]
    touch_session(user_id, session_id, title=first_line)
    await extract_memories(user_id, user_text, assistant_text)
    yield _sse("done", {"citations": unique_citations, "tool_trace": tool_trace})
