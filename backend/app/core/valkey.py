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

    # DigitalOcean managed Valkey uses SSL (valkeys:// protocol)
    use_ssl = parsed.scheme == "valkeys"

    # Extract connection parameters
    host = parsed.hostname or "localhost"
    port = parsed.port or 25061
    password = parsed.password
    username = parsed.username or "default"

    if use_ssl:
        # Create SSL context for DigitalOcean managed Valkey
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED

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
