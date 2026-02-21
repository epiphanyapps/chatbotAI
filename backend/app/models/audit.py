"""Audit models for compliance and legal requirements."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgeVerificationAudit(Base):
    """Audit log for age verification confirmations.

    Captures full compliance data for legal requirements.
    """

    __tablename__ = "age_verification_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=False
    )  # IPv6 max length
    user_agent: Mapped[str] = mapped_column(String(512), nullable=False)
    device_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confirmed_18_plus: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confirmation_text: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AgeVerificationAudit(id={self.id}, user_id={self.user_id}, confirmed={self.confirmed_18_plus})>"
