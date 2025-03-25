# Created by Ryan Polasky - 3/23/25
# All Rights Reserved

from fastapi import APIRouter
from app.finance import aggregator
import json

# Define the actual Fast API router for organization's sake
router = APIRouter(
    prefix="/stocks",
    tags=["stocks"]
)


@router.get("/query/{ticker_symbol}")
def search_stock(ticker_symbol: str) -> dict:
    return aggregator.y_stock_lookup(ticker_symbol)


@router.get("/query/all")
def get_all_tickers() -> dict:
    with open('tickers.json', 'r') as f:
        tickers = json.load(f)
    return tickers

# if __name__ == '__main__':
#     input_symb = input()
#     print(search_stock(input_symb))
