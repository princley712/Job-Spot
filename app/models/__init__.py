# app/models/__init__.py
"""
Import every model so SQLAlchemy's registry (and Alembic's autogenerate)
can discover all tables in one place.
"""
from app.models.user import User                                   # noqa: F401
from app.models.resume import Resume, Skill, ResumeSkill            # noqa: F401
from app.models.job import Job, JobSkill, JobMatch                  # noqa: F401
from app.models.application import (                                # noqa: F401
    Application,
    ApplicationEvent,
    RedirectLog,
)
from app.models.enums import (                                      # noqa: F401
    ApplicationStatus,
    JobSource,
    EmploymentType,
)
