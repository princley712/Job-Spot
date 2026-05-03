# app/models/job.py
from typing import List
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, UniqueConstraint, Index, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
from app.models.enums import JobSource, EmploymentType
import uuid

class Job(Base, TimestampMixin):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),
        Index("ix_jobs_posted_at", "posted_at"),
        Index("ix_jobs_company_title", "company", "title"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Source identification (dedup key)
    source: Mapped[JobSource] = mapped_column(SAEnum(JobSource), index=True)
    external_id: Mapped[str] = mapped_column(String(255))      # board's own job id
    apply_url: Mapped[str] = mapped_column(String(1000))       # external redirect target
    canonical_url: Mapped[str] = mapped_column(String(1000))   # for display
    content_hash: Mapped[str] = mapped_column(String(64), index=True)  # sha256 of normalized title+company+desc

    # Metadata
    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    is_remote: Mapped[bool] = mapped_column(default=False, index=True)
    employment_type: Mapped[EmploymentType | None] = mapped_column(SAEnum(EmploymentType))

    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str | None] = mapped_column(String(3), default="USD")

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)  # preserve original scrape

    skills: Mapped[List["JobSkill"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    matches: Mapped[List["JobMatch"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    is_required: Mapped[bool] = mapped_column(default=True)

    job: Mapped["Job"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship()


class JobMatch(Base, TimestampMixin):
    """Per-user match score. Separating this from Job lets multiple users share a job row."""
    __tablename__ = "job_matches"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_job_matches_user_job"),
        Index("ix_job_matches_user_score", "user_id", "match_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))

    match_score: Mapped[float] = mapped_column(Float)              # 0.0 – 1.0
    skill_overlap: Mapped[dict] = mapped_column(JSONB, default=dict)
    # {"matched": ["python","fastapi"], "missing": ["kubernetes"]}

    job: Mapped["Job"] = relationship(back_populates="matches")
