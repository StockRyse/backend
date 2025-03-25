import json
import time
from fastapi import APIRouter
from gnews import GNews

CACHE_FILE = "news_cache.json"
CACHE_TTL = 3600  # 1 hour in seconds

router = APIRouter(
    prefix="/news",
    tags=["news"]
)


def load_cache():
    """Load cached news data from a file."""
    try:
        with open(CACHE_FILE, "r") as file:
            cache_data = json.load(file)
            if time.time() - cache_data.get("timestamp", 0) < CACHE_TTL:
                return cache_data.get("articles", {})  # Ensure it returns a dictionary
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}  # Return an empty dictionary instead of a list


def save_cache(articles):
    """Save news data to cache."""
    with open(CACHE_FILE, "w") as file:
        json.dump({"timestamp": time.time(), "articles": articles}, file)


@router.get("/general")
async def get_market_news(limit: int = 10):
    """
    Fetch stock market news articles using GoogleNews with caching.
    """
    cached_articles = load_cache().get("general", [])
    if cached_articles:
        return cached_articles[:limit]

    google_news = GNews(language='en', country='US', max_results=limit)
    try:
        articles = google_news.get_news('stock market')
        formatted_articles = []

        for article in articles:
            article_summary = article.get("description", "No summary available")
            if len(article_summary) >= 200:
                article_summary = article_summary[:200] + "..."
            formatted_articles.append({
                "title": article.get('title', 'Untitled Article'),
                "summary": article_summary,
                "source": article.get('publisher', 'Unknown Source'),
                "url": article.get('url', '#'),
                "date": article.get('published date', '')
            })

        cache_data = load_cache()
        cache_data["general"] = formatted_articles
        save_cache(cache_data)
        return formatted_articles
    except Exception as e:
        return {"error": f"Failed to fetch news: {str(e)}", "articles": []}


@router.get("/{stock}")
async def get_stock_news(stock: str, limit: int = 5):
    """
    Fetch news articles related to a specific stock ticker symbol using GoogleNews with caching.
    """
    cache_data: dict = load_cache()
    cached_articles = cache_data.get(stock.upper(), [])
    if cached_articles:
        return cached_articles[:limit]

    google_news = GNews(language='en', country='US', max_results=limit)
    try:
        articles = google_news.get_news(stock.upper())
        formatted_articles = []

        for article in articles:
            article_summary = article.get("description", "No summary available")
            if len(article_summary) >= 200:
                article_summary = article_summary[:200] + "..."
            formatted_articles.append({
                "title": article.get('title', 'Untitled Article'),
                "summary": article_summary,
                "source": article.get('publisher', 'Unknown Source'),
                "url": article.get('url', '#'),
                "date": article.get('published date', '')
            })

        cache_data[stock.upper()] = formatted_articles
        save_cache(cache_data)
        return formatted_articles
    except Exception as e:
        return {"error": f"Failed to fetch news for {stock}: {str(e)}", "articles": []}
