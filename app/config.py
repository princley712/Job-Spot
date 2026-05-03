# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/jobtracker"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis / Celery ────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # ── JWT / Auth ────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Scraper ───────────────────────────────────────────────
    SCRAPER_HEADLESS: bool = True
    SCRAPER_TIMEOUT_MS: int = 30_000
    SCRAPER_MAX_CONCURRENT: int = 3
    SCRAPER_REQUEST_DELAY_S: float = 2.0        # polite crawl delay
    SCRAPER_PROXY: str | None = None             # "http://user:pass@proxy:port"

    # ── Matching ──────────────────────────────────────────────
    MATCH_SCORE_THRESHOLD: float = 0.25          # ignore jobs below this
    TFIDF_MAX_FEATURES: int = 5000

    # ── Application Expiry ────────────────────────────────────
    APPLICATION_EXPIRY_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
