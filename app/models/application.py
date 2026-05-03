# app/models/application.py
from typing import List
from datetime import datetime, timedelta, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, Index, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
from app.models.enums import ApplicationStatus
import uuid

def default_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=7)

class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),
        Index("ix_applications_status_expires", "status", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))

    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus), default=ApplicationStatus.PENDING, index=True
    )

    # 7-day expiration: only enforced while status in (PENDING, NOT_APPLIED)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=default_expires_at, index=True
    )

    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_redirect_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="applications")
    job: Mapped["Job"] = relationship()
    events: Mapped[List["ApplicationEvent"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationEvent.occurred_at"
    )


class ApplicationEvent(Base):
    """Immutable timeline. One row per status change or note."""
    __tablename__ = "application_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )

    from_status: Mapped[ApplicationStatus | None] = mapped_column(SAEnum(ApplicationStatus))
    to_status: Mapped[ApplicationStatus] = mapped_column(SAEnum(ApplicationStatus))
    note: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    # e.g. {"interview_round": 2, "interviewer": "...", "source": "user"|"system"}

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["Application"] = relationship(back_populates="events")


class RedirectLog(Base):
    """Tracks every external 'Apply' click — useful for analytics & confirming the user actually went through."""
    __tablename__ = "redirect_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    target_url: Mapped[str] = mapped_column(String(1000))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
