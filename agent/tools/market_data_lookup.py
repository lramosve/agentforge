"""Tool: Fetch current market data for symbols."""

import time

from langchain_core.tools import tool

from agent.ghostfolio_client import GhostfolioClient


@tool
async def market_data_lookup(
    symbol: str,
    data_source: str = "YAHOO",
) -> dict:
    """Look up current market data for a financial instrument by its ticker symbol.
    Use this when the user asks about a specific stock, ETF, cryptocurrency, or
    other asset's current price or details.

    Args:
        symbol: The ticker symbol to look up (e.g., 'AAPL', 'VOO', 'BTC-USD').
        data_source: The data source to use. Options: 'YAHOO', 'COINGECKO',
                     'ALPHA_VANTAGE', 'FINANCIAL_MODELING_PREP'. Defaults to 'YAHOO'.
    """
    start = time.time()
    client = GhostfolioClient()

    valid_sources = {
        "YAHOO", "COINGECKO", "ALPHA_VANTAGE",
        "FINANCIAL_MODELING_PREP", "MANUAL",
    }
    if data_source not in valid_sources:
        data_source = "YAHOO"

    try:
        data = await client.get_symbol(data_source, symbol.upper())

        return {
            "status": "success",
            "data": {
                "symbol": symbol.upper(),
                "data_source": data_source,
                "name": data.get("name", ""),
                "currency": data.get("currency", ""),
                "market_price": data.get("marketPrice", 0),
                "asset_class": data.get("assetClass", ""),
                "asset_sub_class": data.get("assetSubClass", ""),
                "sectors": data.get("sectors", []),
                "countries": data.get("countries", []),
            },
            "message": f"{symbol.upper()}: {data.get('marketPrice', 'N/A')} {data.get('currency', '')}",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to look up {symbol}: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
