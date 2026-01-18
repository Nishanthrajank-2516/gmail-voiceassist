import re
from html import unescape


def analyze_email(email: dict) -> dict:
    """
    Analyze email content to detect:
    - html
    - images
    - attachments
    """

    has_html = False
    has_images = False
    attachments = []

    html = email.get("html")
    if html:
        has_html = True
        if re.search(r"<img\s", html, re.IGNORECASE):
            has_images = True

    attachments = email.get("attachments") or []

    return {
        "has_html": has_html,
        "has_images": has_images,
        "attachments": attachments,
    }


def html_to_text(html: str) -> str:
    """
    Very lightweight HTML → text conversion
    (safe for speech, no heavy libs)
    """
    # Remove scripts/styles
    html = re.sub(r"<(script|style).*?>.*?</\1>", "", html, flags=re.DOTALL)

    # Remove all tags
    text = re.sub(r"<[^>]+>", "", html)

    # Decode HTML entities
    text = unescape(text)

    # Clean spacing
    text = re.sub(r"\s+", " ", text).strip()

    return text
