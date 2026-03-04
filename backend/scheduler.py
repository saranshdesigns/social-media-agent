"""
Main Scheduler & Orchestrator
- Runs once per day at configured time
- Groups images by filename convention (e.g. 'Project 1.1', 'Project 1.2' → carousel)
- Single images post as normal; multi-slide groups post as carousel
- Bulk trigger mode: posts ALL unposted images ignoring daily limit
- Respects pause/resume toggle from admin dashboard
"""
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import database
from config import get_settings
from modules.drive_watcher import get_new_image_groups, get_latest_image_group
from modules.image_processor import process_image, cleanup_temp
from modules.caption_engine import generate_captions
from modules.poster import instagram, facebook
from modules.retry_handler import with_retry
from modules.telegram_notifier import notify

settings = get_settings()


def _process_group(group: dict, index: int, total: int):
    """
    Process and post a single image group (single image or carousel).
    Returns True if at least one platform succeeded.
    """
    group_key = group["group_key"]
    slides = group["slides"]
    folder_path = group["folder_path"]
    is_carousel = group["is_carousel"]
    label = f"CAROUSEL ({len(slides)} slides)" if is_carousel else "single image"

    print(f"\n[Scheduler] --- Post {index + 1}/{total}: '{group_key}' [{label}] ---")

    # ── 1. Process ALL slides ──────────────────────────────────
    processed_slides = []
    for slide in slides:
        try:
            p = process_image(slide["id"], slide["mime_type"], slide["name"])
            processed_slides.append(p)
        except Exception as e:
            print(f"[Scheduler] Processing failed for {slide['name']}: {e}")
            database.log_platform_result(slide["id"], "processor", "failed", str(e))
            # Skip entire group if any slide fails to process
            for already_processed in processed_slides:
                cleanup_temp(already_processed["temp_file_path"])
            return False

    public_urls = [p["public_url"] for p in processed_slides]
    temp_paths = [p["temp_file_path"] for p in processed_slides]
    first_raw_bytes = processed_slides[0]["raw_bytes"]
    primary_url = public_urls[0]

    # ── 2. Generate AI captions (using first slide for vision) ──
    try:
        captions = generate_captions(first_raw_bytes, slides[0]["name"])
    except Exception as e:
        print(f"[Scheduler] Caption generation failed: {e}")
        database.log_platform_result(slides[0]["id"], "caption_engine", "failed", str(e))
        fallback = f"New portfolio piece — {group_key} #packagingdesign #branding"
        captions = {"instagram": fallback, "facebook": fallback, "category": "design"}

    # ── 3. Post to all platforms ───────────────────────────────
    results = {}
    primary_file_id = slides[0]["id"]

    if is_carousel:
        results["instagram"] = with_retry(
            "instagram", primary_file_id,
            instagram.post_carousel,
            public_urls, captions["instagram"]
        )
        results["facebook"] = with_retry(
            "facebook", primary_file_id,
            facebook.post_album,
            public_urls, captions["facebook"]
        )
    else:
        results["instagram"] = with_retry(
            "instagram", primary_file_id,
            instagram.post_image,
            primary_url, captions["instagram"]
        )
        results["facebook"] = with_retry(
            "facebook", primary_file_id,
            facebook.post_image,
            primary_url, captions["facebook"]
        )

    platform_success = {p: r["success"] for p, r in results.items()}
    primary_caption = captions.get("instagram", captions.get("facebook", ""))

    # ── 4. Record EACH slide in DB ─────────────────────────────
    for slide, p in zip(slides, processed_slides):
        database.mark_as_posted(
            drive_file_id=slide["id"],
            file_name=slide["name"],
            folder_path=folder_path,
            caption=primary_caption,
            cloudinary_url=p["public_url"],
            platforms=platform_success,
        )

    # ── 5. Cleanup temp files ──────────────────────────────────
    for path in temp_paths:
        cleanup_temp(path)

    # ── 6. Summary ────────────────────────────────────────────
    any_success = any(r["success"] for r in results.values())
    for platform, result in results.items():
        status = "✓" if result["success"] else "✗"
        print(f"[Scheduler] {status} {platform}: {result.get('post_id') or result.get('error')}")

    # Telegram notification
    post_type = f"carousel ({len(slides)} slides)" if is_carousel else "image"
    if any_success:
        platforms_ok = [p for p, r in results.items() if r["success"]]
        notify(
            f"✅ <b>Posted:</b> {group_key}\n"
            f"Type: {post_type}\n"
            f"Platforms: {', '.join(platforms_ok)}"
        )
    else:
        errors = "; ".join(r.get("error", "unknown") or "unknown" for r in results.values())
        notify(
            f"❌ <b>Post failed:</b> {group_key}\n"
            f"Error: {errors[:200]}"
        )

    return any_success


def run_posting_job():
    """
    Daily scheduled job — posts up to MAX_POSTS_PER_DAY image groups.
    Respects pause flag and daily limit.
    """
    print(f"\n{'='*60}")
    print(f"[Scheduler] Daily job started at {datetime.utcnow().isoformat()} UTC")
    print(f"{'='*60}")

    if database.get_setting("automation_paused") == "true":
        print("[Scheduler] Automation is PAUSED. Skipping today's run.")
        return

    database.set_setting("last_run_at", datetime.utcnow().isoformat())

    groups = get_new_image_groups(limit=settings.max_posts_per_day)

    if not groups:
        print("[Scheduler] No new images found. Job complete.")
        notify("ℹ️ Daily job ran — no new images to post.")
        database.set_setting("next_run_at", _next_run_time())
        return

    notify(f"🕐 Daily posting job started — {len(groups)} post(s) queued.")
    print(f"[Scheduler] Processing {len(groups)} post(s)...")

    for index, group in enumerate(groups):
        _process_group(group, index, len(groups))

        if index < len(groups) - 1:
            gap = settings.post_interval_minutes * 60
            print(f"[Scheduler] Waiting {settings.post_interval_minutes} minutes before next post...")
            time.sleep(gap)

    print(f"\n[Scheduler] Daily job complete. Processed {len(groups)} post(s).")
    notify(f"✔️ Daily job complete — {len(groups)} post(s) processed.")
    database.set_setting("next_run_at", _next_run_time())


def run_bulk_job():
    """
    Bulk mode — posts ALL unposted image groups with NO daily limit.
    Use this for the initial upload of your entire portfolio.
    Automation pause flag is NOT checked — bulk always runs.
    """
    print(f"\n{'='*60}")
    print(f"[Scheduler] BULK job started at {datetime.utcnow().isoformat()} UTC")
    print(f"{'='*60}")

    database.set_setting("last_run_at", datetime.utcnow().isoformat())

    groups = get_new_image_groups(limit=None)  # No limit

    if not groups:
        print("[Scheduler] No new images found. Bulk job complete.")
        notify("ℹ️ Bulk job ran — no new images found.")
        return

    notify(f"📦 Bulk upload started — {len(groups)} post(s) to process.")
    print(f"[Scheduler] Bulk: processing {len(groups)} post(s)...")

    for index, group in enumerate(groups):
        _process_group(group, index, len(groups))

        if index < len(groups) - 1:
            gap = settings.post_interval_minutes * 60
            print(f"[Scheduler] Waiting {settings.post_interval_minutes} minutes before next post...")
            time.sleep(gap)

    print(f"\n[Scheduler] Bulk job complete. Processed {len(groups)} post(s).")
    notify(f"✔️ Bulk upload complete — {len(groups)} post(s) processed.")
    database.set_setting("next_run_at", _next_run_time())


def run_latest_job():
    """
    Post Latest — posts ONLY the single newest unposted image/carousel.
    Ignores daily limit and pause flag. On-demand use only.
    """
    print(f"\n{'='*60}")
    print(f"[Scheduler] LATEST job started at {datetime.utcnow().isoformat()} UTC")
    print(f"{'='*60}")

    group = get_latest_image_group()
    if not group:
        notify("ℹ️ No unposted images found — nothing to post.")
        return

    notify(f"🆕 Posting latest: <b>{group['group_key']}</b>")
    _process_group(group, 0, 1)
    print(f"\n[Scheduler] Latest job complete.")


def _next_run_time() -> str:
    """Calculate the next scheduled run time string."""
    now = datetime.utcnow()
    next_run = now.replace(
        hour=settings.schedule_hour,
        minute=settings.schedule_minute,
        second=0,
        microsecond=0,
    )
    if next_run <= now:
        next_run += timedelta(days=1)
    return next_run.isoformat()


def start_scheduler():
    """Initialize and start the APScheduler background scheduler."""
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_posting_job,
        trigger=CronTrigger(
            hour=settings.schedule_hour,
            minute=settings.schedule_minute,
            timezone="UTC",
        ),
        id="daily_posting_job",
        name="Daily Portfolio Poster",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    database.set_setting("next_run_at", _next_run_time())
    print(
        f"[Scheduler] Started. Runs daily at "
        f"{settings.schedule_hour:02d}:{settings.schedule_minute:02d} UTC"
    )
    return scheduler


if __name__ == "__main__":
    database.init_db()
    run_posting_job()
