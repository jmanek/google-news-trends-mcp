import pytest
from fastmcp import Client
from google_news_trends_mcp.server import mcp
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
