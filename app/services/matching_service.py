# app/services/matching_service.py
"""
Resume ↔ Job matching engine.

Strategy (layered, highest-signal first):
  1. **Skill overlap** — exact set intersection of canonical skill names.
  2. **TF-IDF cosine similarity** — compares full resume text vs. job description.
  3. **Final score** = weighted blend: 0.55 × skill_score + 0.45 × tfidf_score

The matcher is intentionally dependency-light (scikit-learn only, no GPU).
Swap in sentence-transformers or OpenAI embeddings later by subclassing.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── DTOs ──────────────────────────────────────────────────────────────────────

@dataclass
class MatchResult:
    job_id: str
    score: float                         # 0.0 – 1.0
    tfidf_score: float
    skill_score: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)


# ── Text pre-processing ──────────────────────────────────────────────────────

_CLEAN_RE = re.compile(r"[^a-z0-9\s+#.]")

def _normalise(text: str) -> str:
    """Lowercase, strip non-alpha (keep #, +, . for 'C#', 'C++', '.NET')."""
    return _CLEAN_RE.sub(" ", text.lower()).strip()


def extract_skills_from_text(text: str, known_skills: set[str]) -> set[str]:
    """
    Simple keyword-match skill extractor.
    Matches multi-word skills (e.g. "machine learning") by checking bigrams too.
    """
    norm = _normalise(text)
    tokens = set(norm.split())

    # Build bigrams for multi-word skills
    words = norm.split()
    bigrams = {f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)}
    trigrams = {f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words) - 2)}

    candidates = tokens | bigrams | trigrams
    return candidates & known_skills


# ── Core Matcher ──────────────────────────────────────────────────────────────

class MatchingEngine:
    """
    Stateless matcher.  Instantiate once, call `score_jobs()` per resume.

    Parameters
    ----------
    known_skills : set[str]
        Canonical skill names from the `skills` table (lowercased).
    skill_weight : float
        Blend weight for the skill-overlap component (default 0.55).
    """

    def __init__(
        self,
        known_skills: set[str] | None = None,
        skill_weight: float = 0.55,
    ):
        self._known_skills = {s.lower() for s in (known_skills or set())}
        self._skill_w = skill_weight
        self._tfidf_w = 1.0 - skill_weight
        self._vectorizer = TfidfVectorizer(
            max_features=settings.TFIDF_MAX_FEATURES,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

    # ── Public API ────────────────────────────────────────────

    def score_jobs(
        self,
        resume_text: str,
        jobs: list[dict],
        threshold: float | None = None,
    ) -> list[MatchResult]:
        """
        Score a list of jobs against a single resume.

        Parameters
        ----------
        resume_text : str
            Full extracted resume text.
        jobs : list[dict]
            Each dict must have at minimum: 'id', 'title', 'description'.
            Optionally 'requirements'.
        threshold : float
            Minimum score to include in results (default from config).

        Returns
        -------
        list[MatchResult]
            Sorted descending by score.
        """
        threshold = threshold if threshold is not None else settings.MATCH_SCORE_THRESHOLD

        if not jobs:
            return []

        # ── 1. Build corpus for TF-IDF ────────────────────────
        resume_norm = _normalise(resume_text)
        job_texts = []
        for j in jobs:
            blob = f"{j.get('title', '')} {j.get('description', '')} {j.get('requirements', '') or ''}"
            job_texts.append(_normalise(blob))

        corpus = [resume_norm] + job_texts  # index 0 = resume
        tfidf_matrix = self._vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        # ── 2. Skill overlap ──────────────────────────────────
        resume_skills = extract_skills_from_text(resume_text, self._known_skills)

        results: list[MatchResult] = []
        for idx, job in enumerate(jobs):
            job_blob = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '') or ''}"
            job_skills = extract_skills_from_text(job_blob, self._known_skills)

            matched = resume_skills & job_skills
            missing = job_skills - resume_skills

            skill_score = len(matched) / max(len(job_skills), 1)
            tfidf_score = float(similarities[idx])

            final = self._skill_w * skill_score + self._tfidf_w * tfidf_score
            final = round(min(max(final, 0.0), 1.0), 4)

            if final < threshold:
                continue

            results.append(MatchResult(
                job_id=str(job["id"]),
                score=final,
                tfidf_score=round(tfidf_score, 4),
                skill_score=round(skill_score, 4),
                matched_skills=sorted(matched),
                missing_skills=sorted(missing),
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        logger.info(
            "Matching complete: %d jobs scored, %d above threshold (%.2f)",
            len(jobs), len(results), threshold,
        )
        return results

    # ── Convenience: single-job score ─────────────────────────

    def score_single(self, resume_text: str, job: dict) -> MatchResult | None:
        """Score one job; returns None if below threshold."""
        matches = self.score_jobs(resume_text, [job])
        return matches[0] if matches else None
