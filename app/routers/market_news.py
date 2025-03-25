import json
import time
from fastapi import APIRouter
from gnews import GNews

CACHE_FILE = "news_cache.json"
CACHE_TTL = 3600  # 1 hour in seconds
CACHE_DATA_KEY = "news_data"

router = APIRouter(
    prefix="/news",
    tags=["news"]
)


def load_cache():
    """Load cached news data from a file."""
    try:
        with open(CACHE_FILE, "r") as file:
            cache_data = json.load(file).get(CACHE_DATA_KEY, {})
            if time.time() - cache_data.get("timestamp", 0) < CACHE_TTL:
                return {CACHE_DATA_KEY: cache_data}  # Return with the key
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {CACHE_DATA_KEY: {}}  # Return with the key and an empty dictionary


def save_cache(data):
    """Save news data to cache."""
    with open(CACHE_FILE, "w") as file:
        json.dump({CACHE_DATA_KEY: data}, file)


@router.get("/query/general")
async def get_market_news(limit: int = 10):
    """
    Fetch stock market news articles using GoogleNews with caching.
    """
    cached_data = load_cache().get(CACHE_DATA_KEY, {})
    general_articles = cached_data.get("general",)
    if general_articles and cached_data.get("timestamp", 0) > time.time() - CACHE_TTL:
        return general_articles[:limit]

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

        cached_data["timestamp"] = time.time()
        cached_data["general"] = formatted_articles
        save_cache(cached_data)
        return formatted_articles
    except Exception as e:
        return {"error": f"Failed to fetch news: {str(e)}"}


@router.get("/query/{stock}")
async def get_stock_news(stock: str, limit: int = 5) -> list:
    """
    Fetch news articles related to a specific stock ticker symbol using GoogleNews with caching.
    """
    cached_data = load_cache().get(CACHE_DATA_KEY, {})
    stock_articles = cached_data.get('articles', {}).get(stock.upper(),)
    if stock_articles and cached_data.get("timestamp", 0) > time.time() - CACHE_TTL:
        return stock_articles[:limit]

    google_news = GNews(language='en', country='US', max_results=limit)
    try:
        articles_list = google_news.get_news(f"{stock.upper()} stock news")
        print(articles_list)

        if not articles_list:
            return []

        formatted_articles = []
        for article in articles_list:
            if isinstance(article, dict):  # Check if the article is a dictionary
                article_summary = article.get("description", "No summary available")
                if len(article_summary) >= 200:
                    article_summary = article_summary[:200] + "..."
                formatted_articles.append({
                    "title": article.get('title', 'Untitled Article'),
                    "summary": article_summary,
                    "source": article.get('publisher', {}).get('name', 'Unknown Source'),
                    "url": article.get('url', '#'),
                    "date": article.get('published date', '')
                })
            else:
                print(f"Warning: Skipping non-dictionary article: {article}")  # Optional: Log or handle non-dictionary items

        cached_data['articles'] = cached_data.get('articles', {})
        cached_data['articles'][stock.upper()] = formatted_articles
        cached_data["timestamp"] = time.time()
        save_cache(cached_data)
        return formatted_articles
    except Exception as e:
        return [{"error": f"Failed to fetch news for {stock}: {str(e)}"}]
