"""Tool: Show upcoming ex-dividend dates for portfolio holdings."""

import asyncio
import time

from langchain_core.tools import tool

from agent.dividend_client import DividendClient
from agent.ghostfolio_client import GhostfolioClient


@tool
async def dividend_calendar(
    days_ahead: int = 90,
) -> dict:
    """Show upcoming ex-dividend dates for the user's portfolio holdings. Use this
    when the user asks about their next dividends, dividend calendar, or upcoming
    dividend payments.

    Args:
        days_ahead: How many days ahead to look for upcoming dividends (default 90).
    """
    start = time.time()

    try:
        # Fetch portfolio holdings from Ghostfolio
        gf = GhostfolioClient()
        holdings_data = await gf.get_portfolio_holdings()
        holdings = holdings_data.get("holdings", [])

        symbols = [
            h.get("symbol")
            for h in holdings
            if h.get("symbol")
        ]

        if not symbols:
            return {
                "status": "success",
                "data": {"upcoming": [], "count": 0, "next_payout_date": ""},
                "message": "No holdings found in your portfolio.",
                "execution_time": round(time.time() - start, 3),
            }

        # Fetch upcoming dividends via yfinance (synchronous, run in thread)
        client = DividendClient()
        upcoming = await asyncio.to_thread(client.get_upcoming_dividends, symbols)

        next_date = upcoming[0]["ex_date"] if upcoming else ""

        return {
            "status": "success",
            "data": {
                "upcoming": upcoming,
                "count": len(upcoming),
                "next_payout_date": next_date,
            },
            "message": f"{len(upcoming)} upcoming dividend(s) from your {len(symbols)} holdings",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to fetch dividend calendar: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
