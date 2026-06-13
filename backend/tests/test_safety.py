"""Unit tests for the programmatic CSAM/illegal-content safety guard.

Covers the detector directly (benign passes, minor+sexual co-occurrence is
caught) and the engine/REST wiring (blocked output is not persisted; the REST
endpoint rejects blocked input).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_age_verified_user
from app.core.database import Base, get_db
from app.core.valkey import get_valkey
from app.engine import safety
from app.engine.service import BlockedContentError, ChatService
from app.models.conversation import Message
from app.models.user import User
import app.models  # noqa: F401
from tests.conftest import FakeProvider, FakeValkey


# --- Detector unit tests ----------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "hey babe, you up?",
        "I want you so bad, come over and fuck me",  # explicit ADULT content
        "she's a gorgeous 25 year old and so horny",  # adult age stated
        "the kids are at school so we have the house to ourselves",  # no sexual ctx
        "I love how naughty you are",
        "",
        "   ",
    ],
)
def test_benign_and_adult_content_passes(text):
    assert safety.is_blocked(text) is False
    assert safety.check(text).blocked is False


@pytest.mark.parametrize(
    "text",
    [
        "sexy 12 year old",
        "she is 15 years old and we had sex",
        "a naked child",
        "underage girl giving a blowjob",
        "schoolgirl pussy",
        "this 9yo is so horny",
        "loli porn naked",
    ],
)
def test_minor_plus_sexual_context_is_blocked(text):
    verdict = safety.check(text)
    assert verdict.blocked is True
    assert verdict.reason  # a machine-readable reason tag is set


def test_block_reason_is_generic_and_does_not_echo_content():
    # The user-facing reason must not contain any input content.
    assert "child" not in safety.BLOCK_REASON.lower()
    assert safety.BLOCK_REASON


def test_minor_term_without_sexual_context_passes():
    assert safety.is_blocked("my kid started third grade today") is False


# --- Engine wiring: blocked OUTPUT is not persisted -------------------------

@pytest.mark.asyncio
async def test_blocked_model_output_is_not_persisted(db, valkey):
    # Provider returns CSAM-flavoured output; service must refuse to persist it.
    provider = FakeProvider("she is a naked 12 year old")
    service = ChatService(provider=provider)
    convo = await service.get_or_create_conversation(user_id=99, db=db)

    with pytest.raises(BlockedContentError):
        await service.respond_bubbles(convo, "hi", db, valkey)
    await db.commit()

    rows = (await db.execute(select(Message).order_by(Message.id))).scalars().all()
    roles_contents = [(m.role, m.content) for m in rows]
    # The (screened) user turn may be persisted, but no assistant reply is.
    assert ("assistant", "she is a naked 12 year old") not in roles_contents
    assert all(r != "assistant" for r, _ in roles_contents)


# --- REST endpoint rejects blocked INPUT ------------------------------------

@pytest.fixture
def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_create_all(engine))

    fake_valkey = FakeValkey()

    async def override_get_db():
        async with Session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_get_valkey():
        yield fake_valkey

    async def override_user():
        return User(id=1, email="t@example.com", email_verified=True, age_verified=True)

    import app.main as app_main
    from app.main import app
    from app.chat import router as chat_router

    async def _noop():
        return None

    app_main.create_tables = _noop
    chat_router.service.provider = FakeProvider("Hi cucky---you up?")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_valkey] = override_get_valkey
    app.dependency_overrides[get_age_verified_user] = override_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


async def _create_all(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def test_post_message_rejects_blocked_input(client):
    resp = client.post("/chat/message", json={"text": "sexy 12 year old"})
    assert resp.status_code == 422, resp.text
    # The generic detail must not echo the offending content.
    assert "12" not in resp.json()["detail"]
    assert resp.json()["detail"] == safety.BLOCK_REASON

    # Nothing was persisted for the blocked turn.
    hist = client.get("/chat/history").json()
    assert hist["messages"] == []


def test_post_message_allows_benign_input(client):
    resp = client.post("/chat/message", json={"text": "hey you"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["bubbles"] == ["Hi cucky", "you up?"]
