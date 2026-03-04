"""
Facebook Page Poster — via Facebook Graph API
Posts image directly to a Facebook Page feed.
"""
import requests
from config import get_settings

settings = get_settings()

GRAPH_URL = "https://graph.facebook.com/v19.0"


def post_album(image_urls: list, caption: str) -> dict:
    """
    Post multiple images as a single album/multi-photo post to a Facebook Page.

    Args:
        image_urls: list of publicly accessible image URLs
        caption: Facebook caption

    Returns:
        {"success": bool, "post_id": str or None, "error": str or None}
    """
    page_id = settings.facebook_page_id
    token = settings.facebook_page_access_token

    # Step 1: Upload each photo without publishing
    photo_ids = []
    for i, url in enumerate(image_urls):
        print(f"[Facebook] Uploading photo {i + 1}/{len(image_urls)} (unpublished)...")
        resp = requests.post(
            f"{GRAPH_URL}/{page_id}/photos",
            params={
                "url": url,
                "published": "false",
                "access_token": token,
            },
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            error_msg = data["error"].get("message", str(data["error"]))
            print(f"[Facebook] Photo upload error: {error_msg}")
            return {"success": False, "post_id": None, "error": error_msg}
        photo_ids.append(data["id"])

    # Step 2: Create a post with all photos attached
    print(f"[Facebook] Creating album post with {len(photo_ids)} photos...")
    attached = [{"media_fbid": pid} for pid in photo_ids]
    resp = requests.post(
        f"{GRAPH_URL}/{page_id}/feed",
        json={
            "message": caption,
            "attached_media": attached,
            "access_token": token,
        },
        timeout=30,
    )
    data = resp.json()
    if "error" in data:
        error_msg = data["error"].get("message", str(data["error"]))
        print(f"[Facebook] Album post error: {error_msg}")
        return {"success": False, "post_id": None, "error": error_msg}

    post_id = data.get("id")
    print(f"[Facebook] Album posted successfully: {post_id}")
    return {"success": True, "post_id": post_id, "error": None}


def post_image(cloudinary_url: str, caption: str) -> dict:
    """
    Post an image with caption to a Facebook Page.

    Args:
        cloudinary_url: publicly accessible image URL
        caption: Facebook-specific caption

    Returns:
        {"success": bool, "post_id": str or None, "error": str or None}
    """
    page_id = settings.facebook_page_id
    token = settings.facebook_page_access_token

    print("[Facebook] Posting image to Page...")
    resp = requests.post(
        f"{GRAPH_URL}/{page_id}/photos",
        params={
            "url": cloudinary_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=30,
    )
    data = resp.json()

    if "error" in data:
        error_msg = data["error"].get("message", str(data["error"]))
        print(f"[Facebook] Error: {error_msg}")
        return {"success": False, "post_id": None, "error": error_msg}

    post_id = data.get("id") or data.get("post_id")
    print(f"[Facebook] Posted successfully: {post_id}")
    return {"success": True, "post_id": post_id, "error": None}
