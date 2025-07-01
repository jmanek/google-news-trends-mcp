import pytest
from fastmcp import Client
from google_news_trends_mcp.server import mcp
import json


@pytest.fixture
def mcp_server():
    yield mcp


async def test_get_news_by_keyword(mcp_server):
    async with Client(mcp_server) as client:
        params = {"keyword": "AI", "period": 3, "max_results": 2}
        result = await client.call_tool("get_news_by_keyword", params)
        assert isinstance(result, list)
        assert len(result) <= 2
        for article in result:
            article = json.loads(article.text)
            if isinstance(article, list):
                article = article[0]  # Assuming articles are returned as JSON strings
            assert "title" in article
            assert "url" in article


async def test_get_news_by_location(mcp_server):
    async with Client(mcp_server) as client:
        params = {"location": "California", "period": 3, "max_results": 2}
        result = await client.call_tool("get_news_by_location", params)
        assert isinstance(result, list)
        assert len(result) <= 2
        for article in result:
            article = json.loads(article.text)
            if isinstance(article, list):
                article = article[0]
            assert "title" in article
            assert "url" in article


async def test_get_news_by_topic(mcp_server):
    async with Client(mcp_server) as client:
        params = {"topic": "TECHNOLOGY", "period": 3, "max_results": 2}
        result = await client.call_tool("get_news_by_topic", params)
        assert isinstance(result, list)
        assert len(result) <= 2
        for article in result:
            article = json.loads(article.text)
            if isinstance(article, list):
                article = article[0]
            assert "title" in article
            assert "url" in article


async def test_get_top_news(mcp_server):
    async with Client(mcp_server) as client:
        params = {"period": 2, "max_results": 2}
        result = await client.call_tool("get_top_news", params)
        assert isinstance(result, list)
        assert len(result) <= 2
        for article in result:
            article = json.loads(article.text)
            if isinstance(article, list):
                article = article[0]
            assert "title" in article
            assert "url" in article


async def test_get_trending_terms(mcp_server):
    async with Client(mcp_server) as client:
        params = {"max_results": 3, "geo": "US", "full_data": False}
        result = await client.call_tool("get_trending_terms", params)
        assert isinstance(result, list)
        assert len(result) <= 3
        for item in result:
            item = json.loads(item.text)[0]
            assert "keyword" in item
            assert "volume" in item
