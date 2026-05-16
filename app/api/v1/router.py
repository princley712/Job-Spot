# app/api/v1/router.py
"""Central API v1 router — aggregates all sub-routers."""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.applications import router as applications_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.redirects import router as redirects_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(applications_router)
api_router.include_router(jobs_router)
api_router.include_router(resumes_router)
api_router.include_router(redirects_router)
