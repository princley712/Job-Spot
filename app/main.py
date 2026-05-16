# app/main.py
"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router

app = FastAPI(
    title="Job Aggregator",
    description="Automated job scraping, matching, and application tracking",
    version="0.1.0",
)

# ── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ───────────────────────────────────────────
app.include_router(api_router)

# ── Static files & templates ─────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False)
async def dashboard_page(request: Request):
    """Serve the main dashboard SPA shell."""
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
