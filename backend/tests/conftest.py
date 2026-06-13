"""Shared test fixtures: in-memory SQLite, fake Valkey, fake LLM provider."""

import os

# Config requires these before any app import; set sane test defaults.
# A Postgres URL keeps the module-level engine valid (it never connects in tests);
# the db fixture below uses its own in-memory SQLite engine.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/test")
os.environ.setdefault("VALKEY_URL", "valkey://localhost:6379")
os.environ.setdefault("JWT_SECRET", "test-jwt")
os.environ.setdefault("MAGIC_LINK_SECRET", "test-magic")
os.environ.setdefault("RESEND_API_KEY", "test-resend")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
import app.models  # noqa: F401  (register all models on Base)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """A fresh in-memory SQLite session with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


class FakeValkey:
    """Minimal async Valkey stand-in backed by a dict of lists."""

    def __init__(self) -> None:
        self.store: dict[str, list[str]] = {}

    async def lrange(self, key, start, end):
        items = self.store.get(key, [])
        if end == -1:
            return items[start:]
        return items[start : end + 1]

    async def rpush(self, key, *values):
        self.store.setdefault(key, []).extend(values)

    async def ltrim(self, key, start, end):
        items = self.store.get(key, [])
        self.store[key] = items[start:] if end == -1 else items[start : end + 1]

    async def expire(self, key, seconds):
        return True

    async def close(self):
        return None


@pytest.fixture
def valkey() -> FakeValkey:
    return FakeValkey()


class FakeProvider:
    """LLM provider stub that streams a fixed reply in chunks."""

    def __init__(self, reply: str = "Hey baby---missed you") -> None:
        self.reply = reply
        self.calls: list[list[dict]] = []

    async def stream(self, messages, **overrides):
        self.calls.append(messages)
        for word in self.reply.split(" "):
            yield word + " "

    async def complete(self, messages, **overrides):
        return "".join([c async for c in self.stream(messages, **overrides)])


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()
