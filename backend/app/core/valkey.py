"""Valkey (Redis-compatible) client for session storage."""

import ssl
from typing import AsyncGenerator
from urllib.parse import urlparse

from valkey.asyncio import Valkey

from app.core.config import get_settings


def create_valkey_client() -> Valkey:
    """Create Valkey client with SSL support for DigitalOcean managed instances."""
    settings = get_settings()
    parsed = urlparse(settings.VALKEY_URL)

    # DigitalOcean managed Valkey uses TLS — emitted as either valkeys:// or rediss://
    use_ssl = parsed.scheme in ("valkeys", "rediss")

    # Extract connection parameters
    host = parsed.hostname or "localhost"
    port = parsed.port or 25061
    password = parsed.password
    username = parsed.username or "default"

    if use_ssl:
        # Verify the server cert; load the managed cluster CA when provided
        # (DigitalOcean's CA is not a public root).
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        if settings.VALKEY_SSL_CA:
            from app.core.database import ca_pem

            ssl_context.load_verify_locations(cadata=ca_pem(settings.VALKEY_SSL_CA))

        return Valkey(
            host=host,
            port=port,
            password=password,
            username=username,
            ssl=ssl_context,
            decode_responses=True,
        )

    return Valkey(
        host=host,
        port=port,
        password=password,
        username=username,
        decode_responses=True,
    )


# Global client instance (lazy initialization)
_valkey_client: Valkey | None = None


async def get_valkey() -> AsyncGenerator[Valkey, None]:
    """Dependency that yields Valkey client."""
    global _valkey_client

    if _valkey_client is None:
        _valkey_client = create_valkey_client()

    yield _valkey_client


async def close_valkey() -> None:
    """Close Valkey connection on shutdown."""
    global _valkey_client

    if _valkey_client is not None:
        await _valkey_client.close()
        _valkey_client = None
