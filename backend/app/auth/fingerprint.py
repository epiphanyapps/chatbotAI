"""Device fingerprint service for trial abuse prevention."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User


async def check_trial_abuse(fingerprint: str, db: AsyncSession) -> bool:
    """
    Check if fingerprint has already used a trial.
    Returns True if abuse detected (trial already used on this device).

    Note: Fingerprints can be spoofed. This is ONE signal, not sole source.
    Combine with rate limiting and monitoring for better protection.
    """
    if not fingerprint:
        return False

    result = await db.execute(
        select(User).where(
            User.device_fingerprint == fingerprint,
            User.trial_used == True
        )
    )
    return result.scalar_one_or_none() is not None


async def store_fingerprint(user_id: int, fingerprint: str, db: AsyncSession) -> None:
    """
    Store or update fingerprint for a user.
    Only updates if user doesn't have a fingerprint yet.
    """
    if not fingerprint:
        return

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user and not user.device_fingerprint:
        user.device_fingerprint = fingerprint
        await db.commit()


async def mark_trial_used(user_id: int, db: AsyncSession) -> None:
    """Mark that user has used their trial."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user:
        user.trial_used = True
        from datetime import datetime
        user.trial_started_at = datetime.utcnow()
        await db.commit()
