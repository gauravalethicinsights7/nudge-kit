import httpx
import pytest

from tools.web import FetchError, MissingAPIKeyError, fetch, search


def test_search_parses_results(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "fake-key")

    def fake_request(query, count):
        return {
            "organic": [
                {"title": "A", "link": "https://example.com/a", "snippet": "desc a"},
                {"title": "B", "link": "https://example.com/b", "snippet": "desc b"},
            ]
        }

    monkeypatch.setattr("tools.web._serper_search_request", fake_request)

    results = search("some query", count=2)

    assert len(results) == 2
    assert results[0].title == "A"
    assert results[0].url == "https://example.com/a"
    assert results[0].snippet == "desc a"


def test_search_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError):
        search("some query")


def test_fetch_extracts_title_and_text(monkeypatch):
    class FakeResponse:
        text = "<html>irrelevant, trafilatura is mocked</html>"

    monkeypatch.setattr("tools.web._http_get", lambda url: FakeResponse())
    monkeypatch.setattr(
        "trafilatura.bare_extraction",
        lambda html, url=None, as_dict=True: {"title": "Some Title", "text": "Some extracted text."},
    )

    page = fetch("https://example.com/article")

    assert page.url == "https://example.com/article"
    assert page.title == "Some Title"
    assert page.text == "Some extracted text."
    assert page.fetched_at is not None


def test_fetch_raises_when_no_extractable_text(monkeypatch):
    class FakeResponse:
        text = "<html></html>"

    monkeypatch.setattr("tools.web._http_get", lambda url: FakeResponse())
    monkeypatch.setattr("trafilatura.bare_extraction", lambda html, url=None, as_dict=True: None)

    with pytest.raises(FetchError):
        fetch("https://example.com/empty")


def test_fetch_wraps_http_errors(monkeypatch):
    def raise_http_error(url):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr("tools.web._http_get", raise_http_error)

    with pytest.raises(FetchError):
        fetch("https://example.com/down")
