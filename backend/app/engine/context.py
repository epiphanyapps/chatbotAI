"""Conversation memory: build the LLM context window from durable + fast stores.

Durable transcript lives in Postgres (survives reconnects, multi-device). A
rolling window of recent turns is cached in Valkey so we don't hit the DB on
every keystroke-fast exchange. Older turns are folded into a rolling summary so
long chats stay coherent without an unbounded context window.
"""

from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.engine.personas import build_system_prompt, get_persona
from app.engine.provider import LLMProvider
from app.models.conversation import Conversation, Message


def _window_key(conversation_id: int) -> str:
    return f"chat:window:{conversation_id}"


async def load_recent(
    conversation_id: int, db: AsyncSession, valkey
) -> list[dict]:
    """Return the recent turns as ``[{role, content}, ...]`` (no system prompt).

    Fast path: Valkey list. On a cache miss, hydrate from Postgres and warm the
    cache.
    """
    settings = get_settings()
    limit = settings.LLM_CONTEXT_TURNS

    cached = await valkey.lrange(_window_key(conversation_id), 0, -1)
    if cached:
        return [json.loads(item) for item in cached]

    # Cache miss → hydrate the last N messages from Postgres (chronological).
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    recent = [{"role": m.role, "content": m.content} for m in rows]

    if recent:
        key = _window_key(conversation_id)
        await valkey.rpush(key, *[json.dumps(r) for r in recent])
        await valkey.expire(key, 60 * 60 * 24)  # 24h
    return recent


def build_messages(
    conversation: Conversation, recent: list[dict], user_text: str
) -> list[dict]:
    """Assemble the final messages array sent to the model."""
    persona = get_persona(conversation.persona)
    system = build_system_prompt(persona)
    if conversation.summary:
        system += (
            "\n\n# Earlier in this conversation (summary, remember this)\n"
            f"{conversation.summary}"
        )
    return [{"role": "system", "content": system}, *recent, {"role": "user", "content": user_text}]


async def append_turn(
    conversation: Conversation,
    role: str,
    content: str,
    db: AsyncSession,
    valkey,
    push_cache: bool = True,
) -> Message:
    """Persist a message to Postgres; optionally push it onto the Valkey window.

    Valkey is not transactional with Postgres: if the caller's transaction later
    rolls back (e.g. the provider throws mid-stream) anything we pushed to the
    cache would survive as an orphan and poison the next prompt. So the
    streaming path persists turns with ``push_cache=False`` and only warms the
    cache via :func:`push_window` once both sides of the turn are durably
    committed. See issue #21.
    """
    message = Message(conversation_id=conversation.id, role=role, content=content)
    db.add(message)
    await db.flush()  # assign id, keep within caller's transaction

    if push_cache:
        await push_window(conversation.id, [{"role": role, "content": content}], valkey)
    return message


async def push_window(conversation_id: int, turns: list[dict], valkey) -> None:
    """Append already-committed turns to the bounded Valkey window.

    Only call this for turns that are durably persisted in Postgres, so the
    cache can never diverge from the source of truth.
    """
    if not turns:
        return
    settings = get_settings()
    key = _window_key(conversation_id)
    await valkey.rpush(key, *[json.dumps(t) for t in turns])
    # Keep the window bounded: last N turns only.
    await valkey.ltrim(key, -settings.LLM_CONTEXT_TURNS, -1)
    await valkey.expire(key, 60 * 60 * 24)


async def maybe_summarize(
    conversation: Conversation, db: AsyncSession, provider: LLMProvider
) -> None:
    """Fold older turns into ``conversation.summary`` once history grows long.

    Runs periodically (every context-window's worth of new messages past the
    threshold) so we summarize occasionally, not on every turn.
    """
    settings = get_settings()
    total = await db.scalar(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id
        )
    )
    if not total or total < settings.LLM_SUMMARY_THRESHOLD:
        return
    if total % settings.LLM_CONTEXT_TURNS != 0:
        return

    # Summarize everything except the most recent window.
    keep = settings.LLM_CONTEXT_TURNS
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.asc())
        .limit(max(total - keep, 0))
    )
    older = result.scalars().all()
    if not older:
        return

    transcript = "\n".join(f"{m.role}: {m.content}" for m in older)
    prompt = [
        {
            "role": "system",
            "content": (
                "Summarize the following adult roleplay conversation into a concise "
                "memory note (3-6 sentences). Capture names introduced, ongoing "
                "scenarios, established dynamics, and key facts the characters should "
                "remember. Write it as factual notes, not narrative."
            ),
        },
        {"role": "user", "content": transcript},
    ]
    try:
        summary = await provider.complete(prompt, max_tokens=300, temperature=0.3)
    except Exception:
        return  # summarization is best-effort; never block the chat
    if summary.strip():
        conversation.summary = summary.strip()
        db.add(conversation)
