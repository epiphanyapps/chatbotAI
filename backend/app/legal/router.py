"""Legal compliance endpoints for IntimateAI."""

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.audit import AgeVerificationAudit

router = APIRouter(prefix="/legal", tags=["legal"])

# The exact text users must agree to - stored in audit for legal compliance
AGE_CONFIRMATION_TEXT = (
    "I confirm that I am at least 18 years old and legally permitted "
    "to access adult content in my jurisdiction. I understand this site "
    "contains explicit material intended for adults only."
)


class AgeVerifyRequest(BaseModel):
    """Request body for age verification."""

    confirmed: bool
    fingerprint: str | None = None


class AgeVerifyResponse(BaseModel):
    """Response for age verification."""

    age_verified: bool
    message: str


@router.post("/age-verify")
async def verify_age(
    body: AgeVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AgeVerifyResponse:
    """
    Verify user is 18+ and create audit trail.

    This endpoint:
    1. Records full audit log (IP, user agent, fingerprint, timestamp)
    2. Stores exact confirmation text user agreed to
    3. Updates user.age_verified flag

    LEGAL REQUIREMENT: Audit log must be retained for compliance.
    """
    if user.age_verified:
        return AgeVerifyResponse(age_verified=True, message="Age already verified")

    if not body.confirmed:
        # Log rejection too - shows they saw the gate
        audit = AgeVerificationAudit(
            user_id=user.id,
            email=user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")[:512],
            device_fingerprint=body.fingerprint,
            confirmed_18_plus=False,
            confirmation_text=AGE_CONFIRMATION_TEXT,
        )
        db.add(audit)
        await db.commit()

        raise HTTPException(
            status_code=403, detail="You must be 18 or older to access this service"
        )

    # Create audit log for confirmation
    audit = AgeVerificationAudit(
        user_id=user.id,
        email=user.email,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")[:512],
        device_fingerprint=body.fingerprint,
        confirmed_18_plus=True,
        confirmation_text=AGE_CONFIRMATION_TEXT,
    )
    db.add(audit)

    # Update user record
    user.age_verified = True
    if body.fingerprint and not user.device_fingerprint:
        user.device_fingerprint = body.fingerprint

    await db.commit()

    return AgeVerifyResponse(age_verified=True, message="Age verified successfully")


@router.get("/age-confirmation-text")
async def get_age_confirmation_text():
    """
    Get the current age confirmation text.
    Frontend displays this to user before they confirm.
    """
    return {"text": AGE_CONFIRMATION_TEXT}


@router.get("/age-status")
async def get_age_status(user: User = Depends(get_current_user)):
    """Check if current user has verified their age."""
    return {"age_verified": user.age_verified}
