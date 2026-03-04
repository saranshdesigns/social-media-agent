from fastapi import APIRouter
from datetime import datetime
import database
from config import get_settings
from scheduler import run_posting_job, run_bulk_job, run_latest_job
import threading

settings = get_settings()
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def get_overview():
    """Main dashboard stats."""
    history = database.get_posted_history(limit=1000)
    today = datetime.utcnow().date().isoformat()
    posted_today = [h for h in history if h["posted_at"].startswith(today)]

    return {
        "total_posted": len(history),
        "posted_today": len(posted_today),
        "automation_paused": database.get_setting("automation_paused") == "true",
        "last_run_at": database.get_setting("last_run_at"),
        "next_run_at": database.get_setting("next_run_at"),
        "schedule": f"{settings.schedule_hour:02d}:{settings.schedule_minute:02d} UTC",
        "max_posts_per_day": settings.max_posts_per_day,
    }


@router.post("/pause")
def pause_automation():
    database.set_setting("automation_paused", "true")
    return {"status": "paused"}


@router.post("/resume")
def resume_automation():
    database.set_setting("automation_paused", "false")
    return {"status": "resumed"}


@router.post("/trigger")
def manual_trigger():
    """Manually trigger the posting job (runs in background thread)."""
    thread = threading.Thread(target=run_posting_job, daemon=True)
    thread.start()
    return {"status": "triggered", "message": "Posting job started in background"}


@router.post("/trigger-bulk")
def bulk_trigger():
    """Bulk trigger — posts ALL unposted images, ignoring daily limit. Use for initial upload."""
    thread = threading.Thread(target=run_bulk_job, daemon=True)
    thread.start()
    return {"status": "triggered", "message": "Bulk job started — all unposted images will be posted"}


@router.post("/trigger-latest")
def latest_trigger():
    """Post Latest — posts ONLY the single newest unposted image, ignoring daily limit."""
    thread = threading.Thread(target=run_latest_job, daemon=True)
    thread.start()
    return {"status": "triggered", "message": "Posting the latest unposted image now"}


@router.get("/history")
def get_history(limit: int = 50):
    """List of all posted images."""
    return database.get_posted_history(limit=limit)


@router.get("/logs")
def get_logs(limit: int = 100):
    """Recent platform logs (success/error per post per platform)."""
    return database.get_recent_logs(limit=limit)


@router.get("/platforms")
def get_platform_status():
    """
    Check if each platform API credential is configured.
    Does not make live API calls — just checks if tokens are non-empty.
    """
    return {
        "instagram": bool(settings.instagram_account_id and settings.facebook_page_access_token),
        "facebook": bool(settings.facebook_page_id and settings.facebook_page_access_token),
        "google_drive": bool(settings.google_portfolio_folder_id),
        "openai": bool(settings.openai_api_key),
        "server_url": bool(settings.server_base_url),
    }


@router.get("/settings")
def get_settings_view():
    return {
        "schedule_hour": settings.schedule_hour,
        "schedule_minute": settings.schedule_minute,
        "post_interval_minutes": settings.post_interval_minutes,
        "max_posts_per_day": settings.max_posts_per_day,
        "openai_model": settings.openai_model,
    }
