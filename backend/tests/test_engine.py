"""Engine unit tests: persona prompt, bubble splitting, context, ChatService."""

import pytest
from sqlalchemy import select

from app.engine import context as ctx
from app.engine.personas import build_system_prompt, get_persona
from app.engine.service import ChatService, split_bubbles
from app.models.conversation import Conversation, Message


def test_split_bubbles():
    assert split_bubbles("hi---there---you") == ["hi", "there", "you"]
    assert split_bubbles("single") == ["single"]
    assert split_bubbles("a--- ---b") == ["a", "b"]  # blank middle dropped


def test_system_prompt_encodes_persona_and_rules():
    prompt = build_system_prompt(get_persona("sophia"))
    assert "Sophia" in prompt
    assert "stay" in prompt.lower() and "character" in prompt.lower()
    assert "never involve minors" in prompt.lower()
    assert "Marcus" in prompt  # name pool migrated from old personality data


@pytest.mark.asyncio
async def test_build_messages_order_and_summary():
    convo = Conversation(id=1, user_id=1, persona="sophia", summary="They met at a bar.")
    recent = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}]
    messages = ctx.build_messages(convo, recent, "you up?")

    assert messages[0]["role"] == "system"
    assert "They met at a bar." in messages[0]["content"]  # summary folded in
    assert messages[1:-1] == recent  # history preserved in order
    assert messages[-1] == {"role": "user", "content": "you up?"}


@pytest.mark.asyncio
async def test_chatservice_persists_and_returns_bubbles(db, valkey, provider):
    service = ChatService(provider=provider)
    convo = await service.get_or_create_conversation(user_id=42, db=db)

    bubbles = await service.respond_bubbles(convo, "hi sophia", db, valkey)
    await db.commit()

    # FakeProvider replies "Hey baby---missed you" → two bubbles.
    assert bubbles == ["Hey baby", "missed you"]

    rows = (await db.execute(select(Message).order_by(Message.id))).scalars().all()
    assert [(m.role, m.content) for m in rows][0] == ("user", "hi sophia")
    assert rows[1].role == "assistant"
    assert "Hey baby" in rows[1].content

    # The user message must reach the model exactly once (not duplicated).
    sent = provider.calls[0]
    user_turns = [m for m in sent if m["role"] == "user" and m["content"] == "hi sophia"]
    assert len(user_turns) == 1


@pytest.mark.asyncio
async def test_valkey_window_warmed_and_bounded(db, valkey, provider):
    service = ChatService(provider=provider)
    convo = await service.get_or_create_conversation(user_id=7, db=db)

    await service.respond_bubbles(convo, "first", db, valkey)
    await db.commit()

    key = ctx._window_key(convo.id)
    window = await valkey.lrange(key, 0, -1)
    # One user + one assistant turn cached for fast context assembly.
    assert len(window) == 2


@pytest.mark.asyncio
async def test_history_hydrates_from_postgres_on_cache_miss(db, valkey, provider):
    service = ChatService(provider=provider)
    convo = await service.get_or_create_conversation(user_id=9, db=db)
    db.add_all([
        Message(conversation_id=convo.id, role="user", content="older"),
        Message(conversation_id=convo.id, role="assistant", content="reply"),
    ])
    await db.flush()

    recent = await ctx.load_recent(convo.id, db, valkey)  # empty cache → DB
    assert [m["content"] for m in recent] == ["older", "reply"]
