"""Web search tool using Tavily API.

Runs multiple focused sub-queries on the given topic and returns a deduplicated,
relevance-sorted list of search results for downstream summarisation.
"""

import logging
import os

from tavily import TavilyClient

log = logging.getLogger(__name__)

SUB_QUERIES: list[str] = [
    "latest AI research breakthroughs this week",
    "AI technology product launches this week",
    "large language model developments this week",
    "AI regulation and policy news this week",
    "notable AI startup funding news this week",
]


def run_web_search(topic: str) -> list[dict]:
    """Search the web for recent news on the given topic using Tavily.

    Args:
        topic: High-level research topic (e.g. "AI & Technology Trends").

    Returns:
        Deduplicated list of result dicts with keys: title, url, content, score.
        Sorted by relevance score descending.

    Raises:
        ValueError: If no results are returned across all sub-queries.
        RuntimeError: On Tavily API errors.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY environment variable is not set.")

    client = TavilyClient(api_key=api_key)
    seen_urls: set[str] = set()
    results: list[dict] = []

    log.info("Running %d sub-queries for topic: %s", len(SUB_QUERIES), topic)

    for query in SUB_QUERIES:
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                topic="news",
                max_results=5,
            )
            for item in response.get("results", []):
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "url": url,
                            "content": item.get("content", ""),
                            "score": item.get("score", 0.0),
                        }
                    )
            log.info("Query '%s' returned %d new results", query, len(response.get("results", [])))
        except Exception as exc:
            log.warning("Sub-query '%s' failed: %s", query, exc)

    if not results:
        raise ValueError(f"No search results returned for topic: {topic}")

    results.sort(key=lambda x: x["score"], reverse=True)
    log.info("Total unique results: %d", len(results))
    return results
