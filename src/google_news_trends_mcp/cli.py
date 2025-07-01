import click
import asyncio
from google_news_trends_mcp.news import (
    get_news_by_keyword,
    get_news_by_location,
    get_news_by_topic,
    get_trending_terms,
    get_top_news,
    save_article_to_json,
)


@click.group()
def cli():
    pass


@cli.command(help=get_news_by_keyword.__doc__)
@click.argument("keyword")
@click.option("--period", type=int, default=7, help="Period in days to search for articles.")
@click.option(
    "--max-results",
    "max_results",
    type=int,
    default=10,
    help="Maximum number of results to return.",
)
@click.option("--no-nlp", is_flag=True, default=False, help="Disable NLP processing for articles.")
def keyword(keyword, period, max_results, no_nlp):
    articles = asyncio.run(get_news_by_keyword(keyword, period=period, max_results=max_results, nlp=not no_nlp))
    # asyncio.run(articles)  # Ensure the articles are fetched asynchronously
    print_articles(articles)


@cli.command(help=get_news_by_location.__doc__)
@click.argument("location")
@click.option("--period", type=int, default=7, help="Period in days to search for articles.")
@click.option(
    "--max-results",
    "max_results",
    type=int,
    default=10,
    help="Maximum number of results to return.",
)
@click.option("--no-nlp", is_flag=True, default=False, help="Disable NLP processing for articles.")
def location(location, period, max_results, no_nlp):
    articles = asyncio.run(get_news_by_location(location, period=period, max_results=max_results, nlp=not no_nlp))
    print_articles(articles)


@cli.command(help=get_news_by_topic.__doc__)
@click.argument("topic")
@click.option("--period", type=int, default=7, help="Period in days to search for articles.")
@click.option(
    "--max-results",
    "max_results",
    type=int,
    default=10,
    help="Maximum number of results to return.",
)
@click.option("--no-nlp", is_flag=True, default=False, help="Disable NLP processing for articles.")
def topic(topic, period, max_results, no_nlp):
    articles = asyncio.run(get_news_by_topic(topic, period=period, max_results=max_results, nlp=not no_nlp))
    print_articles(articles)


@cli.command(help=get_trending_terms.__doc__)
@click.option("--geo", type=str, default="US", help="Country code, e.g. 'US', 'GB', 'IN', etc.")
@click.option("--full-data", is_flag=True, default=False, help="Return full data for each trend.")
@click.option(
    "--max-results",
    "max_results",
    type=int,
    default=100,
    help="Maximum number of results to return.",
)
def trending(geo, full_data, max_results):
    trending_terms = asyncio.run(get_trending_terms(geo=geo, full_data=full_data, max_results=max_results))
    if trending_terms:
        print("Trending terms:")
        for term in trending_terms:
            if isinstance(term, dict):
                print(f"{term['keyword']:<40} - {term['volume']}")
            else:
                print(term)
    else:
        print("No trending terms found.")


@cli.command(help=get_top_news.__doc__)
@click.option("--period", type=int, default=3, help="Period in days to search for top articles.")
@click.option(
    "--max-results",
    "max_results",
    type=int,
    default=10,
    help="Maximum number of results to return.",
)
@click.option("--no-nlp", is_flag=True, default=False, help="Disable NLP processing for articles.")
def top(period, max_results, no_nlp):
    articles = asyncio.run(get_top_news(max_results=max_results, period=period, nlp=not no_nlp))
    print_articles(articles)
    print(f"Found {len(articles)} top articles.")


def print_articles(articles):
    for article in articles:
        print(f"Title: {article.title}")
        print(f"URL: {article.original_url}")
        print(f"Authors: {article.authors}")
        print(f"Publish Date: {article.publish_date}")
        print(f"Top Image: {article.top_image}")
        print(f"Summary: {article.summary}\n")
        save_article_to_json(article)


if __name__ == "__main__":
    cli()
