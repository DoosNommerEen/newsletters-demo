"""Gamma presentation creation tool.

Uses the Gamma public API to generate an AI-powered slide deck from the
newsletter's structured content. The API is asynchronous: we POST to create
a generation job, then poll until it completes and return the public URL.
"""

import logging
import os
import time

import requests

log = logging.getLogger(__name__)

GAMMA_BASE_URL = "https://public-api.gamma.app/v1.0"
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 12  # 12 x 10s = 2 minutes max


def _build_input_text(summary: dict, week_label: str) -> str:
    """Compose the slide outline text sent to Gamma."""
    outline = summary.get("slide_outline", "")
    if outline:
        return outline

    # Fallback: build a basic outline from structured fields
    trends = "\n".join(f"• {t}" for t in summary.get("top_trends", []))
    insights = "\n\n".join(summary.get("key_insights", []))
    devs = "\n".join(
        f"• {d['title']}: {d['summary']}"
        for d in summary.get("notable_developments", [])
    )
    return (
        f"AI & Tech Trends — {week_label}\n---\n"
        f"This Week's Overview\n{trends}\n---\n"
        f"Key Insights\n{insights}\n---\n"
        f"Notable Developments\n{devs}\n---\n"
        f"That's a Wrap\nRead more in this week's newsletter."
    )


def run_create_presentation(summary: dict, week_label: str) -> str:
    """Create a Gamma presentation and return its public URL.

    Args:
        summary: Structured summary dict from summarise.run_summarise.
        week_label: Human-readable week label (e.g. "Week of March 14, 2026").

    Returns:
        Public Gamma presentation URL string.

    Raises:
        RuntimeError: If the generation fails or the API returns an error.
        TimeoutError: If the generation does not complete within the polling window.
    """
    api_key = os.environ.get("GAMMA_API_KEY")
    if not api_key:
        raise RuntimeError("GAMMA_API_KEY environment variable is not set.")

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    input_text = _build_input_text(summary, week_label)

    payload = {
        "inputText": input_text,
        "textMode": "condense",
        "format": "presentation",
        "cardSplit": "inputTextBreaks",
        "numCards": 8,
        "textOptions": {
            "amount": "medium",
            "tone": "professional, informative",
            "audience": "technology professionals",
            "language": "en",
        },
        "imageOptions": {
            "source": "aiGenerated",
            "style": "clean, modern, tech-focused",
        },
    }

    # Phase 1: Submit generation job
    log.info("Submitting Gamma generation request...")
    response = requests.post(
        f"{GAMMA_BASE_URL}/generations",
        json=payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    generation_id = response.json().get("generationId") or response.json().get("id")
    if not generation_id:
        raise RuntimeError(f"Gamma API did not return a generationId. Response: {response.json()}")

    log.info("Generation job submitted. ID: %s — polling for completion...", generation_id)

    # Phase 2: Poll for completion
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        time.sleep(POLL_INTERVAL_SECONDS)
        poll_response = requests.get(
            f"{GAMMA_BASE_URL}/generations/{generation_id}",
            headers=headers,
            timeout=30,
        )
        poll_response.raise_for_status()
        data = poll_response.json()
        status = data.get("status", "unknown")
        log.info("Poll attempt %d/%d — status: %s", attempt, MAX_POLL_ATTEMPTS, status)

        if status == "completed":
            gamma_url = data.get("gammaUrl") or data.get("url") or data.get("shareUrl")
            if not gamma_url:
                raise RuntimeError(f"Generation completed but no URL found. Response: {data}")
            log.info("Gamma presentation ready: %s", gamma_url)
            return gamma_url

        if status == "failed":
            raise RuntimeError(f"Gamma generation failed. Response: {data}")

    raise TimeoutError(
        f"Gamma generation did not complete after {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s. "
        f"Generation ID: {generation_id}"
    )
