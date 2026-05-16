# app/parsers/resume_parser.py
"""
Resume text extraction and basic NER-based skill/entity parsing.

Supports:
  - PDF via PyPDF2
  - Plain text (.txt)

For skill extraction, uses regex + keyword matching against common tech terms.
Optionally uses spaCy NER if the model is installed.
"""
from __future__ import annotations

import io
import re
import logging

logger = logging.getLogger(__name__)

# ── Common tech skills for keyword matching ───────────────────────────────────

TECH_SKILLS = {
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "sql",
    "fastapi", "django", "flask", "react", "angular", "vue", "next.js",
    "node.js", "express", ".net", "spring boot", "rails", "laravel",
    "celery", "sqlalchemy", "pandas", "numpy", "scikit-learn", "tensorflow",
    "pytorch", "spark", "machine learning", "deep learning",
    "natural language processing", "computer vision",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible",
    "jenkins", "github actions", "ci/cd", "linux", "nginx", "git",
    "rest api", "graphql", "microservices", "agile", "scrum",
    "html", "css", "sass", "webpack", "playwright", "selenium",
    "rabbitmq", "kafka", "grpc", "websocket",
}

# ── Year-of-experience extraction regex ───────────────────────────────────────

_YEARS_RE = re.compile(
    r"(\d{1,2})\+?\s*(?:years?|yrs?)[\s\w]*(?:experience|exp\.?)",
    re.IGNORECASE,
)


def _extract_text_from_pdf(raw_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception:
        logger.exception("PDF text extraction failed")
        return ""


def _extract_skills(text: str) -> list[str]:
    """Match known tech skills against the resume text."""
    lower = text.lower()
    found = []

    # Check multi-word skills first (longest match)
    for skill in sorted(TECH_SKILLS, key=len, reverse=True):
        if skill in lower:
            found.append(skill)

    return sorted(set(found))


def _extract_years_experience(text: str) -> int | None:
    """Pull the first mention of 'N years experience' from the text."""
    match = _YEARS_RE.search(text)
    if match:
        return int(match.group(1))
    return None


def _extract_entities_spacy(text: str) -> dict:
    """
    Optional spaCy NER extraction.
    Returns name, email, phone if detectable.
    Falls back gracefully if spaCy is not installed.
    """
    entities: dict = {}
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text[:5000])  # limit for performance

        for ent in doc.ents:
            if ent.label_ == "PERSON" and "name" not in entities:
                entities["name"] = ent.text
            if ent.label_ == "ORG" and "organizations" not in entities:
                entities.setdefault("organizations", []).append(ent.text)
    except (ImportError, OSError):
        logger.debug("spaCy not available — skipping NER")

    # Regex fallback for email and phone
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    if email_match:
        entities["email"] = email_match.group()

    phone_match = re.search(r"[\+]?[\d\s\-\(\)]{10,15}", text)
    if phone_match:
        entities["phone"] = phone_match.group().strip()

    return entities


# ── Public API ────────────────────────────────────────────────────────────────

def parse_resume_text(raw_bytes: bytes, content_type: str) -> dict:
    """
    Parse a resume file and return structured data.

    Returns:
        {
            "text": "full extracted text...",
            "data": {
                "skills": ["python", "fastapi", ...],
                "name": "...",
                "email": "...",
                ...
            },
            "years_experience": 5
        }
    """
    # 1. Extract raw text
    if "pdf" in content_type:
        text = _extract_text_from_pdf(raw_bytes)
    else:
        text = raw_bytes.decode("utf-8", errors="replace")

    if not text.strip():
        return {"text": "", "data": {"skills": []}, "years_experience": None}

    # 2. Extract structured data
    skills = _extract_skills(text)
    years = _extract_years_experience(text)
    entities = _extract_entities_spacy(text)

    data = {
        "skills": skills,
        **entities,
    }

    logger.info(
        "Parsed resume: %d chars, %d skills, %s years exp",
        len(text), len(skills), years or "?"
    )

    return {
        "text": text,
        "data": data,
        "years_experience": years,
    }
