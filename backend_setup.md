# 🛠 Backend Setup Guide

This guide will walk you through setting up the Job Aggregator backend from scratch on your local machine.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.10+**
- **PostgreSQL** (Running and accessible)
- **Redis** (Used for the Celery task queue)
- **Git**

---

## 🚀 Step-by-Step Installation

### 1. Create a Virtual Environment
It is highly recommended to use a virtual environment to keep dependencies isolated.

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
Install the project in editable mode along with all necessary libraries.

```bash
pip install -e .
```

### 3. Install Playwright Browsers
The scraping engine uses Playwright to navigate job boards.

```bash
playwright install chromium
```

### 4. Configure Environment Variables
Copy the template file and update it with your local credentials.

```bash
cp .env.example .env
```

**Edit the `.env` file:**
- Set `DATABASE_URL` (e.g., `postgresql://postgres:password@localhost:5432/job_db`)
- Set `REDIS_URL` (e.g., `redis://localhost:6379/0`)
- Set a `SECRET_KEY` for JWT authentication.

### 5. Initialize the Database
Run the migrations to create the tables and seed the skill dictionary for the matching engine.

```bash
# Run migrations
alembic upgrade head

# Seed skills (critical for the matching engine)
python -m scripts.seed_skills
```

---

## 🏃 Running the Platform

To run the full system, you need to open **three separate terminal windows**:

### Terminal 1: The API Server
This handles all frontend requests and serves the dashboard data.

```bash
uvicorn app.main:app --reload
```

### Terminal 2: Celery Worker
This handles background tasks like scraping and matching.

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

### Terminal 3: Celery Beat (Scheduler)
This schedules recurring tasks like the hourly "Janitor" clean-up.

```bash
celery -A app.workers.celery_app beat --loglevel=info
```

---

## 🔍 Troubleshooting

- **Database Errors**: Ensure PostgreSQL is running and the database name in your `DATABASE_URL` exists.
- **Redis Connection**: If Celery fails to start, check if your Redis server is active (`redis-cli ping` should return `PONG`).
- **Scraping Blocked**: If LinkedIn/Indeed scraping fails, you might need to provide a session cookie or run in headful mode for debugging.

---

## 🛠 Useful Commands

- **Manual Scrape**: Trigger a scrape for a specific user to test the matching engine.
  ```bash
  python -m scripts.manual_scrape linkedin --match-user <USER_UUID>
  ```
- **Check Migrations**: See the current database version.
  ```bash
  alembic current
  ```
