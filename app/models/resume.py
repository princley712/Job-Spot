# app/models/resume.py
from typing import List
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
import uuid

class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Storage
    file_url: Mapped[str] = mapped_column(String(500))   # S3/local path
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Parsed content
    raw_text: Mapped[str] = mapped_column(Text)
    parsed_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    # parsed_data shape:
    # {
    #   "name": "...", "email": "...", "phone": "...",
    #   "experience": [{"company": "...", "title": "...", "start": "...", "end": "...", "summary": "..."}],
    #   "education": [...], "certifications": [...], "summary": "..."
    # }

    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)  # use pgvector in prod
    years_experience: Mapped[int | None] = mapped_column(Integer)

    user: Mapped["User"] = relationship(back_populates="resumes")
    skills: Mapped[List["ResumeSkill"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class Skill(Base):
    """Canonical skill dictionary, shared across resumes & jobs."""
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(50))  # "language", "framework", "tool"


class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    proficiency: Mapped[int | None] = mapped_column(Integer)  # 1–5, optional
    years: Mapped[float | None] = mapped_column()

    resume: Mapped["Resume"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship()
