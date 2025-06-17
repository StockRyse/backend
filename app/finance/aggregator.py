# Created by Ryan Polasky - 3/23/25
# All Rights Reserved

import requests
import yfinance as yf
import finnhub
import pandas as pd
from fastapi.security import api_key
from rich.progress import track
from rich import print as rprint
from datetime import datetime, timedelta
import os
import json

# Securely get the API key and handle if it's not set
try:
    finnhub_api_key = os.environ['FINNHUB_API_KEY']
    finnhub_client = finnhub.Client(api_key=finnhub_api_key)
except KeyError:
    rprint("[bold red]Error: The 'FINNHUB_API_KEY' environment variable is not set.[/bold red]")
    rprint("Please set it to your Finnhub API key.")
    exit()  # Exit the script if the key is not available


def get_historical_prices(ticker, period='max'):
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)

        # Get historical market data
        historical_data = stock.history(period=period)
        if historical_data.empty:
            rprint(f"[yellow]Warning: No historical data found for {ticker}. It may be an invalid ticker.[/yellow]")
            return []

        # Convert to list of dictionaries with date and closing price
        price_data = [
            {
                "date": index.strftime('%Y-%m-%d'),
                "price": float(row['Close'])
            }
            for index, row in historical_data.iterrows()
        ]
        return price_data

    except requests.exceptions.RequestException as e: # More specific network error
        rprint(f"[bold red]Network error fetching historical prices for {ticker}: {e}[/bold red]")
        return []
    except Exception as e: # A fallback for other unexpected errors
        rprint(f"[bold red]An unexpected error occurred for {ticker}: {e}[/bold red]")
        return []


def y_stock_lookup(ticker_symbol: str):
    # Try to get Yahoo Finance data on the ticker symbol
    data = yf.Ticker(ticker_symbol)

    # data.info is the dictionary we need to check
    data_dict = data.info

    # Check for a key that is likely to exist if the ticker is valid, like 'symbol'
    if not data_dict or 'symbol' not in data_dict:
        return {"error": f"No data found for ticker: {ticker_symbol}"}

    # Use .get() for safer dictionary access, providing a default value of None or "N/A"
    refined_market_cap = refine_market_cap(data_dict.get('marketCap'))

    refined_response = {
        "companyName": data_dict.get("shortName"),
        "tickerSymbol": data_dict.get("symbol"),
        "exchange": data_dict.get("exchange"),
        "sector": data_dict.get("sectorDisp"),
        "marketCap": refined_market_cap,
        "companyDescription": data_dict.get("longBusinessSummary"),
        "currentPrice": f"${round(data_dict.get('regularMarketPrice', 0), 2)}",
        "previousClosingPrice": f"${round(data_dict.get('previousClose', 0), 2)}",
        "openPrice": f"${round(data_dict.get('open', 0), 2)}",
        "dayHigh": f"${round(data_dict.get('dayHigh', 0), 2)}",
        "dayLow": f"${round(data_dict.get('dayLow', 0), 2)}",
        "yearRange": f"${round(data_dict.get('fiftyTwoWeekLow', 0), 2)} - ${round(data_dict.get('fiftyTwoWeekHigh', 0), 2)}",
        "historicalPrices": get_historical_prices(ticker_symbol)
    }
    return refined_response


def fetch_and_prepare_all_tickers(cache_duration_days=1):
    """
    Fetch tickers and cache them. The cache is refreshed if it's older
    than cache_duration_days.
    """
    tickers_file = 'tickers.json'

    # Check if the file exists and how old it is
    if os.path.exists(tickers_file):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(tickers_file))
        if datetime.now() - file_mod_time < timedelta(days=cache_duration_days):
            rprint("[green]Loading tickers from local cache.[/green]")
            with open(tickers_file, 'r') as f:
                return json.load(f)

    # If cache is old or doesn't exist, fetch from API
    rprint("[yellow]Cache is old or missing. Fetching fresh tickers from Finnhub...[/yellow]")
    exchanges = ['US']  # Can be expanded, e.g., ['US', 'L'] for London
    all_tickers = []

    for exchange in track(exchanges, description="Fetching tickers for exchanges..."):
        try:
            symbols = finnhub_client.stock_symbols(exchange)
            for ticker in symbols:  # No need for a second progress bar here for speed
                all_tickers.append({
                    "ticker_symbol": ticker.get("displaySymbol") or ticker.get("symbol"),
                    "exchange": exchange,
                    "company_name": ticker.get("description"),
                })
        except Exception as e:
            rprint(f"[bold red]Error fetching tickers for {exchange}: {e}[/bold red]")

    # Write the fresh data to the cache file
    with open(tickers_file, 'w') as f:
        json.dump(all_tickers, f, indent=4)  # Use indent for readability

    return all_tickers


def refine_market_cap(market_cap):
    try:
        market_cap = int(market_cap)
    except ValueError:
        return "Invalid market cap format"

    trillion = 1_000_000_000_000
    billion = 1_000_000_000
    million = 1_000_000

    if market_cap >= trillion:
        refined_value = round(market_cap / trillion, 2)
        return f"${refined_value}T"
    elif market_cap >= billion:
        refined_value = round(market_cap / billion, 2)
        return f"${refined_value}B"
    elif market_cap >= million:
        refined_value = round(market_cap / million, 2)
        return f"${refined_value}M"
    else:
        return f"${market_cap}"


if __name__ == "__main__":
    rprint("[blue]attempting to load tickers...")
    fetch_and_prepare_all_tickers()
