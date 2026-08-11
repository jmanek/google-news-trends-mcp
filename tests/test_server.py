import asyncio
import pytest
from contextlib import asynccontextmanager
from fastmcp import Client
from fastmcp.exceptions import ToolError
from google_news_trends_mcp.server import mcp
from google_news_trends_mcp import news
from google_news_trends_mcp.news import (
    download_article_with_playwright,
    save_article_to_json,
    download_article,
    BrowserManager,
)
from pathlib import Path


@pytest.fixture
def mcp_server():
    yield mcp


async def test_smoke(mcp_server):
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
        assert isinstance(tools, list)


async def test_download_article():
    async with BrowserManager():
        article = await download_article("nytimes.com")
        assert article is None
        article = await download_article_with_playwright(
            "https://archive.nytimes.com/www.nytimes.com/learning/general/onthisday/big/0720.html"
        )
        assert article is not None
        article_path = Path(__file__).parent / Path("test.json")
        save_article_to_json(article, str(article_path))
        assert article_path.exists()
        article_path.unlink()
    with pytest.raises(RuntimeError):
        article = await download_article_with_playwright("nytimes.com")


def _articles(result):
    return result.structured_content.get("result", [])


def test_decode_url_preserves_direct_publisher_url():
    url = "https://example.com/news/story"

    assert news.decode_url(url) == url


def test_decode_url_falls_back_when_google_news_decode_fails(monkeypatch):
    url = "https://news.google.com/rss/articles/example"
    monkeypatch.setattr(news, "gnewsdecoder", lambda _: {"status": False})

    assert news.decode_url(url) == url


async def test_browser_manager_shuts_down_after_final_context(monkeypatch):
    shutdown_calls = []

    async def fake_shutdown(cls):
        shutdown_calls.append(True)

    monkeypatch.setattr(BrowserManager, "_shutdown", classmethod(fake_shutdown))

    async with BrowserManager():
        async with BrowserManager():
            assert BrowserManager._class_contexts == 2
        assert BrowserManager._class_contexts == 1
        assert shutdown_calls == []

    assert BrowserManager._class_contexts == 0
    assert shutdown_calls == [True]


async def test_browser_manager_waits_for_shutdown_before_reentering(monkeypatch):
    shutdown_started = asyncio.Event()
    finish_shutdown = asyncio.Event()
    entry_attempted = asyncio.Event()
    entered = asyncio.Event()

    async def fake_shutdown(cls):
        shutdown_started.set()
        await finish_shutdown.wait()

    monkeypatch.setattr(BrowserManager, "_shutdown", classmethod(fake_shutdown))

    manager = BrowserManager()
    await manager.__aenter__()
    exit_task = asyncio.create_task(manager.__aexit__(None, None, None))
    await shutdown_started.wait()

    async def enter_next_context():
        entry_attempted.set()
        async with BrowserManager():
            entered.set()

    enter_task = asyncio.create_task(enter_next_context())
    try:
        await entry_attempted.wait()
        assert not entered.is_set()
    finally:
        finish_shutdown.set()
        await asyncio.gather(exit_task, enter_task)

    assert entered.is_set()
    assert BrowserManager._class_contexts == 0


def test_scraper_fallback_has_timeout(monkeypatch):
    seen_timeouts = []

    def fail_newspaper_article(*args, **kwargs):
        raise RuntimeError("download failed")

    class Response:
        status_code = 500

    def fake_get(url, timeout):
        seen_timeouts.append(timeout)
        return Response()

    monkeypatch.setattr(news.newspaper, "article", fail_newspaper_article)
    monkeypatch.setattr(news.scraper, "get", fake_get)

    assert news.download_article_with_scraper("https://example.com/news") is None
    assert seen_timeouts == [30]


async def test_playwright_navigation_has_timeout(monkeypatch):
    seen_timeouts = []

    class Page:
        async def goto(self, *args, **kwargs):
            seen_timeouts.append(kwargs["timeout"])
            raise RuntimeError("navigation failed")

    class Context:
        async def new_page(self):
            return Page()

    @asynccontextmanager
    async def fake_browser_context():
        yield Context()

    monkeypatch.setattr(BrowserManager, "browser_context", classmethod(lambda cls: fake_browser_context()))

    assert await download_article_with_playwright("https://example.com/news") is None
    assert seen_timeouts == [30_000]


async def test_news_tools_reject_unbounded_max_results(mcp_server):
    async with Client(mcp_server) as client:
        with pytest.raises(ToolError, match="less than or equal to 25"):
            await client.call_tool("get_top_news", {"max_results": 26})


async def test_browser_startup_failure_raises_runtime_error(monkeypatch):
    BrowserManager._browser = None
    BrowserManager._playwright = None

    class FakePlaywright:
        async def start(self):
            raise OSError("chromium missing")

    monkeypatch.setattr(news, "async_playwright", lambda: FakePlaywright())

    with pytest.raises(RuntimeError, match="Browser startup failed"):
        await BrowserManager._get_browser()


async def test_get_news_by_keyword(mcp_server):
    async with Client(mcp_server) as client:
        params = {"keyword": "AI", "period": 3, "max_results": 2}
        result = await client.call_tool("get_news_by_keyword", params)
        articles = _articles(result)
        assert isinstance(articles, list)
        assert len(articles) <= 2
        for article in articles:
            assert "title" in article
            assert "url" in article


async def test_get_news_by_location(mcp_server):
    async with Client(mcp_server) as client:
        params = {"location": "California", "period": 3, "max_results": 2}
        result = await client.call_tool("get_news_by_location", params)
        articles = _articles(result)
        assert isinstance(articles, list)
        assert len(articles) <= 2
        for article in articles:
            assert "title" in article
            assert "url" in article
        params = {"location": "Mars", "period": 3, "max_results": 2}
        result = await client.call_tool("get_news_by_location", params)
        assert _articles(result) == []


async def test_get_news_by_topic(mcp_server):
    async with Client(mcp_server) as client:
        params = {"topic": "TECHNOLOGY", "period": 3, "max_results": 2}
        result = await client.call_tool("get_news_by_topic", params)
        articles = _articles(result)
        assert isinstance(articles, list)
        assert len(articles) <= 2
        for article in articles:
            assert "title" in article
            assert "url" in article
        params = {"topic": "CATS", "period": 3, "max_results": 2}
        result = await client.call_tool("get_news_by_topic", params)
        assert _articles(result) == []


async def test_get_top_news(mcp_server):
    async with Client(mcp_server) as client:
        params = {"period": 2, "max_results": 2}
        result = await client.call_tool("get_top_news", params)
        articles = _articles(result)
        assert isinstance(articles, list)
        assert len(articles) <= 2
        for article in articles:
            assert "title" in article
            assert "url" in article


async def test_get_trending_terms(mcp_server):
    async with Client(mcp_server) as client:
        params = {"geo": "US", "full_data": True}
        result = await client.call_tool("get_trending_terms", params)
        for item in _articles(result):
            assert "keyword" in item
            assert "volume" in item
            assert "link" in item
        params = {"geo": "US", "full_data": False}
        result = await client.call_tool("get_trending_terms", params)
        for item in _articles(result):
            assert "keyword" in item
            assert "volume" in item
        params = {"geo": "USA", "full_data": True}
        result = await client.call_tool("get_trending_terms", params)
        assert _articles(result) == []
