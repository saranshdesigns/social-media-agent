"""
Google Drive Watcher Module
- Connects using existing Google credentials (same project as your chatbot)
- Reads the Portfolio folder (read-only, never modifies Drive)
- Recursively scans subfolders for new images
- Filters out already-posted images using the local DB
"""
import os
import io
from typing import Optional
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import database
from config import get_settings

settings = get_settings()

# Read-only scope — this agent never writes to Drive
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/tiff",
}


def _get_drive_service():
    """
    Build the Drive API service client.
    Supports both:
      - Service Account (credentials.json with type: service_account)
      - OAuth2 user credentials (credentials.json from Google Cloud Console)
    """
    creds_path = settings.google_credentials_path

    # --- Try service account first ---
    try:
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)
    except Exception:
        pass

    # --- Fall back to OAuth2 (same flow your chatbot likely uses) ---
    creds = None
    token_path = "token.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def _list_images_in_folder(service, folder_id: str, folder_path: str = "") -> list[dict]:
    """
    Recursively list all image files inside a folder and its subfolders.
    Returns a list of dicts with file metadata.
    """
    results = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)",
            pageToken=page_token
        ).execute()

        for item in response.get("files", []):
            mime = item.get("mimeType", "")
            if mime == "application/vnd.google-apps.folder":
                # Recurse into subfolder
                sub_path = f"{folder_path}/{item['name']}" if folder_path else item["name"]
                results.extend(
                    _list_images_in_folder(service, item["id"], sub_path)
                )
            elif mime in SUPPORTED_MIME_TYPES:
                results.append({
                    "id": item["id"],
                    "name": item["name"],
                    "mime_type": mime,
                    "folder_path": folder_path,
                    "created_time": item.get("createdTime", ""),
                    "modified_time": item.get("modifiedTime", ""),
                })

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return results


def _parse_slide_info(file_name: str):
    """
    Parse filename to extract group key and slide number.

    Naming convention: 'Mahodey 1.1.jpg' → group='Mahodey 1', slide=1.0
    Files without a dot in the name (after stripping extension) → standalone.

    Returns:
        (group_key: str, slide_num: float)
    """
    name_no_ext, _ = os.path.splitext(file_name)

    if "." not in name_no_ext:
        return name_no_ext, 0.0

    last_dot = name_no_ext.rfind(".")
    group_key = name_no_ext[:last_dot]
    slide_str = name_no_ext[last_dot + 1:]

    try:
        slide_num = float(slide_str)
    except ValueError:
        return name_no_ext, 0.0

    return group_key, slide_num


def get_new_image_groups(limit: int = None) -> list[dict]:
    """
    Main entry point. Returns image GROUPS from Portfolio folder that have NOT
    been posted yet, grouped by filename convention:
      'Mahodey 1.1.jpg' + 'Mahodey 1.2.jpg' → one carousel group
      'Logo.jpg' → standalone single-image group

    Args:
        limit: max number of GROUPS to return (None = no limit / bulk mode)

    Returns:
        List of group dicts:
        [{"group_key", "folder_path", "is_carousel", "slides": [img_meta...]}, ...]
    """
    print("[Drive] Connecting to Google Drive...")
    service = _get_drive_service()

    print(f"[Drive] Scanning Portfolio folder: {settings.google_portfolio_folder_id}")
    all_images = _list_images_in_folder(
        service, settings.google_portfolio_folder_id, folder_path=""
    )
    print(f"[Drive] Total images found: {len(all_images)}")

    new_images = [img for img in all_images if not database.is_already_posted(img["id"])]
    print(f"[Drive] New (unposted) images: {len(new_images)}")

    if not new_images:
        print("[Drive] No new images found.")
        return []

    # Group images by (group_key, folder_path)
    groups: dict[tuple, list] = {}
    for img in new_images:
        group_key, slide_num = _parse_slide_info(img["name"])
        key = (group_key, img["folder_path"])
        if key not in groups:
            groups[key] = []
        groups[key].append((slide_num, img))

    all_groups = []
    for (group_key, folder_path), slides_raw in groups.items():
        slides_raw.sort(key=lambda x: x[0])
        slides = [img for _, img in slides_raw]
        all_groups.append({
            "group_key": group_key,
            "folder_path": folder_path,
            "is_carousel": len(slides) > 1,
            "slides": slides,
        })

    # ── Mixed category round-robin ─────────────────────────────
    # Group by folder (category), sort each category oldest-first
    by_category: dict[str, list] = {}
    for g in all_groups:
        cat = g["folder_path"] or "root"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(g)

    for cat in by_category:
        by_category[cat].sort(key=lambda g: g["slides"][0]["created_time"])

    # Order categories by their oldest item so we don't always favour one folder
    cat_order = sorted(by_category.keys(), key=lambda c: by_category[c][0]["slides"][0]["created_time"])
    pointers = {cat: 0 for cat in cat_order}

    result = []
    while True:
        added = False
        for cat in cat_order:
            idx = pointers[cat]
            if idx < len(by_category[cat]):
                result.append(by_category[cat][idx])
                pointers[cat] += 1
                added = True
                if limit is not None and len(result) >= limit:
                    break
        if not added or (limit is not None and len(result) >= limit):
            break

    categories_used = list(by_category.keys())
    total_slides = sum(len(g["slides"]) for g in result)
    print(f"[Drive] Groups to post: {len(result)} post(s), {total_slides} slide(s) — categories: {categories_used}")
    return result


def get_latest_image_group() -> dict | None:
    """
    Returns the single NEWEST unposted image group from the Portfolio folder.
    Sorted by newest created_time first — returns only 1 group.
    Used for the 'Post Latest' on-demand trigger.
    """
    print("[Drive] Fetching latest unposted image group...")
    service = _get_drive_service()
    all_images = _list_images_in_folder(
        service, settings.google_portfolio_folder_id, folder_path=""
    )

    new_images = [img for img in all_images if not database.is_already_posted(img["id"])]
    if not new_images:
        print("[Drive] No unposted images found.")
        return None

    groups: dict[tuple, list] = {}
    for img in new_images:
        group_key, slide_num = _parse_slide_info(img["name"])
        key = (group_key, img["folder_path"])
        if key not in groups:
            groups[key] = []
        groups[key].append((slide_num, img))

    result = []
    for (group_key, folder_path), slides_raw in groups.items():
        slides_raw.sort(key=lambda x: x[0])
        slides = [img for _, img in slides_raw]
        latest_time = max(s["created_time"] for s in slides)
        result.append({
            "group_key": group_key,
            "folder_path": folder_path,
            "is_carousel": len(slides) > 1,
            "slides": slides,
            "_latest_time": latest_time,
        })

    # Sort newest-first, return only the latest
    result.sort(key=lambda g: g["_latest_time"], reverse=True)
    latest = result[0]
    latest.pop("_latest_time")
    print(f"[Drive] Latest group: '{latest['group_key']}' ({len(latest['slides'])} slide(s))")
    return latest


def get_new_images(limit: int = None) -> list[dict]:
    """Legacy — kept for compatibility."""
    if limit is None:
        limit = settings.max_posts_per_day
    service = _get_drive_service()
    all_images = _list_images_in_folder(
        service, settings.google_portfolio_folder_id, folder_path=""
    )
    new_images = [img for img in all_images if not database.is_already_posted(img["id"])]
    new_images.sort(key=lambda x: x["created_time"])
    return new_images[:limit]


def download_image(drive_file_id: str, mime_type: str) -> bytes:
    """
    Download a file from Google Drive and return raw bytes.
    Used by the image processor before uploading to Cloudinary.
    """
    service = _get_drive_service()
    request = service.files().get_media(fileId=drive_file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()
