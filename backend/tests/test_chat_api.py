"""Integration test for the REST chat path: HTTP → router → engine → DB."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_age_verified_user
from app.core.database import Base, get_db
from app.core.valkey import get_valkey
from app.models.user import User
import app.models  # noqa: F401
from tests.conftest import FakeProvider, FakeValkey


@pytest.fixture
def client():
    # Shared in-memory DB (StaticPool) so every session sees the same rows.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    import asyncio

    asyncio.get_event_loop().run_until_complete(_create_all(engine))

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

    # Import after env is set up by conftest.
    import app.main as app_main
    from app.main import app
    from app.chat import router as chat_router

    # Lifespan startup would hit the global Postgres engine; the fixture already
    # created its own tables, so make startup table-creation a no-op.
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


def test_post_message_returns_bubbles_and_persists(client):
    resp = client.post("/chat/message", json={"text": "hey"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["bubbles"] == ["Hi cucky", "you up?"]
    assert isinstance(data["conversation_id"], int)

    # History endpoint should now return the persisted transcript.
    hist = client.get("/chat/history").json()
    roles = [m["role"] for m in hist["messages"]]
    assert roles == ["user", "assistant"]
    assert hist["messages"][1]["bubbles"] == ["Hi cucky", "you up?"]
