# Created by Ryan Polasky - 3/23/25
# All Rights Reserved

import yfinance as yf
import finnhub
import pandas as pd
from fastapi.security import api_key
from rich.progress import track
from rich import print as rprint
import os
import json

finnhub_api_key: str = os.environ.get('FINNHUB_API_KEY')
finnhub_client = finnhub.Client(api_key=api_key)


def y_stock_lookup(ticker_symbol: str):
    # Try to get Yahoo Finance data on the ticker symbol
    data = yf.Ticker(ticker_symbol)

    # If proper data is returned,
    if data:
        return data.info

    else:  # If no data is returned,
        return "no data for you :("


def fetch_and_prepare_all_tickers():
    """
    Fetch tickers and prepare them as a list of dictionaries with a rich progress bar.
    """
    exchanges = ['US']
    all_tickers = []

    for exchange in track(exchanges, description="Fetching tickers for exchanges..."):
        try:
            symbols = finnhub_client.stock_symbols(exchange)
            for ticker in track(symbols, description=f"Processing tickers for {exchange}..."):
                all_tickers.append({
                    "ticker_symbol": ticker["displaySymbol"],
                    "exchange": exchange,
                    "company_name": ticker["description"],
                })
        except Exception as e:
            print(f"Error fetching tickers for {exchange}: {e}")

    with open('tickers.json', 'w') as f:
        json.dump(list(all_tickers), f)

    return list(all_tickers)


if __name__ == "__main__":
    rprint("[blue]attempting to load tickers...")
    fetch_and_prepare_all_tickers()
