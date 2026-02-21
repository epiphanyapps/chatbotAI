"""FastAPI authentication dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import SessionManager
from app.core.config import get_settings
from app.core.database import get_db
from app.core.valkey import get_valkey
from app.models.user import User

security = HTTPBearer()


async def get_session_manager(valkey=Depends(get_valkey)) -> SessionManager:
    """Dependency that provides SessionManager instance.

    Args:
        valkey: Valkey client from dependency

    Returns:
        Configured SessionManager
    """
    settings = get_settings()
    return SessionManager(settings.JWT_SECRET, valkey)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_manager: SessionManager = Depends(get_session_manager),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: Bearer token from Authorization header
        session_manager: JWT session manager
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: 401 if token invalid or user not found
    """
    token = credentials.credentials
    payload = session_manager.verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_verified_user(user: User = Depends(get_current_user)) -> User:
    """Require email verified user.

    Args:
        user: Current authenticated user

    Returns:
        User if email verified

    Raises:
        HTTPException: 403 if email not verified
    """
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    return user


async def get_age_verified_user(user: User = Depends(get_verified_user)) -> User:
    """Require age verified user (also requires email verification).

    Args:
        user: Current email-verified user

    Returns:
        User if age verified

    Raises:
        HTTPException: 403 if age not verified
    """
    if not user.age_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Age verification required",
        )
    return user
