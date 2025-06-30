from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_context
from pydantic import BaseModel, Field
from typing import Optional
from google_news_trends_mcp import news
from typing import Annotated
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware


class ArticleOut(BaseModel):
    read_more_link: Annotated[
        Optional[str], Field(description="Link to read more about the article.")
    ] = None
    language: Annotated[
        Optional[str], Field(description="Language code of the article.")
    ] = None
    meta_img: Annotated[Optional[str], Field(description="Meta image URL.")] = None
    movies: Annotated[
        Optional[list[str]], Field(description="List of movie URLs or IDs.")
    ] = None
    meta_favicon: Annotated[
        Optional[str], Field(description="Favicon URL from meta data.")
    ] = None
    meta_site_name: Annotated[
        Optional[str], Field(description="Site name from meta data.")
    ] = None
    title: Annotated[str, Field(description="Title of the article.")]
    authors: Annotated[Optional[list[str]], Field(description="list of authors.")] = (
        None
    )
    publish_date: Annotated[
        Optional[str], Field(description="Publish date in ISO format.")
    ] = None
    top_image: Annotated[Optional[str], Field(description="URL of the top image.")] = (
        None
    )
    images: Annotated[Optional[list[str]], Field(description="list of image URLs.")] = (
        None
    )
    text: Annotated[str, Field(description="Full text of the article.")]
    url: Annotated[str, Field(description="Original article URL.")]
    summary: Annotated[Optional[str], Field(description="Summary of the article.")] = (
        None
    )
    keywords: Annotated[
        Optional[list[str]], Field(description="Extracted keywords.")
    ] = None
    tags: Annotated[Optional[list[str]], Field(description="Tags for the article.")] = (
        None
    )
    meta_keywords: Annotated[
        Optional[list[str]], Field(description="Meta keywords from the article.")
    ] = None
    meta_description: Annotated[
        Optional[str], Field(description="Meta description from the article.")
    ] = None
    canonical_link: Annotated[
        Optional[str], Field(description="Canonical link for the article.")
    ] = None
    meta_data: Annotated[
        Optional[dict[str, str | int]], Field(description="Meta data dictionary.")
    ] = None
    meta_lang: Annotated[
        Optional[str], Field(description="Language of the article.")
    ] = None
    source_url: Annotated[
        Optional[str], Field(description="Source URL if different from original.")
    ] = None


class TrendingTermArticleOut(BaseModel):
    title: Annotated[str, Field(description="Article title.")] = ""
    url: Annotated[str, Field(description="Article URL.")] = ""
    source: Annotated[Optional[str], Field(description="News source name.")] = None
    picture: Annotated[Optional[str], Field(description="URL to article image.")] = None
    time: Annotated[
        Optional[str | int], Field(description="Publication time or timestamp.")
    ] = None
    snippet: Annotated[Optional[str], Field(description="Article preview text.")] = None


class TrendingTermOut(BaseModel):
    keyword: Annotated[str, Field(description="Trending keyword.")]
    volume: Annotated[Optional[int], Field(description="Search volume.")] = None
    geo: Annotated[Optional[str], Field(description="Geographic location code.")] = None
    started_timestamp: Annotated[
        Optional[list],
        Field(
            description="When the trend started (year, month, day, hour, minute, second)."
        ),
    ] = None
    ended_timestamp: Annotated[
        Optional[tuple[int, int]],
        Field(
            description="When the trend ended (year, month, day, hour, minute, second)."
        ),
    ] = None
    volume_growth_pct: Annotated[
        Optional[float], Field(description="Percentage growth in search volume.")
    ] = None
    trend_keywords: Annotated[
        Optional[list[str]], Field(description="Related keywords.")
    ] = None
    topics: Annotated[
        Optional[list[str | int]], Field(description="Related topics.")
    ] = None
    news: Annotated[
        Optional[list[TrendingTermArticleOut]],
        Field(description="Related news articles."),
    ] = None
    news_tokens: Annotated[
        Optional[list], Field(description="Associated news tokens.")
    ] = None
    normalized_keyword: Annotated[
        Optional[str], Field(description="Normalized form of the keyword.")
    ] = None


mcp = FastMCP(
    name="google-news-trends",
    instructions="This server provides tools to search, analyze, and summarize Google News articles and Google Trends",
    on_duplicate_tools="replace",
)

mcp.add_middleware(ErrorHandlingMiddleware())  # Handle errors first
mcp.add_middleware(RateLimitingMiddleware(max_requests_per_second=50))
mcp.add_middleware(TimingMiddleware())  # Time actual execution
mcp.add_middleware(LoggingMiddleware())  # Log everything


@mcp.tool(
    description=news.get_news_by_keyword.__doc__,
    tags={"news", "articles", "keyword"},
)
async def get_news_by_keyword(
    keyword: Annotated[str, Field(description="Search term to find articles.")],
    period: Annotated[
        int, Field(description="Number of days to look back for articles.", ge=1)
    ] = 7,
    max_results: Annotated[
        int, Field(description="Maximum number of results to return.", ge=1)
    ] = 10,
    nlp: Annotated[
        bool, Field(description="Whether to perform NLP on the articles.")
    ] = True,
) -> list[ArticleOut]:
    articles = await news.get_news_by_keyword(
        keyword=keyword,
        period=period,
        max_results=max_results,
        nlp=nlp,
    )
    return [ArticleOut(**a.to_json(False)) for a in articles]


@mcp.tool(
    description=news.get_news_by_location.__doc__,
    tags={"news", "articles", "location"},
)
async def get_news_by_location(
    location: Annotated[str, Field(description="Name of city/state/country.")],
    period: Annotated[
        int, Field(description="Number of days to look back for articles.", ge=1)
    ] = 7,
    max_results: Annotated[
        int, Field(description="Maximum number of results to return.", ge=1)
    ] = 10,
    nlp: Annotated[
        bool, Field(description="Whether to perform NLP on the articles.")
    ] = True,
) -> list[ArticleOut]:
    articles = await news.get_news_by_location(
        location=location,
        period=period,
        max_results=max_results,
        nlp=nlp,
    )
    return [ArticleOut(**a.to_json(False)) for a in articles]


@mcp.tool(
    description=news.get_news_by_topic.__doc__, tags={"news", "articles", "topic"}
)
async def get_news_by_topic(
    topic: Annotated[str, Field(description="Topic to search for articles.")],
    period: Annotated[
        int, Field(description="Number of days to look back for articles.", ge=1)
    ] = 7,
    max_results: Annotated[
        int, Field(description="Maximum number of results to return.", ge=1)
    ] = 10,
    nlp: Annotated[
        bool, Field(description="Whether to perform NLP on the articles.")
    ] = True,
) -> list[ArticleOut]:
    articles = await news.get_news_by_topic(
        topic=topic,
        period=period,
        max_results=max_results,
        nlp=nlp,
    )
    return [ArticleOut(**a.to_json(False)) for a in articles]


@mcp.tool(description=news.get_top_news.__doc__, tags={"news", "articles", "top"})
async def get_top_news(
    period: Annotated[
        int, Field(description="Number of days to look back for top articles.", ge=1)
    ] = 3,
    max_results: Annotated[
        int, Field(description="Maximum number of results to return.", ge=1)
    ] = 10,
    nlp: Annotated[
        bool, Field(description="Whether to perform NLP on the articles.")
    ] = True,
) -> list[ArticleOut]:
    articles = await news.get_top_news(
        period=period,
        max_results=max_results,
        nlp=nlp,
    )
    return [ArticleOut(**a.to_json(False)) for a in articles]


@mcp.tool(
    description=news.get_trending_terms.__doc__, tags={"trends", "google", "trending"}
)
async def get_trending_terms(
    geo: Annotated[
        str, Field(description="Country code, e.g. 'US', 'GB', 'IN', etc.")
    ] = "US",
    full_data: Annotated[
        bool,
        Field(
            description="Return full data for each trend. Should be False for most use cases."
        ),
    ] = False,
    max_results: Annotated[
        int, Field(description="Maximum number of results to return.", ge=1)
    ] = 100,
) -> list[TrendingTermOut]:
    trends = await news.get_trending_terms(
        geo=geo, full_data=full_data, max_results=max_results
    )
    if not full_data:
        # Only return keyword and volume fields
        return [
            TrendingTermOut(keyword=tt["keyword"], volume=tt["volume"]) for tt in trends
        ]
    else:
        # Assume each tt is a TrendingTerm object
        return [TrendingTermOut(**tt.__dict__) for tt in trends]

def main():
    mcp.run()
