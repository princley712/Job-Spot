# app/models/enums.py
import enum

class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"          # Matched, not yet acted on
    NOT_APPLIED = "not_applied"  # User explicitly skipped
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"          # Auto-set by janitor after 7 days

class JobSource(str, enum.Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WELLFOUND = "wellfound"
    OTHER = "other"

class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
