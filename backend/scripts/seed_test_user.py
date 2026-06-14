"""Seed an age-verified test user and print a JWT — for post-deploy smoke tests.

Bypasses the Resend email/magic-link flow so the chat can be exercised before
the public auth path (Resend + domain) is wired.

Run from `backend/` with the TARGET database's env set. The managed DB is on a
private VPC, so run this from inside the VPC (App Platform console/exec) or add
your IP to `allowed_admin_ips` and use the cluster's public connection URI.

    DATABASE_URL='postgresql://…?sslmode=require' \
    DATABASE_SSL_CA="$(doctl databases certificate get <pg-id> --format Certificate --no-header)" \
    JWT_SECRET='<the deployed JWT secret>' \
    VALKEY_URL='rediss://…' MAGIC_LINK_SECRET=x RESEND_API_KEY=x \
    python -m scripts.seed_test_user

Prints the user id and a 12-hour access token. Use it as a Bearer token against
`POST /api/chat/message` or inject into the web app's localStorage as
`access_token`.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, create_tables
from app.models.user import User

EMAIL = os.environ.get("SEED_EMAIL", "tester@intimateai.local")


async def main() -> None:
    await create_tables()  # no-op if the app already created the schema

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == EMAIL))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(email=EMAIL)
            db.add(user)
        user.email_verified = True
        user.age_verified = True
        user.is_active = True
        await db.commit()
        await db.refresh(user)
        user_id = user.id

    settings = get_settings()
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": str(user_id), "exp": now + timedelta(hours=12), "type": "access"},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    print(f"user_id: {user_id}")
    print(f"email:   {EMAIL}")
    print(f"ACCESS_TOKEN: {token}")


if __name__ == "__main__":
    asyncio.run(main())
