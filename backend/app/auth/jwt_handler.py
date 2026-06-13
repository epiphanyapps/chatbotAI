"""JWT session management with Valkey-backed refresh tokens."""

from datetime import datetime, timedelta, timezone

import jwt
from valkey.asyncio import Valkey


class SessionManager:
    """Manages JWT access and refresh tokens with Valkey storage.

    Access tokens are short-lived (30 min) and stateless.
    Refresh tokens are stored in Valkey for revocation capability.
    """

    def __init__(self, secret: str, valkey: Valkey):
        """Initialize session manager.

        Args:
            secret: JWT signing secret
            valkey: Async Valkey client for refresh token storage
        """
        self.secret = secret
        self.algorithm = "HS256"
        self.valkey = valkey
        self.access_expire = timedelta(minutes=30)
        self.refresh_expire = timedelta(days=7)

    async def create_tokens(self, user_id: int) -> dict:
        """Create access + refresh token pair.

        Args:
            user_id: User ID to encode in tokens

        Returns:
            Dict with access_token and refresh_token
        """
        now = datetime.now(timezone.utc)

        access_token = jwt.encode(
            {"sub": str(user_id), "exp": now + self.access_expire, "type": "access"},
            self.secret,
            algorithm=self.algorithm,
        )

        refresh_token = jwt.encode(
            {"sub": str(user_id), "exp": now + self.refresh_expire, "type": "refresh"},
            self.secret,
            algorithm=self.algorithm,
        )

        # Store refresh token in Valkey for revocation capability
        # Key format: refresh:{user_id}:{token_prefix}
        await self.valkey.setex(
            f"refresh:{user_id}:{refresh_token[:8]}",
            int(self.refresh_expire.total_seconds()),
            refresh_token,
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    def verify_access_token(self, token: str) -> dict | None:
        """Verify access token and return payload.

        Args:
            token: JWT access token

        Returns:
            Token payload dict or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") != "access":
                return None
            return payload
        except jwt.InvalidTokenError:
            return None

    async def refresh_access_token(self, refresh_token: str) -> str | None:
        """Verify refresh token and issue new access token.

        Args:
            refresh_token: JWT refresh token

        Returns:
            New access token or None if refresh token invalid
        """
        try:
            payload = jwt.decode(
                refresh_token, self.secret, algorithms=[self.algorithm]
            )
            if payload.get("type") != "refresh":
                return None

            user_id = payload["sub"]

            # Check if refresh token is still valid in Valkey
            stored = await self.valkey.get(f"refresh:{user_id}:{refresh_token[:8]}")
            if not stored:
                return None

            # Issue new access token
            now = datetime.now(timezone.utc)
            return jwt.encode(
                {"sub": user_id, "exp": now + self.access_expire, "type": "access"},
                self.secret,
                algorithm=self.algorithm,
            )
        except jwt.InvalidTokenError:
            return None

    async def revoke_refresh_token(self, user_id: int, refresh_token: str) -> None:
        """Revoke a refresh token.

        Args:
            user_id: User ID
            refresh_token: Refresh token to revoke
        """
        await self.valkey.delete(f"refresh:{user_id}:{refresh_token[:8]}")

    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user.

        Args:
            user_id: User ID to revoke all tokens for

        Returns:
            Number of tokens revoked
        """
        pattern = f"refresh:{user_id}:*"
        keys = []
        async for key in self.valkey.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            await self.valkey.delete(*keys)

        return len(keys)
