import logging

import httpx

logger = logging.getLogger(__name__)


def fetch_source_content(url: str, max_chars: int = 8000) -> str:
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            content = response.text[:max_chars]
            return content if content.strip() else "Source returned empty content."
    except Exception as exc:
        logger.warning("Failed to fetch source %s: %s", url, exc)
        return f"Could not fetch source: {url}"
