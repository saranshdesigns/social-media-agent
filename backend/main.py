"""
Social Media Automation Agent — FastAPI Backend
Entry point: starts the API server and the background scheduler.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import database
from config import get_settings
from scheduler import start_scheduler
from api.routes import dashboard
from modules.telegram_bot import start_telegram_bot

settings = get_settings()

TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp"))

_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, create temp dir, write credentials if needed, start scheduler."""
    global _scheduler

    # Write credentials.json from env var if not present (Railway deployment)
    if settings.google_credentials_json and not os.path.exists(settings.google_credentials_path):
        with open(settings.google_credentials_path, "w") as f:
            f.write(settings.google_credentials_json)
        print("[Startup] credentials.json written from GOOGLE_CREDENTIALS_JSON env var.")

    os.makedirs(TEMP_DIR, exist_ok=True)
    database.init_db()
    _scheduler = start_scheduler()
    start_telegram_bot()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


# Build CORS origins list
_cors_origins = ["http://localhost:3000"]
if settings.frontend_url:
    _cors_origins.append(settings.frontend_url)

app = FastAPI(
    title="Social Media Automation Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve temp images publicly — used by Instagram/Facebook APIs
app.mount("/temp", StaticFiles(directory=TEMP_DIR), name="temp")

# Register route modules
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "Social Media Automation Agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
