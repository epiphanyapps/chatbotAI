"""Auth API endpoints for magic link authentication."""

import hashlib
from fastapi import APIRouter, HTTPException, Request, Depends, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import resend

from app.core.database import get_db
from app.core.valkey import get_valkey
from app.core.config import get_settings
from app.auth.magic_link import MagicLinkService
from app.auth.email_validator import is_disposable_email
from app.auth.jwt_handler import SessionManager
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class MagicLinkRequest(BaseModel):
    """Request body for magic link email."""

    email: EmailStr
    fingerprint: str | None = None


class TokenResponse(BaseModel):
    """Response containing access token."""

    access_token: str


@router.post("/magic-link")
async def request_magic_link(
    body: MagicLinkRequest,
    db: AsyncSession = Depends(get_db),
    valkey=Depends(get_valkey),
):
    """Request a magic link email.

    - Blocks disposable emails (AUTH-04)
    - Rate limits: max 3 requests per email per hour
    - Checks fingerprint for trial abuse if new user
    """
    settings = get_settings()

    # 1. Check disposable email
    if is_disposable_email(body.email):
        raise HTTPException(
            status_code=400, detail="Please use a non-disposable email address"
        )

    # 2. Check if user exists
    result = await db.execute(select(User).where(User.email == body.email))
    existing_user = result.scalar_one_or_none()

    # 3. If new user, check fingerprint for trial abuse
    if not existing_user and body.fingerprint:
        abuse_result = await db.execute(
            select(User).where(
                User.device_fingerprint == body.fingerprint, User.trial_used == True
            )
        )
        if abuse_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Trial already used on this device")

    # 4. Rate limit: max 3 requests per email per hour
    rate_key = f"magic_link_rate:{body.email}"
    count = await valkey.incr(rate_key)
    if count == 1:
        await valkey.expire(rate_key, 3600)
    if count > 3:
        raise HTTPException(
            status_code=429, detail="Too many requests. Please try again later."
        )

    # 5. Generate token and send email
    magic_link_service = MagicLinkService(settings.MAGIC_LINK_SECRET)
    token = magic_link_service.create_token(body.email)
    magic_url = f"{settings.APP_URL}/verify?token={token}"

    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send(
        {
            "from": "IntimateAI <noreply@intimateai.chat>",
            "to": [body.email],
            "subject": "Your login link",
            "html": f"""
                <p>Click to sign in to IntimateAI:</p>
                <a href="{magic_url}">Sign in to IntimateAI</a>
                <p>This link expires in 15 minutes.</p>
                <p>If you didn't request this, you can safely ignore this email.</p>
            """,
        }
    )

    return {"message": "Check your email for the login link"}


@router.get("/verify")
async def verify_magic_link(
    token: str,
    fingerprint: str | None = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db),
    valkey=Depends(get_valkey),
):
    """Verify magic link token and create session.

    - Prevents token replay (one-time use)
    - Creates or gets user
    - Issues JWT tokens
    - Sets refresh token as httpOnly cookie
    """
    settings = get_settings()

    # 1. Atomically consume token (prevent replay)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    was_new = await valkey.setnx(f"used_token:{token_hash}", "1")
    if not was_new:
        raise HTTPException(status_code=400, detail="Link already used")
    await valkey.expire(f"used_token:{token_hash}", 900)  # 15 min cleanup

    # 2. Verify token signature and expiry
    magic_link_service = MagicLinkService(settings.MAGIC_LINK_SECRET)
    payload = magic_link_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired link")

    email = payload["email"]

    # 3. Get or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            device_fingerprint=fingerprint,
            email_verified=True,  # Verified by clicking magic link
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Existing user - mark email as verified
        user.email_verified = True
        if fingerprint and not user.device_fingerprint:
            user.device_fingerprint = fingerprint
        await db.commit()

    # 4. Create session tokens
    session_manager = SessionManager(settings.JWT_SECRET, valkey)
    tokens = await session_manager.create_tokens(user.id)

    # 5. Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return TokenResponse(access_token=tokens["access_token"])


@router.post("/refresh")
async def refresh_token(request: Request, valkey=Depends(get_valkey)):
    """Refresh access token using httpOnly cookie."""
    settings = get_settings()
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    session_manager = SessionManager(settings.JWT_SECRET, valkey)
    new_access_token = await session_manager.refresh_access_token(refresh_token)

    if not new_access_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    return TokenResponse(access_token=new_access_token)


@router.post("/logout")
async def logout(
    request: Request, response: Response, valkey=Depends(get_valkey)
):
    """Revoke refresh token and clear cookie."""
    settings = get_settings()
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        try:
            import jwt

            payload = jwt.decode(
                refresh_token, settings.JWT_SECRET, algorithms=["HS256"]
            )
            user_id = payload["sub"]
            session_manager = SessionManager(settings.JWT_SECRET, valkey)
            await session_manager.revoke_refresh_token(int(user_id), refresh_token)
        except Exception:
            pass  # Token was invalid anyway

    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}
