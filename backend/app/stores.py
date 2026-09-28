from __future__ import annotations

import json
import uuid
from typing import Any

from backend.app.db import connect
from backend.app.users import DEMO_USERS


def list_users() -> list[dict[str, Any]]:
    return [
        {"user_id": user["user_id"], "name": user["name"], "role": user["role"], "team": user["team"]}
        for user in DEMO_USERS.values()
    ]


def seed_user_memories(user_id: str) -> None:
    user = DEMO_USERS.get(user_id)
    if not user:
        return
    with connect() as conn:
        for memory in user["seed_memories"]:
            conn.execute(
                """
                INSERT OR IGNORE INTO user_memories(user_id, key, value, source)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, memory["key"], memory["value"], memory["source"]),
            )
        conn.commit()


def create_session(user_id: str, title: str = "New conversation") -> dict[str, Any]:
    seed_user_memories(user_id)
    session_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions(id, user_id, title) VALUES (?, ?, ?)",
            (session_id, user_id, title),
        )
        conn.commit()
    return get_session(user_id, session_id)


def list_sessions(user_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, user_id, title, summary, created_at, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_session(user_id: str, session_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, user_id, title, summary, created_at, updated_at FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def touch_session(user_id: str, session_id: str, title: str | None = None, summary: str | None = None) -> None:
    assignments = ["updated_at = CURRENT_TIMESTAMP"]
    values: list[Any] = []
    if title is not None:
        assignments.append("title = ?")
        values.append(title)
    if summary is not None:
        assignments.append("summary = ?")
        values.append(summary)
    values.extend([session_id, user_id])
    with connect() as conn:
        conn.execute(
            f"UPDATE sessions SET {', '.join(assignments)} WHERE id = ? AND user_id = ?",
            values,
        )
        conn.commit()


def add_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    citations: list[dict[str, Any]] | None = None,
    tool_trace: list[dict[str, Any]] | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO messages(session_id, user_id, role, content, citations_json, tool_trace_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                role,
                content,
                json.dumps(citations or []),
                json.dumps(tool_trace or []),
            ),
        )
        conn.commit()
    touch_session(user_id, session_id)


def list_messages(user_id: str, session_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, citations_json, tool_trace_json, created_at
            FROM messages
            WHERE session_id = ? AND user_id = ?
            ORDER BY id ASC
            """,
            (session_id, user_id),
        ).fetchall()
    messages = []
    for row in rows:
        item = dict(row)
        item["citations"] = json.loads(item.pop("citations_json") or "[]")
        item["tool_trace"] = json.loads(item.pop("tool_trace_json") or "[]")
        messages.append(item)
    return messages


def list_memories(user_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT key, value, source, updated_at FROM user_memories WHERE user_id = ? ORDER BY key",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_memory(user_id: str, key: str, value: str, source: str = "conversation") -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO user_memories(user_id, key, value, source, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, key) DO UPDATE SET
                value = excluded.value,
                source = excluded.source,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, key, value, source),
        )
        conn.commit()


def delete_memory(user_id: str, key: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM user_memories WHERE user_id = ? AND key = ?", (user_id, key))
        conn.commit()
