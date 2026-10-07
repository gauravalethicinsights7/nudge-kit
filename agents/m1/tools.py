"""M1-scoped wrapper over the shared tools/web.py, per CLAUDE.md's
`/agents/<mod>` layout (agent.py, prompts/, tools.py per module)."""

from tools.web import FetchedPage, FetchError, MissingAPIKeyError, SearchResult, fetch, search

__all__ = ["FetchedPage", "FetchError", "MissingAPIKeyError", "SearchResult", "fetch", "search"]
