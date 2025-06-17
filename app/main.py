# Created by Ryan Polasky - 3/23/25
# All Rights Reserved

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import stocks, market_news

# Designate the actual Fast API application
app = FastAPI(
    title="StockRyse API",
    description="A modern, high-performance API for fetching real-time and historical stock data and news.",
    version="1.0.0",
    contact={
        "name": "Ryan Polasky",
        "url": "https://www.ryanpolasky.com",
        "email": "ryanpolasky@hotmail.com",
    },
)

# Add CORS middleware to allow frontend requests
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the /stocks route, which will hold almost all paths
app.include_router(stocks.router)

# Include the /news route, which will have a few other paths
app.include_router(market_news.router)


# Define what happens when route path is accessed
@app.get('/')
async def root_path():
    return {"contents": "Thanks for checking out StockRyse :)"}


# Start the app with Uvicorn if the Python file is run
if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
