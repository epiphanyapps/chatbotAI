"""Engine unit tests: persona prompt, bubble splitting, context, ChatService."""

import pytest
from sqlalchemy import select

from app.core.config import get_settings
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


async def _seed_messages(convo: Conversation, n: int, db) -> list[Message]:
    """Insert ``n`` alternating user/assistant messages and return them by id."""
    msgs = []
    for i in range(n):
        role = "user" if i % 2 == 0 else "assistant"
        msgs.append(Message(conversation_id=convo.id, role=role, content=f"msg-{i}"))
    db.add_all(msgs)
    await db.flush()
    return msgs


@pytest.mark.asyncio
async def test_summary_and_window_are_gap_free(db, valkey, provider):
    """#19 regression: every message is covered by either the summary
    (id <= summarized_through) or the recent window (last N) — never absent
    from both. Checked across many total lengths as the window slides."""
    keep = get_settings().LLM_CONTEXT_TURNS
    service = ChatService(provider=provider)

    for k in range(1, keep + 1):
        total = keep * 2 + k  # past the summary threshold, window has slid
        convo = await service.get_or_create_conversation(user_id=1000 + k, db=db)
        msgs = await _seed_messages(convo, total, db)

        await ctx.maybe_summarize(convo, db, provider)

        all_ids = {m.id for m in msgs}
        # Recent window = last `keep` messages by id (what build_messages will use).
        window_ids = {m.id for m in sorted(msgs, key=lambda m: m.id)[-keep:]}
        summarized_ids = {m.id for m in msgs if m.id <= convo.summarized_through}

        covered = window_ids | summarized_ids
        missing = all_ids - covered
        assert not missing, (
            f"total={total}: ids {sorted(missing)} are in NEITHER summary "
            f"(through {convo.summarized_through}) nor window {sorted(window_ids)}"
        )
        # Boundary must meet the window exactly: summary ends right where the
        # window begins (no gap, no large overlap).
        assert convo.summarized_through == min(window_ids) - 1


@pytest.mark.asyncio
async def test_summarizer_input_is_bounded(db, valkey, provider):
    """#20 regression: the transcript handed to the summarizer per call stays
    bounded (~CONTEXT_TURNS messages) and does NOT grow with total history,
    because only newly-aged-out turns are folded in each run."""
    settings = get_settings()
    keep = settings.LLM_CONTEXT_TURNS
    threshold = settings.LLM_SUMMARY_THRESHOLD
    service = ChatService(provider=provider)
    convo = await service.get_or_create_conversation(user_id=2000, db=db)

    # Seed past the threshold so summarization is active, then walk the
    # conversation forward many turns, summarizing each step like the live path.
    await _seed_messages(convo, threshold, db)

    def _turns_in_last_call() -> int:
        user_msg = provider.calls[-1][-1]["content"]
        return sum(
            1
            for ln in user_msg.splitlines()
            if ln.startswith("user:") or ln.startswith("assistant:")
        )

    # First (catch-up) summarization, then keep growing the conversation far
    # beyond `keep` and summarize at each step like the live path.
    await ctx.maybe_summarize(convo, db, provider)
    first_call_turns = _turns_in_last_call()

    per_step_turns: list[int] = []
    for _ in range(keep * 4):  # grow total by 4*keep — well past any window
        await _seed_messages(convo, 1, db)
        before = len(provider.calls)
        await ctx.maybe_summarize(convo, db, provider)
        if len(provider.calls) > before:
            per_step_turns.append(_turns_in_last_call())

    max_turns = max([first_call_turns, *per_step_turns])

    # Bounded independent of total length: even the one-time catch-up fold is
    # capped by the (constant) threshold-sized prefix, and steady-state folds are
    # tiny. Unbounded behaviour would feed total-keep lines (hundreds+).
    assert 0 < max_turns <= threshold, (
        f"summarizer ingested {max_turns} turns; expected <= {threshold}"
    )
    # And it must NOT grow as the conversation lengthens: steady-state folds stay
    # small no matter how long the chat gets.
    assert per_step_turns, "expected steady-state summarizations to occur"
    assert max(per_step_turns) <= keep
