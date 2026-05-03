# scripts/seed_skills.py
"""
Seed the `skills` table with a curated list of tech skills.
Run once after migrations:
    python -m scripts.seed_skills
"""
from app.db.session import SessionLocal
from app.models.resume import Skill

SKILLS: list[dict] = [
    # ── Languages ─────────────────────────────────────────
    {"name": "python",       "category": "language"},
    {"name": "javascript",   "category": "language"},
    {"name": "typescript",   "category": "language"},
    {"name": "java",         "category": "language"},
    {"name": "c++",          "category": "language"},
    {"name": "c#",           "category": "language"},
    {"name": "go",           "category": "language"},
    {"name": "rust",         "category": "language"},
    {"name": "ruby",         "category": "language"},
    {"name": "php",          "category": "language"},
    {"name": "swift",        "category": "language"},
    {"name": "kotlin",       "category": "language"},
    {"name": "scala",        "category": "language"},
    {"name": "r",            "category": "language"},
    {"name": "sql",          "category": "language"},

    # ── Frameworks / Libraries ────────────────────────────
    {"name": "fastapi",        "category": "framework"},
    {"name": "django",         "category": "framework"},
    {"name": "flask",          "category": "framework"},
    {"name": "react",          "category": "framework"},
    {"name": "next.js",        "category": "framework"},
    {"name": "angular",        "category": "framework"},
    {"name": "vue",            "category": "framework"},
    {"name": "spring boot",    "category": "framework"},
    {"name": "express",        "category": "framework"},
    {"name": "node.js",        "category": "framework"},
    {"name": ".net",           "category": "framework"},
    {"name": "rails",          "category": "framework"},
    {"name": "laravel",        "category": "framework"},
    {"name": "celery",         "category": "framework"},
    {"name": "sqlalchemy",     "category": "framework"},

    # ── Data / ML ─────────────────────────────────────────
    {"name": "pandas",           "category": "data"},
    {"name": "numpy",            "category": "data"},
    {"name": "scikit-learn",     "category": "data"},
    {"name": "tensorflow",       "category": "data"},
    {"name": "pytorch",          "category": "data"},
    {"name": "spark",            "category": "data"},
    {"name": "machine learning", "category": "data"},
    {"name": "deep learning",    "category": "data"},
    {"name": "natural language processing", "category": "data"},
    {"name": "computer vision",  "category": "data"},
    {"name": "data engineering", "category": "data"},

    # ── Databases ─────────────────────────────────────────
    {"name": "postgresql",   "category": "database"},
    {"name": "mysql",        "category": "database"},
    {"name": "mongodb",      "category": "database"},
    {"name": "redis",        "category": "database"},
    {"name": "elasticsearch","category": "database"},
    {"name": "dynamodb",     "category": "database"},
    {"name": "cassandra",    "category": "database"},
    {"name": "sqlite",       "category": "database"},

    # ── DevOps / Cloud ────────────────────────────────────
    {"name": "docker",       "category": "tool"},
    {"name": "kubernetes",   "category": "tool"},
    {"name": "aws",          "category": "tool"},
    {"name": "gcp",          "category": "tool"},
    {"name": "azure",        "category": "tool"},
    {"name": "terraform",    "category": "tool"},
    {"name": "ansible",      "category": "tool"},
    {"name": "jenkins",      "category": "tool"},
    {"name": "github actions","category": "tool"},
    {"name": "ci/cd",        "category": "tool"},
    {"name": "linux",        "category": "tool"},
    {"name": "nginx",        "category": "tool"},
    {"name": "grafana",      "category": "tool"},
    {"name": "prometheus",   "category": "tool"},

    # ── Practices / Concepts ──────────────────────────────
    {"name": "rest api",         "category": "concept"},
    {"name": "graphql",          "category": "concept"},
    {"name": "microservices",    "category": "concept"},
    {"name": "event driven",     "category": "concept"},
    {"name": "agile",            "category": "concept"},
    {"name": "scrum",            "category": "concept"},
    {"name": "git",              "category": "tool"},
    {"name": "unit testing",     "category": "concept"},
    {"name": "system design",    "category": "concept"},
]


def seed():
    with SessionLocal() as db:
        existing = {s.name for s in db.query(Skill).all()}
        added = 0
        for entry in SKILLS:
            if entry["name"] not in existing:
                db.add(Skill(name=entry["name"], category=entry["category"]))
                added += 1
        db.commit()
        print(f"Seeded {added} new skills ({len(existing)} already existed)")


if __name__ == "__main__":
    seed()
