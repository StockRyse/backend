# Created by Ryan Polasky - 3/23/25
# All Rights Reserved

from fastapi import APIRouter
from app.finance import aggregator
import json

from fastapi import APIRouter, HTTPException
from app.finance import aggregator
import json
from typing import List, Dict


def _load_all_tickers() -> List[Dict]:
    """Loads the ticker data from the JSON file at startup."""
    try:
        with open('finance/tickers.json', 'r') as f:
            # Assuming the JSON file contains a list of ticker objects
            print("finance/tickers.json loaded successfully!")
            return json.load(f)
    except FileNotFoundError:
        # If the file doesn't exist, log an error & try to generate the JSON
        print("Warning: 'finance/tickers.json' not found. Attempting to generate...")
        aggregator.fetch_and_prepare_all_tickers()
        return []
    except json.JSONDecodeError:
        print("Error: Could not decode 'tickers.json'. The file might be corrupt.")
        return []


# Load the data into a variable when the module is imported
ALL_TICKERS_DATA = _load_all_tickers()

router = APIRouter(
    prefix="/stocks",
    tags=["stocks"]
)


@router.get("/query/{ticker_symbol}")
async def search_stock(ticker_symbol: str) -> Dict:
    """
    Search for a specific stock by its ticker symbol.
    Utilizes the y_stock_lookup function from the aggregator.
    """
    stock_data = aggregator.y_stock_lookup(ticker_symbol)

    # Handle cases where the backend function returns an error or no data
    if not stock_data or stock_data.get("error"):
        raise HTTPException(
            status_code=404,
            detail=f"Data not found for ticker: {ticker_symbol}"
        )

    return stock_data


@router.get("/query/all")
async def get_all_tickers() -> List[Dict]:
    """
    Retrieve a list of all available tickers.
    This data is loaded from cache at application startup.
    """
    return ALL_TICKERS_DATA
