"""
AI Caption Engine — OpenAI GPT-4o-mini (cheapest model with vision)
- Analyzes image content using vision API
- Detects design category (packaging, branding, logo, label, etc.)
- Generates platform-specific captions with hashtags
- Each call produces unique captions to avoid repetition
"""
import base64
from openai import OpenAI
from config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)

# Platform-specific caption instructions
PLATFORM_PROMPTS = {
    "instagram": (
        "Write an Instagram caption. 1-2 lines max. High engagement, "
        "professional and creative tone. End with 15-20 relevant hashtags on a new line. "
        "Hashtags must include variations of: packaging design, branding, graphic design, "
        "packaging designer, product packaging. Add category-specific hashtags too."
    ),
    "facebook": (
        "Write a Facebook Page caption. 1-2 lines max. Warm, professional tone. "
        "Add 5-8 relevant hashtags at the end. "
        "Hashtags: packaging design, branding, graphic design, product packaging."
    ),
}

DESIGN_CATEGORIES = [
    "packaging design",
    "logo design",
    "brand identity",
    "label design",
    "product packaging",
    "box design",
    "pouch design",
    "bottle label",
    "typography",
    "branding",
]


def _image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def detect_design_category(image_bytes: bytes) -> str:
    """
    Use GPT-4o-mini vision to detect what type of design work is shown.
    Returns a short category string like 'packaging design' or 'logo design'.
    """
    b64 = _image_to_base64(image_bytes)
    categories_list = ", ".join(DESIGN_CATEGORIES)

    response = client.chat.completions.create(
        model=settings.openai_model,  # gpt-4o-mini
        max_tokens=50,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "low",  # cheapest vision detail level
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Look at this design portfolio image. "
                            f"Which category best describes it? Choose one from: {categories_list}. "
                            f"Reply with ONLY the category name, nothing else."
                        ),
                    },
                ],
            }
        ],
    )
    category = response.choices[0].message.content.strip().lower()
    print(f"[Caption] Detected design category: {category}")
    return category


def generate_captions(image_bytes: bytes, file_name: str = "") -> dict:
    """
    Generate platform-specific captions for a portfolio image.

    Args:
        image_bytes: raw image bytes (original quality, for AI vision)
        file_name: optional file name hint for context

    Returns:
        {
            "category": str,
            "instagram": str,
            "facebook": str,
        }
    """
    print(f"[Caption] Generating captions for: {file_name or 'image'}")

    # Step 1: Detect category
    category = detect_design_category(image_bytes)
    b64 = _image_to_base64(image_bytes)

    captions = {"category": category}

    for platform, instruction in PLATFORM_PROMPTS.items():
        print(f"[Caption] Generating {platform} caption...")
        response = client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=300,
            temperature=0.9,  # high temp = more variation between captions
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional social media copywriter specializing in "
                        "design portfolios — specifically packaging design, branding, and "
                        "graphic design. Write captions that attract potential clients and "
                        "fellow designers. Always sound authentic, never robotic."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                                "detail": "low",
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                f"This is a {category} portfolio piece.\n\n"
                                f"{instruction}\n\n"
                                f"Make the caption feel fresh and unique — not generic."
                            ),
                        },
                    ],
                },
            ],
        )
        caption = response.choices[0].message.content.strip()
        captions[platform] = caption
        print(f"[Caption] {platform} done ({len(caption)} chars)")

    return captions
