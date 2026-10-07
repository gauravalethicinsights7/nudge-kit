"""Pluggable web search + fetch, per CLAUDE.md's tech stack line
"Web research: pluggable search + fetch tool behind tools/web.py".

Backend: Serper (Google Search API wrapper) for search, httpx + trafilatura
for fetch/extract. Both network calls are isolated in small
`_*_request`/`_http_get` functions so tests can monkeypatch them instead of
hitting the network, the same pattern as llm/client.py::_call_anthropic.
"""

from __future__ import annotations

import os
from datetime import datetime

import httpx
from pydantic import BaseModel

from schemas.base import utcnow

SERPER_SEARCH_URL = "https://google.serper.dev/search"
DEFAULT_TIMEOUT = 15.0
USER_AGENT = "NudgeOmnichannel-M1-ResearchAgent/0.1"


class MissingAPIKeyError(Exception):
    pass


class FetchError(Exception):
    pass


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""


class FetchedPage(BaseModel):
    url: str
    title: str = ""
    text: str
    fetched_at: datetime


def _serper_search_request(query: str, count: int) -> dict:
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise MissingAPIKeyError("SERPER_API_KEY is not set (copy .env.example to .env)")
    response = httpx.post(
        SERPER_SEARCH_URL,
        json={"q": query, "num": count},
        headers={"Content-Type": "application/json", "X-API-KEY": api_key},
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def search(query: str, count: int = 10) -> list[SearchResult]:
    data = _serper_search_request(query, count)
    return [
        SearchResult(
            title=item.get("title", ""),
            url=item["link"],
            snippet=item.get("snippet", ""),
        )
        for item in data.get("organic", [])
    ]


def _http_get(url: str) -> httpx.Response:
    response = httpx.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
    )
    response.raise_for_status()
    return response


def fetch(url: str) -> FetchedPage:
    """Fetches and extracts readable article text. Never returns a search
    snippet as a substitute — per spec, the extractor only ever sees this."""
    try:
        response = _http_get(url)
    except httpx.HTTPError as e:
        raise FetchError(f"failed to fetch {url}: {e}") from e

    import trafilatura

    extracted = trafilatura.bare_extraction(response.text, url=url, as_dict=True)
    if not extracted or not extracted.get("text"):
        raise FetchError(f"could not extract readable text from {url}")

    return FetchedPage(
        url=url,
        title=extracted.get("title") or "",
        text=extracted["text"],
        fetched_at=utcnow(),
    )
