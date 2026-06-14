"""Database connection and session management using SQLAlchemy async."""

import base64
import ssl
from typing import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

# libpq-only query params that asyncpg rejects (SSL is applied via connect_args).
_LIBPQ_ONLY_PARAMS = {"sslmode", "ssl", "channel_binding", "sslrootcert", "sslcert", "sslkey"}


def ca_pem(ca: str) -> str:
    """Return PEM text from a CA cert that may be raw PEM or base64-encoded PEM.

    DigitalOcean's ``digitalocean_database_ca`` exposes the cert base64-encoded;
    accept either form so the env wiring is robust.
    """
    ca = ca.strip()
    if "BEGIN CERTIFICATE" in ca:
        return ca
    try:
        return base64.b64decode(ca).decode()
    except Exception:
        return ca


def normalize_db_url(url: str) -> str:
    """Coerce a Postgres URL to the asyncpg driver and drop libpq-only params.

    Managed providers (e.g. DigitalOcean) hand out ``postgresql://…?sslmode=require``;
    SQLAlchemy needs ``postgresql+asyncpg://…`` and asyncpg errors on ``sslmode``.
    SSL itself is reattached via :func:`db_connect_args`.
    """
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql") or scheme.startswith("postgresql+"):
        scheme = "postgresql+asyncpg"
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in _LIBPQ_ONLY_PARAMS]
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def db_connect_args(url: str, ca_cert: str = "") -> dict:
    """asyncpg connect args: encrypt and **verify** the server certificate.

    Managed providers whose CA is not a public root (DigitalOcean) require the
    cluster CA PEM, supplied via ``settings.DATABASE_SSL_CA``, so verification
    succeeds without disabling it. Returns no SSL when the URL opts out
    (``sslmode=disable`` or no sslmode for local/plaintext dev).
    """
    sslmode = dict(parse_qsl(urlsplit(url).query)).get("sslmode", "")
    if sslmode in ("", "disable"):
        return {}
    ctx = ssl.create_default_context()  # CERT_REQUIRED + hostname check
    if ca_cert:
        ctx.load_verify_locations(cadata=ca_pem(ca_cert))
    return {"ssl": ctx}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


settings = get_settings()

# Create async engine
engine = create_async_engine(
    normalize_db_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=db_connect_args(settings.DATABASE_URL, settings.DATABASE_SSL_CA),
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables in the database (use with caution)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
