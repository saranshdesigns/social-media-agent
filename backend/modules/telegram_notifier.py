"""
Telegram Notifier — Sends one-way notifications to the configured chat.
Uses raw requests (no library) — never blocks the posting job.
"""
import requests
from config import get_settings


def notify(text: str) -> None:
    """Send a message to the Telegram chat. Silently ignores errors."""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
    except Exception:
        pass  # Never let Telegram errors affect the posting job
