"""Summarisation tool using the Anthropic Claude API.

Takes raw search results and extracts a structured newsletter summary including
a slide outline suitable for Gamma presentation generation.
"""

import json
import logging
import os
import re

import anthropic

log = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2000
MAX_SEARCH_RESULTS = 20


def _build_prompt(search_results: list[dict], topic: str, week_label: str) -> str:
    """Build the structured extraction prompt from search results."""
    articles = "\n\n".join(
        f"[{i + 1}] {r['title']}\nURL: {r['url']}\n{r['content'][:800]}"
        for i, r in enumerate(search_results[:MAX_SEARCH_RESULTS])
    )
    return f"""You are an expert technology analyst producing a weekly newsletter on "{topic}" for {week_label}.

Below are this week's most relevant news articles and research snippets:

{articles}

Analyse the above and return a JSON object with exactly these fields:

{{
  "newsletter_intro": "A compelling 2–3 sentence opening paragraph for the newsletter. Should hook the reader with the most interesting development of the week.",
  "top_trends": ["Trend 1 (1 sentence)", "Trend 2", "Trend 3", "Trend 4", "Trend 5"],
  "key_insights": ["Insight 1 (2–3 sentences of analysis)", "Insight 2", "Insight 3"],
  "notable_developments": [
    {{"title": "Short headline", "summary": "1–2 sentence summary", "url": "source URL"}},
    {{"title": "...", "summary": "...", "url": "..."}},
    {{"title": "...", "summary": "...", "url": "..."}}
  ],
  "slide_outline": "Title: AI & Tech Trends — {week_label}\\n---\\nThis Week's Overview\\n• [bullet 1]\\n• [bullet 2]\\n• [bullet 3]\\n---\\nTop Trend: [Name]\\n[2-3 sentence explanation]\\n---\\nKey Insight 1\\n[explanation]\\n---\\nKey Insight 2\\n[explanation]\\n---\\nNotable Development\\n[headline and brief context]\\n---\\nWhat to Watch\\n• [forward-looking point 1]\\n• [forward-looking point 2]\\n---\\nThat's a Wrap\\nRead more and explore sources at the links in this week's email."
}}

Rules:
- Return ONLY valid JSON. No markdown, no code fences, no extra text.
- The slide_outline field uses \\n---\\n as slide separators for Gamma. Keep each slide concise.
- Source URLs must come from the articles provided above.
- Write in a professional but accessible tone suitable for technology professionals."""


def run_summarise(search_results: list[dict], topic: str, week_label: str) -> dict:
    """Summarise search results into a structured newsletter dict using Claude.

    Args:
        search_results: List of result dicts from web_search.run_web_search.
        topic: Research topic string.
        week_label: Human-readable week label (e.g. "Week of March 14, 2026").

    Returns:
        Dict with keys: newsletter_intro, top_trends, key_insights,
        notable_developments, slide_outline.

    Raises:
        RuntimeError: On API errors or if the response cannot be parsed.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(search_results, topic, week_label)

    log.info("Sending %d results to Claude for summarisation", len(search_results[:MAX_SEARCH_RESULTS]))

    for attempt in range(2):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()

            # Strip any accidental markdown code fences
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            summary = json.loads(raw)
            log.info("Summarisation complete — %d top trends, %d developments",
                     len(summary.get("top_trends", [])),
                     len(summary.get("notable_developments", [])))
            return summary

        except json.JSONDecodeError as exc:
            log.warning("Attempt %d: Failed to parse Claude response as JSON: %s", attempt + 1, exc)
            if attempt == 1:
                raise RuntimeError(f"Claude returned unparseable JSON after 2 attempts: {exc}") from exc
        except anthropic.APIError as exc:
            log.warning("Attempt %d: Anthropic API error: %s", attempt + 1, exc)
            if attempt == 1:
                raise RuntimeError(f"Anthropic API failed after 2 attempts: {exc}") from exc

    raise RuntimeError("Summarisation failed after 2 attempts.")
