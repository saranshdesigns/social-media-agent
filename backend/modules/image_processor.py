"""
Image Processor Module
- Downloads image from Google Drive as-is (no resizing, no compression)
- Saves original file to temp/ folder served publicly by FastAPI
- No editing whatsoever — your portfolio images are already social-media ready
"""
import os
from config import get_settings
from modules.drive_watcher import download_image

settings = get_settings()

# Temp folder — created inside backend/ at runtime
TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "temp"))


def _get_extension(mime_type: str, file_name: str) -> str:
    """Determine file extension from mime type or file name."""
    mime_map = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    if mime_type in mime_map:
        return mime_map[mime_type]
    # Fallback: use existing file extension
    _, ext = os.path.splitext(file_name)
    return ext.lower() if ext else ".jpg"


def process_image(drive_file_id: str, mime_type: str, file_name: str) -> dict:
    """
    Download from Google Drive and save to temp/ with no modifications.

    Returns:
        {
            "public_url": str,       # https://your-server/temp/{id}.ext
            "temp_file_path": str,   # local path for cleanup after posting
            "raw_bytes": bytes,      # original image bytes for OpenAI vision
        }
    """
    os.makedirs(TEMP_DIR, exist_ok=True)

    print(f"[Image] Downloading: {file_name}")
    raw_bytes = download_image(drive_file_id, mime_type)
    print(f"[Image] Downloaded {len(raw_bytes) // 1024}KB — saving as-is (no editing)")

    ext = _get_extension(mime_type, file_name)
    temp_filename = f"{drive_file_id}{ext}"
    temp_path = os.path.join(TEMP_DIR, temp_filename)

    with open(temp_path, "wb") as f:
        f.write(raw_bytes)

    public_url = f"{settings.server_base_url.rstrip('/')}/temp/{temp_filename}"
    print(f"[Image] Temp public URL: {public_url}")

    return {
        "public_url": public_url,
        "temp_file_path": temp_path,
        "raw_bytes": raw_bytes,
    }


def cleanup_temp(temp_file_path: str):
    """Delete the temporary image file after posting is complete."""
    try:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"[Image] Temp file deleted: {temp_file_path}")
    except Exception as e:
        print(f"[Image] Temp cleanup warning: {e}")
