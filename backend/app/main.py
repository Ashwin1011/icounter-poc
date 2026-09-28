from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.agent import run_turn
from backend.app.config import settings
from backend.app.db import init_db
from backend.app.mcp_client import gateway
from backend.app.stores import (
    create_session,
    get_session,
    list_memories,
    list_messages,
    list_sessions,
    list_users,
    seed_user_memories,
)
from backend.app.users import get_user


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    for user in list_users():
        seed_user_memories(user["user_id"])
    try:
        yield
    finally:
        await gateway.close()


app = FastAPI(title="Nexora Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str = Field(min_length=1)
    fail: str | None = None


class SessionCreate(BaseModel):
    user_id: str
    title: str = "New conversation"


def _require_user(user_id: str) -> None:
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="Unknown user")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "nexora-api", "model": settings.anthropic_model}


@app.get("/api/users")
def users() -> dict:
    return {"users": list_users()}


@app.get("/api/sessions")
def sessions(user_id: str = Query(...)) -> dict:
    _require_user(user_id)
    return {"sessions": list_sessions(user_id)}


@app.post("/api/sessions")
def new_session(body: SessionCreate) -> dict:
    _require_user(body.user_id)
    return create_session(body.user_id, body.title)


@app.get("/api/sessions/{session_id}")
def session_detail(session_id: str, user_id: str = Query(...)) -> dict:
    _require_user(user_id)
    session = get_session(user_id, session_id)
    if session is None:
        raise HTTPException(status_code=403, detail="Session is not visible to this user")
    return session


@app.get("/api/sessions/{session_id}/messages")
def session_messages(session_id: str, user_id: str = Query(...)) -> dict:
    _require_user(user_id)
    if get_session(user_id, session_id) is None:
        raise HTTPException(status_code=403, detail="Session is not visible to this user")
    return {"messages": list_messages(user_id, session_id)}


@app.get("/api/memory")
def memory(user_id: str = Query(...)) -> dict:
    _require_user(user_id)
    return {"memories": list_memories(user_id)}


@app.post("/api/chat")
async def chat(
    body: ChatRequest,
    x_nexora_fail: str | None = Header(default=None),
    fail: str | None = Query(default=None),
) -> StreamingResponse:
    _require_user(body.user_id)
    if get_session(body.user_id, body.session_id) is None:
        raise HTTPException(status_code=403, detail="Session is not visible to this user")
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured")
    fail_mode = fail or body.fail or x_nexora_fail
    return StreamingResponse(
        run_turn(body.user_id, body.session_id, body.message, fail_mode=fail_mode),
        media_type="text/event-stream",
    )
