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
from app.engine import safety
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
    """Incrementally fold turns that have aged out of the recent window into
    ``conversation.summary``, keeping summary + window gap-free and the
    summarizer input bounded.

    Invariant maintained: messages with ``id <= conversation.summarized_through``
    are represented in ``summary``; messages with a greater id are in the recent
    window (the last ``LLM_CONTEXT_TURNS``). The boundary is advanced so the two
    together tile the entire history with no gap (#19).

    Only the messages that *newly* aged out since the last run are read and
    folded in, alongside the previous summary text — the full prefix is never
    re-read, so the summarizer input stays bounded by ~LLM_CONTEXT_TURNS
    regardless of total conversation length (#20).
    """
    settings = get_settings()
    keep = settings.LLM_CONTEXT_TURNS

    max_id = await db.scalar(
        select(func.max(Message.id)).where(
            Message.conversation_id == conversation.id
        )
    )
    total = await db.scalar(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id
        )
    )
    if not total or total < settings.LLM_SUMMARY_THRESHOLD:
        return

    # The recent window is the last ``keep`` messages by id. Everything older than
    # the window's first message must be covered by the summary. Find the id of
    # the oldest message still inside the window so the summary boundary can be
    # advanced to exactly meet it (no gap, no overlap).
    window_first_id = await db.scalar(
        select(func.min(Message.id)).where(
            Message.conversation_id == conversation.id,
            Message.id.in_(
                select(Message.id)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.id.desc())
                .limit(keep)
            ),
        )
    )
    if window_first_id is None:
        return

    # Target boundary: everything strictly below the window must be summarized.
    target_through = window_first_id - 1
    if target_through <= conversation.summarized_through:
        return  # nothing new has aged out of the window yet

    # Read ONLY the newly-aged-out messages (bounded by ~keep per run).
    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.id > conversation.summarized_through,
            Message.id <= target_through,
        )
        .order_by(Message.id.asc())
    )
    newly_aged = result.scalars().all()
    if not newly_aged:
        return

    # Screen each newly-aged-out turn before it reaches the summarizer (a paid
    # model call): redact any blocked (e.g. CSAM) content rather than forwarding
    # it. This is a defence-in-depth backstop — the inbound and output guards
    # should have already prevented such content from being persisted. Only the
    # turns folded in *this* run are screened, preserving #19/#20's incremental,
    # bounded summarizer input.
    lines = []
    for m in newly_aged:
        content = "[redacted]" if safety.is_blocked(m.content) else m.content
        lines.append(f"{m.role}: {content}")
    transcript = "\n".join(lines)
    prior = conversation.summary or ""
    user_content = (
        (f"# Existing memory note (carry forward, do not drop facts)\n{prior}\n\n" if prior else "")
        + "# New turns to fold into the memory note\n"
        + transcript
    )
    prompt = [
        {
            "role": "system",
            "content": (
                "You maintain a running memory note for an adult roleplay "
                "conversation. Merge the new turns into the existing memory note "
                "and return a single concise note (3-6 sentences). Preserve names "
                "introduced, ongoing scenarios, established dynamics, and key facts "
                "the characters should remember. Write factual notes, not narrative."
            ),
        },
        {"role": "user", "content": user_content},
    ]
    try:
        summary = await provider.complete(prompt, max_tokens=300, temperature=0.3)
    except Exception:
        return  # summarization is best-effort; never block the chat
    if summary.strip():
        conversation.summary = summary.strip()
        conversation.summarized_through = target_through
        db.add(conversation)
