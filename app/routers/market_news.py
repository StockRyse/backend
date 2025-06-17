# Created by Ryan Polasky - 3/23/25
# All Rights Reserved

import json
import time
from fastapi import APIRouter
from gnews import GNews
from typing import List, Dict, Any, Optional

CACHE_FILE = "news_cache.json"
CACHE_TTL = 3600  # 1 hour in seconds
CACHE_DATA_KEY = "news_data"

router = APIRouter(
    prefix="/news",
    tags=["news"]
)


def load_cache() -> Dict[str, Any]:
    """Load the entire cache from a file."""
    try:
        with open(CACHE_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Return an empty dict if file not found or corrupt


def save_cache(data: Dict[str, Any]):
    """Save the entire cache to a file."""
    with open(CACHE_FILE, "w") as file:
        json.dump(data, file, indent=4)  # Use indent for readability


def get_cached_news(key: str) -> Optional[List[Dict[str, Any]]]:
    """
    Attempts to retrieve fresh news from the cache for a given key.
    Returns the news if it exists and is not expired, otherwise returns None.
    """
    cache = load_cache()
    if key in cache:
        cache_entry = cache[key]
        if time.time() - cache_entry.get("timestamp", 0) < CACHE_TTL:
            return cache_entry.get("data")
    return None


def cache_news(key: str, news_data: List[Dict[str, Any]]):
    """Saves news data for a specific key to the cache."""
    cache = load_cache()
    cache[key] = {
        "timestamp": time.time(),
        "data": news_data
    }
    save_cache(cache)


def _format_article(article: Dict[str, Any]) -> Dict[str, str]:
    """Formats a raw GNews article into a structured dictionary."""
    summary = article.get("description", "No summary available.")
    if summary and len(summary) > 200:
        summary = summary[:200].strip() + "..."

    # GNews publisher format can vary
    publisher = article.get('publisher')
    source_name = publisher.get('title') if isinstance(publisher, dict) else "Unknown Source"

    return {
        "title": article.get('title', 'Untitled Article'),
        "summary": summary,
        "source": source_name,
        "url": article.get('url', '#'),
        "date": article.get('published date', '')
    }


async def _fetch_and_cache_news(query: str, cache_key: str, limit: int) -> List[Dict[str, Any]]:
    """
    Generic function to fetch news from GNews, format it, and cache it.
    """
    google_news = GNews(language='en', country='US', max_results=limit)
    try:
        raw_articles = google_news.get_news(query)
        if not raw_articles:
            return []

        formatted_articles = [_format_article(article) for article in raw_articles]

        # Cache the newly fetched articles
        cache_news(cache_key, formatted_articles)

        return formatted_articles
    except Exception as e:
        print(f"Error fetching news for query '{query}': {e}")
        return [{"error": f"Failed to fetch news: {str(e)}"}]


@router.get("/query/general")
async def get_market_news(limit: int = 10):
    """
    Fetch general stock market news articles with caching.
    """
    cache_key = "general_market"
    # Try to get from cache first
    cached_news = get_cached_news(cache_key)
    if cached_news is not None:
        return cached_news[:limit]

    # If not in cache, fetch, cache, and return
    return await _fetch_and_cache_news('stock market', cache_key, limit)


@router.get("/query/{stock}")
async def get_stock_news(stock: str, limit: int = 5):
    """
    Fetch news articles for a specific stock ticker with caching.
    """
    stock_ticker = stock.upper()
    cache_key = stock_ticker

    # Try to get from cache first
    cached_news = get_cached_news(cache_key)
    if cached_news is not None:
        return cached_news[:limit]

    # If not in cache, fetch, cache, and return
    query = f"{stock_ticker} stock news"
    return await _fetch_and_cache_news(query, cache_key, limit)
