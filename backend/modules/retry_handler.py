"""
Retry Handler
- Wraps any platform posting function
- Retries up to 3 times with exponential backoff on failure
- Logs each attempt to the database
"""
import time
import functools
from typing import Callable
import database


MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 10  # 10s → 20s → 40s


def with_retry(platform: str, drive_file_id: str, fn: Callable, *args, **kwargs) -> dict:
    """
    Execute a posting function with automatic retry on failure.

    Args:
        platform: name for logging ("instagram", "facebook", etc.)
        drive_file_id: used for DB logging
        fn: the posting function to call
        *args, **kwargs: passed directly to fn

    Returns:
        Final result dict from fn: {"success": bool, "post_id": ..., "error": ...}
    """
    last_result = {"success": False, "post_id": None, "error": "Not attempted"}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"[Retry] {platform} — attempt {attempt}/{MAX_ATTEMPTS}")
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            result = {"success": False, "post_id": None, "error": str(e)}

        database.log_platform_result(
            drive_file_id=drive_file_id,
            platform=platform,
            status="success" if result["success"] else "failed",
            response=result.get("error") or result.get("post_id") or "",
            attempt=attempt,
        )

        if result["success"]:
            return result

        last_result = result

        if attempt < MAX_ATTEMPTS:
            delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))  # exponential backoff
            print(f"[Retry] {platform} failed. Retrying in {delay}s...")
            time.sleep(delay)

    print(f"[Retry] {platform} — all {MAX_ATTEMPTS} attempts exhausted.")
    return last_result
