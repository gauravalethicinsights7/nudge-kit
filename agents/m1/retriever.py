from __future__ import annotations

import httpx

from agents.m1.tools import FetchedPage, FetchError, MissingAPIKeyError, fetch, search

MAX_PAGES_PER_RUN = 40
"""Deterministic cap on fan-out. Each fetched page becomes one extractor LLM
call (llm/client.py enforces NUDGE_RUN_BUDGET_USD per call, but not across a
whole pipeline) — this bounds the worst case without needing a separate
pipeline-wide cost tracker, which is a real gap left for a later session."""


def retrieve_pages(
    queries: list[str],
    max_results_per_query: int = 3,
    max_pages: int = MAX_PAGES_PER_RUN,
) -> list[FetchedPage]:
    """Search + fetch full pages for each query, deduped by URL. Per
    specs/m1-research.md: 'fetch the page, never use a search snippet as
    evidence' — this returns FetchedPage (full extracted text), not
    SearchResult (title/snippet). A failed search or fetch for one query/page
    is skipped, not fabricated; a missing API key is a config error and
    propagates immediately rather than silently producing zero evidence."""
    seen_urls: set[str] = set()
    pages: list[FetchedPage] = []

    for query in queries:
        if len(pages) >= max_pages:
            break
        try:
            results = search(query, count=max_results_per_query)
        except MissingAPIKeyError:
            raise
        except httpx.HTTPError:
            continue

        for result in results[:max_results_per_query]:
            if len(pages) >= max_pages:
                break
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)
            try:
                pages.append(fetch(result.url))
            except FetchError:
                continue

    return pages
