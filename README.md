# Google News Trends MCP

An MCP server to access Google News and Google Trends.  Does not rely on any paid APIs.  

## Features

- Search Google News articles based on keyword, location, topic
- Get top news stories from Google News
- Google Trends keywords base on location
- Optional LLM Sampling and NLP to summarize articles and extract keywords

## Installation

### Using uv/uvx (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *google-news-trends-mcp*.

### Using PIP

```bash
pip install google-news-trends-mcp
```
After installation, you can run it as a script using:

```bash
python -m google_news_trends_mcp
```

## Configuration

### Configure for Claude.app

Add to your Claude settings:

<details>
<summary>Using uvx</summary>

```json
{
  "mcpServers": {
    "google-news-trends": {
      "command": "uvx",
      "args": ["google-news-trends-mcp@latest"]
    }
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
{
  "mcpServers": {
    "google-news-trends": {
      "command": "python",
      "args": ["-m", "google_news_trends_mcp"]
    }
  }
}
```
</details>

### Configure for VS Code

<details>
<summary>Using uvx</summary>

```json
{
  "mcp": {
    "servers": {
      "google-news-trends": {
        "command": "uvx",
        "args": ["google-news-trends-mcp@latest"]
      }
    }
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
{
  "mcp": {
    "servers": {
      "google-news-trends": {
        "command": "python",
        "args": ["-m", "google_news_trends_mcp"]
      }
    }
  }
}
```
</details>


## Tools

The following MCP tools are available:

| Tool Name                | Description                                                        |
|--------------------------|--------------------------------------------------------------------|
| **get_news_by_keyword**  | Search for news using specific keywords.                           |
| **get_news_by_location** | Retrieve news relevant to a particular location.                   |
| **get_news_by_topic**    | Get news based on a chosen topic.                                  |
| **get_top_news**         | Fetch the top news stories from Google News.                       |
| **get_trending_keywords**| Return trending keywords from Google Trends for a specified location.|

All of the news related tools have an option to summarize the text of the article using NLP (nltk)


## CLI
All tools can be accessed from the command line using `uv`

```bash
uv run google-news-trends
Usage: google-news-trends [OPTIONS] COMMAND [ARGS]...

  Find and download news articles using Google News.

Options:
  --help  Show this message and exit.

Commands:
  keyword   Find articles by keyword using Google News.
  location  Find articles by location using Google News.
  top       Get top news stories from Google News.
  topic     Find articles by topic using Google News.
  trending  Returns google trends for a specific geo location.
```

## Debugging

```bash
npx @modelcontextprotocol/inspector uvx google-news-trends-mcp
```

To run from within locally installed project

```bash
cd path/to/google/news/tends/mcp
npx @modelcontextprotocol/inspector uv run google-news-trends-mcp
```

## Testing

```bash
cd path/to/google/news/tends/mcp
python -m pytest
```