"""Magic link token generation and verification using itsdangerous."""

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


class MagicLinkService:
    """Service for creating and verifying magic link tokens.

    Uses itsdangerous URLSafeTimedSerializer for:
    - Cryptographic signing (tamper-proof)
    - Time-based expiration
    - URL-safe encoding
    """

    def __init__(self, secret_key: str):
        """Initialize with secret key.

        Args:
            secret_key: Secret for signing tokens
        """
        self.serializer = URLSafeTimedSerializer(secret_key)

    def create_token(self, email: str) -> str:
        """Create signed, time-limited token for magic link.

        Args:
            email: User's email address

        Returns:
            URL-safe signed token string
        """
        return self.serializer.dumps({"email": email, "purpose": "login"})

    def verify_token(self, token: str, max_age: int = 900) -> dict | None:
        """Verify token signature and expiry.

        Args:
            token: The token to verify
            max_age: Maximum age in seconds (default 900 = 15 minutes)

        Returns:
            Payload dict with email if valid, None if invalid/expired
        """
        try:
            return self.serializer.loads(token, max_age=max_age)
        except (SignatureExpired, BadSignature):
            return None
