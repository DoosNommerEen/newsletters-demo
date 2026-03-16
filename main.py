"""Weekly AI & Technology Newsletter Pipeline.

Orchestrates the four-step newsletter generation workflow:
  1. Web Research  — Tavily API
  2. Summarisation — Anthropic Claude API
  3. Presentation  — Gamma API
  4. Email         — Gmail SMTP

Run directly:
    python main.py

Triggered automatically by n8n on a weekly schedule (see n8n_workflow.json).
Environment variables are loaded from a .env file in the project root.
"""

import logging
import sys
from datetime import datetime

from dotenv import load_dotenv

from src.tools.create_presentation import run_create_presentation
from src.tools.send_email import run_send_email
from src.tools.summarise import run_summarise
from src.tools.web_search import run_web_search

TOPIC = "AI & Technology Trends"


def main() -> int:
    """Run the full newsletter pipeline. Returns 0 on success, 1 on failure."""
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    log = logging.getLogger(__name__)

    week_label = datetime.now().strftime("Week of %B %d, %Y")
    log.info("=" * 60)
    log.info("Newsletter pipeline starting — %s", week_label)
    log.info("Topic: %s", TOPIC)
    log.info("=" * 60)

    try:
        # Step 1: Web Research
        log.info("[Step 1/4] Running web research...")
        search_results = run_web_search(topic=TOPIC)
        log.info("[Step 1/4] Complete — %d articles collected.", len(search_results))

        # Step 2: Summarise
        log.info("[Step 2/4] Summarising with Claude...")
        summary = run_summarise(
            search_results=search_results,
            topic=TOPIC,
            week_label=week_label,
        )
        log.info("[Step 2/4] Complete — summary structured.")

        # Step 3: Create Gamma presentation
        log.info("[Step 3/4] Creating Gamma presentation...")
        gamma_url = run_create_presentation(summary=summary, week_label=week_label)
        log.info("[Step 3/4] Complete — presentation URL: %s", gamma_url)

        # Step 4: Send email
        log.info("[Step 4/4] Sending newsletter email...")
        run_send_email(summary=summary, gamma_url=gamma_url, week_label=week_label)
        log.info("[Step 4/4] Complete — email delivered.")

        log.info("=" * 60)
        log.info("Pipeline finished successfully.")
        log.info("=" * 60)
        return 0

    except Exception as exc:
        log.exception("Pipeline failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
