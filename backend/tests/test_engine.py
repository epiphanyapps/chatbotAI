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


class _ThrowingProvider:
    """Provider that yields a few tokens then raises mid-stream (issue #21)."""

    def __init__(self, tokens_before_error: int = 2) -> None:
        self.tokens_before_error = tokens_before_error
        self.calls: list[list[dict]] = []

    async def stream(self, messages, **overrides):
        self.calls.append(messages)
        for i in range(self.tokens_before_error):
            yield f"tok{i} "
        raise RuntimeError("provider blew up mid-stream")

    async def complete(self, messages, **overrides):  # pragma: no cover
        raise RuntimeError("provider blew up")


@pytest.mark.asyncio
async def test_midstream_failure_leaves_valkey_and_postgres_consistent(db, valkey):
    """A provider crash mid-stream must not orphan a user turn in the cache.

    Simulates the WS/REST flow: the user turn is persisted within the request
    transaction and tokens stream out, then the provider raises. The transaction
    is rolled back (as get_db / the WS handler would on the exception), so the
    user turn never lands in Postgres — and it must also never land in Valkey,
    otherwise the next prompt is poisoned by a user-only orphan.
    """
    service = ChatService(provider=_ThrowingProvider())
    convo = await service.get_or_create_conversation(user_id=21, db=db)
    await db.commit()  # commit the conversation row, like the WS "ready" step
    convo_id = convo.id

    streamed: list[str] = []
    with pytest.raises(RuntimeError):
        async for delta in service.respond_stream(convo, "are you there?", db, valkey):
            streamed.append(delta)

    # Tokens did stream to the client before the failure.
    assert streamed == ["tok0 ", "tok1 "]

    # The request transaction rolls back on the exception (get_db / WS handler).
    await db.rollback()

    # Valkey window must NOT contain the orphaned user turn.
    key = ctx._window_key(convo_id)
    window = await valkey.lrange(key, 0, -1)
    assert window == []

    # Postgres has no message rows either — cache and durable store agree.
    rows = (await db.execute(select(Message))).scalars().all()
    assert rows == []

    # The next context window assembled from the stores has no orphaned user
    # turn waiting without a reply.
    recent = await ctx.load_recent(convo_id, db, valkey)
    assert recent == []


@pytest.mark.asyncio
async def test_successful_turn_after_failure_has_no_duplicate_user(db, valkey):
    """After a mid-stream failure + retry, the user message still appears once."""
    convo = await ChatService(provider=_ThrowingProvider()).get_or_create_conversation(
        user_id=22, db=db
    )
    await db.commit()
    convo_id = convo.id

    with pytest.raises(RuntimeError):
        async for _ in ChatService(provider=_ThrowingProvider()).respond_stream(
            convo, "hello?", db, valkey
        ):
            pass
    await db.rollback()

    from tests.conftest import FakeProvider

    # Re-fetch the conversation in the fresh transaction, like the WS handler.
    convo = await db.get(Conversation, convo_id)
    good = FakeProvider()
    bubbles = await ChatService(provider=good).respond_bubbles(convo, "hello?", db, valkey)
    await db.commit()
    assert bubbles == ["Hey baby", "missed you"]

    # Exactly one user "hello?" reached the model on the successful retry.
    sent = good.calls[0]
    user_turns = [m for m in sent if m["role"] == "user" and m["content"] == "hello?"]
    assert len(user_turns) == 1

    # Cache holds exactly the committed pair: user + assistant.
    window = await valkey.lrange(ctx._window_key(convo_id), 0, -1)
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
