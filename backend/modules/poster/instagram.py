"""
Instagram Poster — via Facebook Graph API
Requires: Instagram Business Account linked to a Facebook Page

Flow (required by Meta):
1. POST /ig-user-id/media  → create media container with image URL + caption
2. POST /ig-user-id/media_publish  → publish the container
"""
import requests
from config import get_settings

settings = get_settings()

GRAPH_URL = "https://graph.facebook.com/v19.0"


def post_carousel(image_urls: list, caption: str) -> dict:
    """
    Post a carousel (multi-slide) post to Instagram.

    Args:
        image_urls: list of publicly accessible image URLs (2–10 images)
        caption: Instagram caption with hashtags

    Returns:
        {"success": bool, "post_id": str or None, "error": str or None}
    """
    account_id = settings.instagram_account_id
    token = settings.facebook_page_access_token

    # Step 1: Create a carousel item container for each image
    children_ids = []
    for i, url in enumerate(image_urls):
        print(f"[Instagram] Creating carousel item {i + 1}/{len(image_urls)}...")
        resp = requests.post(
            f"{GRAPH_URL}/{account_id}/media",
            params={
                "image_url": url,
                "is_carousel_item": "true",
                "access_token": token,
            },
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            error_msg = data["error"].get("message", str(data["error"]))
            print(f"[Instagram] Carousel item error: {error_msg}")
            return {"success": False, "post_id": None, "error": error_msg}
        children_ids.append(data["id"])

    # Step 2: Create the carousel container
    print(f"[Instagram] Creating carousel container with {len(children_ids)} items...")
    carousel_resp = requests.post(
        f"{GRAPH_URL}/{account_id}/media",
        params={
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
            "access_token": token,
        },
        timeout=30,
    )
    carousel_data = carousel_resp.json()
    if "error" in carousel_data:
        error_msg = carousel_data["error"].get("message", str(carousel_data["error"]))
        print(f"[Instagram] Carousel container error: {error_msg}")
        return {"success": False, "post_id": None, "error": error_msg}

    carousel_id = carousel_data.get("id")

    # Step 3: Publish the carousel
    publish_resp = requests.post(
        f"{GRAPH_URL}/{account_id}/media_publish",
        params={"creation_id": carousel_id, "access_token": token},
        timeout=30,
    )
    publish_data = publish_resp.json()
    if "error" in publish_data:
        error_msg = publish_data["error"].get("message", str(publish_data["error"]))
        print(f"[Instagram] Carousel publish error: {error_msg}")
        return {"success": False, "post_id": None, "error": error_msg}

    post_id = publish_data.get("id")
    print(f"[Instagram] Carousel posted successfully: {post_id}")
    return {"success": True, "post_id": post_id, "error": None}


def post_image(cloudinary_url: str, caption: str) -> dict:
    """
    Post an image to Instagram Business account.

    Args:
        cloudinary_url: publicly accessible image URL
        caption: Instagram-specific caption with hashtags

    Returns:
        {"success": bool, "post_id": str or None, "error": str or None}
    """
    account_id = settings.instagram_account_id
    token = settings.facebook_page_access_token

    # Step 1: Create media container
    print("[Instagram] Creating media container...")
    container_resp = requests.post(
        f"{GRAPH_URL}/{account_id}/media",
        params={
            "image_url": cloudinary_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=30,
    )
    container_data = container_resp.json()

    if "error" in container_data:
        error_msg = container_data["error"].get("message", str(container_data["error"]))
        print(f"[Instagram] Container error: {error_msg}")
        return {"success": False, "post_id": None, "error": error_msg}

    container_id = container_data.get("id")
    if not container_id:
        return {"success": False, "post_id": None, "error": "No container ID returned"}

    print(f"[Instagram] Container created: {container_id}")

    # Step 2: Publish the container
    publish_resp = requests.post(
        f"{GRAPH_URL}/{account_id}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": token,
        },
        timeout=30,
    )
    publish_data = publish_resp.json()

    if "error" in publish_data:
        error_msg = publish_data["error"].get("message", str(publish_data["error"]))
        print(f"[Instagram] Publish error: {error_msg}")
        return {"success": False, "post_id": None, "error": error_msg}

    post_id = publish_data.get("id")
    print(f"[Instagram] Posted successfully: {post_id}")
    return {"success": True, "post_id": post_id, "error": None}
