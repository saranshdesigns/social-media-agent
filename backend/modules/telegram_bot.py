"""
Telegram Bot — Command interface for the Social Media Automation Agent.

Commands:
  /start   — show available commands
  /status  — stats (paused/active, total posted, today, next run)
  /latest  — post the newest unposted image RIGHT NOW
  /trigger — manually run today's posting job (daily limit applies)
  /bulk    — post ALL unposted images (no daily limit)
  /pause   — pause automation
  /resume  — resume automation
  /logs    — last 5 activity log entries

Runs in a background daemon thread with its own event loop.
"""
import threading
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import database
from config import get_settings
from scheduler import run_posting_job, run_bulk_job, run_latest_job

settings = get_settings()

HELP_TEXT = (
    "📱 <b>Social Media Agent</b>\n\n"
    "/status  — Current stats\n"
    "/latest  — Post newest image right now\n"
    "/trigger — Post now (daily limit applies)\n"
    "/bulk    — Upload ALL unposted images (mixed categories)\n"
    "/pause   — Pause automation\n"
    "/resume  — Resume automation\n"
    "/logs    — Last 5 activity logs"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = database.get_posted_history(limit=1000)
    today = datetime.utcnow().date().isoformat()
    posted_today = [h for h in history if h["posted_at"].startswith(today)]

    paused = database.get_setting("automation_paused") == "true"
    last_run = database.get_setting("last_run_at") or "Never"
    next_run = database.get_setting("next_run_at") or "—"

    status_icon = "⏸" if paused else "▶️"
    state_text = "PAUSED" if paused else "ACTIVE"

    def fmt(dt_str: str) -> str:
        if dt_str in ("Never", "—"):
            return dt_str
        return dt_str[:16] + " UTC"

    text = (
        f"{status_icon} <b>Automation {state_text}</b>\n\n"
        f"📸 Total posted: <b>{len(history)}</b>\n"
        f"📅 Posted today: <b>{len(posted_today)}</b> / {settings.max_posts_per_day}\n"
        f"🕐 Last run: {fmt(last_run)}\n"
        f"⏰ Next run: {fmt(next_run)}\n"
        f"📋 Schedule: {settings.schedule_hour:02d}:{settings.schedule_minute:02d} UTC daily"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆕 Posting the latest unposted image now..."
    )
    threading.Thread(target=run_latest_job, daemon=True).start()


async def cmd_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Posting job started — check /logs in a few minutes for results."
    )
    threading.Thread(target=run_posting_job, daemon=True).start()


async def cmd_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📦 Bulk upload started — posting ALL unposted images.\n"
        "This may take a while depending on how many images there are."
    )
    threading.Thread(target=run_bulk_job, daemon=True).start()


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.set_setting("automation_paused", "true")
    await update.message.reply_text(
        "⏸ Automation <b>PAUSED</b>.\nSend /resume to restart.", parse_mode="HTML"
    )


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.set_setting("automation_paused", "false")
    await update.message.reply_text(
        "▶️ Automation <b>RESUMED</b>.\nNext post at scheduled time.", parse_mode="HTML"
    )


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logs = database.get_recent_logs(limit=8)
    if not logs:
        await update.message.reply_text("No activity logs yet.")
        return

    lines = []
    for log in logs:
        icon = "✅" if log["status"] == "success" else "❌"
        platform = log["platform"].capitalize()
        time_str = log["logged_at"][:16]
        response = (log["response"] or "ok")[:80]
        lines.append(f"{icon} <b>{platform}</b> — {time_str}\n  <i>{response}</i>")

    await update.message.reply_text("\n\n".join(lines), parse_mode="HTML")


def start_telegram_bot() -> None:
    """Start the Telegram bot in a background daemon thread."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print("[Telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — bot disabled.")
        return

    def _run():
        app = Application.builder().token(settings.telegram_bot_token).build()
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_start))
        app.add_handler(CommandHandler("status", cmd_status))
        app.add_handler(CommandHandler("latest", cmd_latest))
        app.add_handler(CommandHandler("trigger", cmd_trigger))
        app.add_handler(CommandHandler("bulk", cmd_bulk))
        app.add_handler(CommandHandler("pause", cmd_pause))
        app.add_handler(CommandHandler("resume", cmd_resume))
        app.add_handler(CommandHandler("logs", cmd_logs))
        print("[Telegram] Bot polling started.")
        app.run_polling(stop_signals=None)

    threading.Thread(target=_run, daemon=True, name="telegram-bot").start()
