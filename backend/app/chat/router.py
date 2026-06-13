"""Chat endpoints.

- ``WebSocket /chat/ws``   — primary real-time channel (token streaming + typing).
- ``GET  /chat/history``   — load the transcript on reconnect.
- ``POST /chat/message``   — non-streaming fallback; the Telegram bot calls this.

All paths run through ``ChatService`` so web and Telegram share one engine.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_age_verified_user
from app.auth.jwt_handler import SessionManager
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, get_db
from app.core.valkey import create_valkey_client, get_valkey
from app.engine.service import ChatService, split_bubbles
from app.models.conversation import Conversation, Message
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])

service = ChatService()

# Upper bound on a single inbound message. A paid per-token backend makes
# unbounded input a cost/abuse vector; cap it on every entry point (REST + WS).
MAX_MESSAGE_CHARS = 4000


class MessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class MessageResponse(BaseModel):
    conversation_id: int
    bubbles: list[str]


@router.post("/message", response_model=MessageResponse)
async def send_message(
    body: MessageRequest,
    user: User = Depends(get_age_verified_user),
    db: AsyncSession = Depends(get_db),
    valkey=Depends(get_valkey),
) -> MessageResponse:
    """Non-streaming reply, returned as texting-style bubbles."""
    conversation = await service.get_or_create_conversation(user.id, db)
    bubbles = await service.respond_bubbles(conversation, body.text, db, valkey)
    return MessageResponse(conversation_id=conversation.id, bubbles=bubbles)


@router.get("/history")
async def get_history(
    user: User = Depends(get_age_verified_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the user's active conversation transcript for reconnect."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.last_message_at.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        return {"conversation_id": None, "messages": []}

    rows = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.asc())
    )
    messages = [
        {
            "role": m.role,
            "content": m.content,
            "bubbles": split_bubbles(m.content) if m.role == "assistant" else [m.content],
            "created_at": m.created_at.isoformat(),
        }
        for m in rows.scalars().all()
    ]
    return {"conversation_id": conversation.id, "messages": messages}


async def _authenticate_ws(token: str, db: AsyncSession, valkey) -> User | None:
    """Resolve a WebSocket connection's bearer token to an age-verified user."""
    settings = get_settings()
    payload = SessionManager(settings.JWT_SECRET, valkey).verify_access_token(token)
    if not payload:
        return None
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not user.email_verified or not user.age_verified:
        return None
    return user


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    """Real-time chat: client sends {text}, server streams tokens + typing.

    Auth token arrives as a WebSocket subprotocol (``["bearer", "<token>"]``),
    not in the URL — keeps the JWT out of access logs and browser history.
    """
    # subprotocols offered by the client, e.g. ["bearer", "<jwt>"].
    offered = websocket.scope.get("subprotocols", [])
    token = offered[1] if len(offered) >= 2 and offered[0] == "bearer" else ""
    # Echo back the "bearer" subprotocol (never the token itself) on accept.
    await websocket.accept(subprotocol="bearer" if token else None)
    valkey = create_valkey_client()

    try:
        # Authenticate once, on connect, using a short-lived session.
        async with AsyncSessionLocal() as db:
            user = await _authenticate_ws(token, db, valkey)
        if user is None:
            await websocket.close(code=4401)  # unauthorized
            return

        async with AsyncSessionLocal() as db:
            conversation = await service.get_or_create_conversation(user.id, db)
            conversation_id = conversation.id
            await db.commit()
        await websocket.send_json({"type": "ready", "conversation_id": conversation_id})

        while True:
            data = await websocket.receive_json()
            text = (data or {}).get("text", "").strip()
            if not text:
                continue
            # Same cap as the REST body; reject oversized frames instead of
            # forwarding them to the (paid, per-token) model.
            if len(text) > MAX_MESSAGE_CHARS:
                await websocket.send_json(
                    {"type": "error", "detail": "message too long"}
                )
                continue

            await websocket.send_json({"type": "typing"})

            # One DB transaction per turn so each exchange is durably committed.
            async with AsyncSessionLocal() as db:
                conversation = await db.get(Conversation, conversation_id)
                async for delta in service.respond_stream(conversation, text, db, valkey):
                    await websocket.send_json({"type": "token", "delta": delta})
                await db.commit()

            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass
    finally:
        await valkey.close()
