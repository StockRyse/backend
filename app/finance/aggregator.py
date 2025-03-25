# Created by Ryan Polasky - 3/23/25
# All Rights Reserved

import yfinance as yf
import finnhub
import pandas as pd
from fastapi.security import api_key
from rich.progress import track
from rich import print as rprint
from datetime import datetime, timedelta
import os
import json

finnhub_api_key: str = os.environ.get('FINNHUB_API_KEY')
finnhub_client = finnhub.Client(api_key=api_key)

def get_historical_prices(ticker, period='max'):
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)

        # Get historical market data
        historical_data = stock.history(period=period)

        # Convert to list of dictionaries with date and closing price
        price_data = [
            {
                "date": index.strftime('%Y-%m-%d'),
                "price": float(row['Close'])
            }
            for index, row in historical_data.iterrows()
        ]

        return price_data

    except Exception as e:
        print(f"Error fetching historical prices for {ticker}: {e}")
        return []


def y_stock_lookup(ticker_symbol: str):
    # Try to get Yahoo Finance data on the ticker symbol
    data = yf.Ticker(ticker_symbol)

    # If proper data is returned,
    if data:
        data_dict = data.info

        refined_market_cap = refine_market_cap(data_dict['marketCap'])
        historical_data = get_historical_prices(ticker_symbol)

        refined_response = {
            "companyName": data_dict["shortName"],
            "tickerSymbol": data_dict["symbol"],
            "exchange": data_dict["exchange"],
            "sector": data_dict["sectorDisp"],
            "marketCap": refined_market_cap,
            "companyDescription": data_dict["longBusinessSummary"],
            "currentPrice": f"${round(data_dict['regularMarketPrice'], 2)}",
            "previousClosingPrice": f"${round(data_dict['previousClose'], 2)}",
            "openPrice": f"${round(data_dict['open'], 2)}",
            "dayHigh": f"${round(data_dict['dayHigh'], 2)}",
            "dayLow": f"${round(data_dict['dayLow'], 2)}",
            "yearRange": f"${round(data_dict['fiftyTwoWeekLow'], 2)} - ${round(data_dict['fiftyTwoWeekHigh'], 2)}",
            "historicalPrices": historical_data
        }
        return refined_response

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
