# Job Aggregator Platform

A comprehensive job aggregation and matching platform built with FastAPI, Playwright, and Celery. This system automatically scrapes multiple job boards, scores them against user resumes using a hybrid TF-IDF and skill-overlap matching engine, and manages the application lifecycle.

## 🚀 Features

- **Automated Scraping**: Asynchronous scrapers for LinkedIn, Indeed, Greenhouse, and Lever using Playwright.
- **Intelligent Matching**: Hybrid matching engine combining TF-IDF cosine similarity (45%) and exact skill-set overlap (55%).
- **Lifecycle Management**: Auto-expires stale "Pending" applications after 7 days via a background janitor task.
- **Scalable Workers**: Distributed task processing using Celery and Redis.
- **Persistence**: Robust data modeling with PostgreSQL, SQLAlchemy, and Alembic migrations.
- **RESTful API**: FastAPI-powered backend with JWT authentication and Pydantic validation.

## 🛠 Tech Stack

- **Backend**: FastAPI, Python 3.10+
- **Database**: PostgreSQL, SQLAlchemy, Alembic
- **Task Queue**: Celery, Redis
- **Scraping**: Playwright (Headless Chromium)
- **Matching**: Scikit-learn (TF-IDF), Regex (Skill Extraction)
- **Settings**: Pydantic Settings (Environment-driven)

## 📁 Project Structure

```text
job-aggregator/
├── alembic/              # DB migrations
├── app/
│   ├── api/              # API routes (auth, jobs, resumes, etc.)
│   ├── core/             # Security and logging
│   ├── db/               # Database session and base models
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response models
│   ├── services/         # Business logic (matching, job persistence)
│   ├── scrapers/         # Playwright modules (LinkedIn, Indeed, etc.)
│   └── workers/          # Celery tasks (scrapers, matcher, janitor)
├── docker/               # Docker configuration
├── scripts/              # CLI tools (seeding, manual scraping)
├── .env.example          # Template for environment variables
└── pyproject.toml        # Dependencies and project metadata
```

## 🏁 Getting Started

### 1. Clone and Install
```bash
git clone <repo-url>
cd job-aggregator
pip install -e .
playwright install chromium
```

### 2. Configure Environment
Copy `.env.example` to `.env` and update your database and redis credentials.
```bash
cp .env.example .env
```

### 3. Database Setup
Run migrations and seed the canonical skills dictionary.
```bash
alembic upgrade head
python -m scripts.seed_skills
```

### 4. Run the Platform
You need three processes running for the full system:

**API Server:**
```bash
uvicorn app.main:app --reload
```

**Celery Worker:**
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

**Celery Beat (Scheduler):**
```bash
celery -A app.workers.celery_app beat --loglevel=info
```

## 🔍 Key Components

### Matching Engine
The engine uses a weighted blend of two scores:
1. **Skill Score (55%)**: Extracted from the `skills` table, matching uni/bi/trigrams in the resume vs. job description.
2. **Context Score (45%)**: TF-IDF cosine similarity between the full resume text and the job listing.

### The Janitor
The `janitor.expire_stale_applications` task runs hourly. It finds applications in `PENDING` or `NOT_APPLIED` status that are older than 7 days and marks them as `EXPIRED`, keeping the user's dashboard clean.

### Manual Scraping
Trigger a scrape manually for testing:
```bash
python -m scripts.manual_scrape linkedin --match-user <USER_UUID>
```

## 📄 License
MIT
