"""
# news.py
This module provides functions to find and download news articles using Google News.
It allows searching for articles by keyword, location, or topic, and can also retrieve google trending terms.
It uses the `gnews` library to search for news articles and trendspy to get Google Trends data.
It will fallback to using Playwright for websites that are difficult to scrape with newspaper4k or cloudscraper.
"""

import re
import json
import time
import asyncio
from gnews import GNews
import newspaper  # newspaper4k
from googlenewsdecoder import gnewsdecoder
import cloudscraper
from playwright.async_api import async_playwright, Browser
from trendspy import Trends, TrendKeyword
import click
from typing import Optional
import atexit
from contextlib import asynccontextmanager

tr = Trends()

scraper = cloudscraper.create_scraper(
    # Challenge handling
    interpreter="js2py",  # Best compatibility for v3 challenges
    delay=5,  # Extra time for complex challenges
    # Stealth mode
    # enable_stealth=True,
    # stealth_options={
    #     'min_delay': 2.0,
    #     'max_delay': 6.0,
    #     'human_like_delays': True,
    #     'randomize_headers': True,
    #     'browser_quirks': True
    # },
    # Browser emulation
    browser="chrome",
    # Debug mode
    debug=False,
)

google_news = GNews(
    language="en",
    exclude_websites=["mensjournal.com"],
)

playwright = None
browser: Browser = None


async def startup_browser():
    global playwright, browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)


@atexit.register
def shutdown_browser():
    if browser:
        asyncio.run(browser.close())
    if playwright:
        asyncio.run(playwright.stop())


async def get_browser() -> Browser:
    global browser
    if browser is None:
        await startup_browser()
    return browser


@asynccontextmanager
async def browser_context():
    context = await (await get_browser()).new_context()
    try:
        yield context
    finally:
        print("Closing browser context...")
        await context.close()


async def download_article_with_playwright(url) -> newspaper.Article | None:
    """
    Download an article using Playwright to handle complex websites (async).
    """
    try:
        async with browser_context() as context:
            # context = await new_context()
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(2)  # Wait for the page to load completely
            content = await page.content()
            # await context.close()
            article = newspaper.article(url, input_html=content, language="en")
            return article
    except Exception as e:
        print(f"Error downloading article with Playwright from {url}\n {e.args}")
        return None


async def download_article(url: str, nlp: bool = True) -> newspaper.Article | None:
    """
    Download an article from a given URL using newspaper4k and cloudscraper (async).
    """
    article = None
    if url.startswith("https://news.google.com/rss/"):
        try:
            decoded_url = gnewsdecoder(url)
            if decoded_url.get("status"):
                url = decoded_url["decoded_url"]
            else:
                print("Failed to decode Google News RSS link:")
                return None
        except Exception as err:
            print(f"Error while decoding url {url}\n {err.args}")
    try:
        article = newspaper.article(url)
    except Exception as e:
        print(f"Error downloading article with newspaper from {url}\n {e.args}")
        try:
            # Retry with cloudscraper
            response = scraper.get(url)
            if response.status_code < 400:
                article = newspaper.article(url, input_html=response.text)
            else:
                print(
                    f"Failed to download article with cloudscraper from {url}, status code: {response.status_code}"
                )
        except Exception as e:
            print(f"Error downloading article with cloudscraper from {url}\n {e.args}")

    try:
        if article is None:
            # If newspaper failed, try downloading with Playwright
            print(f"Retrying with Playwright for {url}")
            article = await download_article_with_playwright(url)
        article.parse()
        if nlp:
            article.nlp()
        if article.publish_date:
            article.publish_date = article.publish_date.isoformat()
    except Exception as e:
        print(f"Error parsing article from {url}\n {e.args}")
        return None
    return article


async def process_gnews_articles(
    gnews_articles: list[dict], nlp: bool = True
) -> list["newspaper.Article"]:
    """
    Process a list of Google News articles and download them (async).
    """
    articles = []
    for gnews_article in gnews_articles:
        article = await download_article(gnews_article["url"], nlp=nlp)
        if article is None or not article.text:
            print(f"Failed to download article from {gnews_article['url']}:\n{article}")
            continue
        articles.append(article)
    return articles


async def get_news_by_keyword(
    keyword: str, period=7, max_results: int = 10, nlp: bool = True
) -> list[newspaper.Article]:
    """
    Find articles by keyword using Google News.
    keyword: is the search term to find articles.
    period: is the number of days to look back for articles.
    max_results: is the maximum number of results to return.
    nlp: If True, will perform NLP on the articles to extract keywords and summary.
    Returns:
        list[newspaper.Article]: A list of newspaper.Article objects containing the articles.
    """
    google_news.period = f"{period}d"
    google_news.max_results = max_results
    gnews_articles = google_news.get_news(keyword)
    if not gnews_articles:
        print(f"No articles found for keyword '{keyword}' in the last {period} days.")
        return []
    return await process_gnews_articles(gnews_articles, nlp=nlp)


async def get_top_news(
    period: int = 3, max_results: int = 10, nlp: bool = True
) -> list["newspaper.Article"]:
    """
    Get top news stories from Google News.
    period: is the number of days to look back for top articles.
    max_results: is the maximum number of results to return.
    nlp: If True, will perform NLP on the articles to extract keywords and summary.
    Returns:
        list[newspaper.Article]: A list of newspaper.Article objects containing the top news articles.
    """
    google_news.period = f"{period}d"
    google_news.max_results = max_results
    gnews_articles = google_news.get_top_news()
    if not gnews_articles:
        print("No top news articles found.")
        return []
    return await process_gnews_articles(gnews_articles, nlp=nlp)


async def get_news_by_location(
    location: str, period=7, max_results: int = 10, nlp: bool = True
) -> list[newspaper.Article]:
    """Find articles by location using Google News.
    location: is the name of city/state/country
    period: is the number of days to look back for articles.
    max_results: is the maximum number of results to return.
    nlp: If True, will perform NLP on the articles to extract keywords and summary.
    Returns:
        list[newspaper.Article]: A list of newspaper.Article objects containing the articles for the specified location
    """
    google_news.period = f"{period}d"
    google_news.max_results = max_results
    gnews_articles = google_news.get_news_by_location(location)
    if not gnews_articles:
        print(f"No articles found for location '{location}' in the last {period} days.")
        return []
    return await process_gnews_articles(gnews_articles, nlp=nlp)


async def get_news_by_topic(
    topic: str, period=7, max_results: int = 10, nlp: bool = True
) -> list[newspaper.Article]:
    """Find articles by topic using Google News.
    topic is one of
    WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH,
    POLITICS, CELEBRITIES, TV, MUSIC, MOVIES, THEATER, SOCCER, CYCLING, MOTOR SPORTS,
    TENNIS, COMBAT SPORTS, BASKETBALL, BASEBALL, FOOTBALL, SPORTS BETTING, WATER SPORTS,
    HOCKEY, GOLF, CRICKET, RUGBY, ECONOMY, PERSONAL FINANCE, FINANCE, DIGITAL CURRENCIES,
    MOBILE, ENERGY, GAMING, INTERNET SECURITY, GADGETS, VIRTUAL REALITY, ROBOTICS, NUTRITION,
    PUBLIC HEALTH, MENTAL HEALTH, MEDICINE, SPACE, WILDLIFE, ENVIRONMENT, NEUROSCIENCE, PHYSICS,
    GEOLOGY, PALEONTOLOGY, SOCIAL SCIENCES, EDUCATION, JOBS, ONLINE EDUCATION, HIGHER EDUCATION,
    VEHICLES, ARTS-DESIGN, BEAUTY, FOOD, TRAVEL, SHOPPING, HOME, OUTDOORS, FASHION.
    period: is the number of days to look back for articles.
    max_results: is the maximum number of results to return.
    nlp: If True, will perform NLP on the articles to extract keywords and summary.
    Returns:
        list[newspaper.Article]: A list of newspaper.Article objects containing the articles for the specified topic
    """
    google_news.period = f"{period}d"
    google_news.max_results = max_results
    gnews_articles = google_news.get_news_by_topic(topic)
    if not gnews_articles:
        print(f"No articles found for topic '{topic}' in the last {period} days.")
        return []
    return await process_gnews_articles(gnews_articles, nlp=nlp)


async def get_trending_terms(
    geo: str = "US", full_data: bool = False, max_results: int = 100
) -> list[tuple[str, int]] | list[TrendKeyword]:
    """
    Returns google trends for a specific geo location.
    Default is US.
    geo: is the country code, e.g. 'US', 'GB', 'IN', etc.
    full_data: if True, returns full data for each trend, otherwise returns only the trend and volume.
    max_results: is the maximum number of results to return, default is 100.
    Returns:
        list[tuple[str, int]]: A list of tuples containing the trend keyword and its volume.
        If full_data is True, each tuple will also contain additional data such as related queries and trend type.
    """
    try:
        trends = list(tr.trending_now(geo=geo))
        trends = list(sorted(trends, key=lambda tt: tt.volume, reverse=True))[
            :max_results
        ]
        if not full_data:
            return [(trend.keyword, trend.volume) for trend in trends]
        return trends
    except Exception as e:
        print(f"Error fetching trending terms: {e}")
        return []


def save_article_to_json(article: newspaper.Article, filename: str = "") -> None:
    def sanitize_filename(title: str) -> str:
        """
        # save Article to json file
        # filename is based on the article title
        # if the title is too long, it will be truncated to 50 characters
        # and replaced with underscores if it contains any special characters
        """
        # Replace special characters and spaces with underscores, then truncate to 50 characters
        sanitized_title = re.sub(r'[\\/*?:"<>|\s]', "_", title)[:50]
        return sanitized_title + ".json"

    """
    Save an article to a JSON file.
    """
    article_data = {
        "title": article.title,
        "authors": article.authors,
        "publish_date": str(article.publish_date) if article.publish_date else None,
        "top_image": article.top_image,
        "images": article.images,
        "text": article.text,
        "url": article.original_url,
        "summary": article.summary,
        "keywords": article.keywords,
        "keyword_scores": article.keyword_scores,
        "tags": article.tags,
        "meta_keywords": article.meta_keywords,
        "meta_description": article.meta_description,
        "canonical_link": article.canonical_link,
        "meta_data": article.meta_data,
        "meta_lang": article.meta_lang,
        "source_url": article.source_url,
    }

    if not filename:
        # Use the article title to create a filename
        filename = sanitize_filename(article.title)
    else:
        # Ensure the filename ends with .json
        if not filename.endswith(".json"):
            filename += ".json"
    with open(filename, "w") as f:
        json.dump(article_data, f, indent=4)
    print(f"Article saved to {filename}")
