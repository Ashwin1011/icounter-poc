from __future__ import annotations

import json
from typing import Any

import anthropic

from backend.app.config import settings
from backend.app.stores import delete_memory, list_memories, upsert_memory


EXTRACT_PROMPT = """Extract durable user facts from this latest turn.
Return JSON only: {"items":[{"action":"upsert|delete","key":"short_snake","value":"fact"}]}
Only store durable preferences, role context, or investigations the user wants remembered across sessions.
If nothing should be stored, return {"items":[]}.
"""


def memory_block(user_id: str) -> str:
    memories = list_memories(user_id)
    if not memories:
        return "No persistent user memories."
    lines = [f"- {row['key']}: {row['value']}" for row in memories]
    return "Persistent user memories (this user only):\n" + "\n".join(lines)


def apply_memory_updates(user_id: str, items: list[dict[str, Any]]) -> None:
    for item in items:
        action = str(item.get("action") or "upsert").lower()
        key = str(item.get("key") or "").strip()
        value = str(item.get("value") or "").strip()
        if not key:
            continue
        if action == "delete":
            delete_memory(user_id, key)
        elif value:
            upsert_memory(user_id, key, value, source="conversation")


async def extract_memories(user_id: str, user_text: str, assistant_text: str) -> None:
    if not settings.anthropic_api_key:
        return
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=300,
            system=EXTRACT_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"User: {user_text}\nAssistant: {assistant_text}",
                }
            ],
        )
    except Exception:
        return
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return
    apply_memory_updates(user_id, payload.get("items") or [])
