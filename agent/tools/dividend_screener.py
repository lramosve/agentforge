"""Tool: Look up dividend information for any stock."""

import asyncio
import time

from langchain_core.tools import tool

from agent.dividend_client import DividendClient


@tool
async def dividend_screener(
    symbol: str = "",
    symbols: str = "",
) -> dict:
    """Look up dividend information for any stock: yield, payout ratio, ex-dividend
    date, history, and 5-year growth rate. Use this when the user asks about a
    specific stock's dividend details or wants to screen stocks for dividends.

    Args:
        symbol: A single ticker symbol (e.g. "JNJ").
        symbols: Comma-separated ticker symbols for multi-lookup (e.g. "JNJ,PG,KO").
    """
    start = time.time()
    client = DividendClient()

    tickers: list[str] = []
    if symbols:
        tickers = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    elif symbol:
        tickers = [symbol.strip().upper()]

    if not tickers:
        return {
            "status": "error",
            "data": None,
            "message": "Please provide at least one stock symbol.",
            "execution_time": round(time.time() - start, 3),
        }

    try:
        stocks: list[dict] = []
        for sym in tickers:
            info = await asyncio.to_thread(client.get_dividend_info, sym)
            history = await asyncio.to_thread(client.get_dividend_history, sym, 5)

            # Calculate 5-year dividend growth rate from history
            growth_rate = _calc_growth_rate(history)

            stocks.append({
                **info,
                "growth_rate_5yr": growth_rate,
                "history": history[-8:],  # last 8 payments
                "pays_dividend": info["annual_dividend"] > 0,
            })

        return {
            "status": "success",
            "data": {"stocks": stocks},
            "message": f"Dividend data for {len(stocks)} stock(s)",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to fetch dividend data: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }


def _calc_growth_rate(history: list[dict]) -> float:
    """Approximate compound annual growth rate from dividend history."""
    if len(history) < 8:
        return 0.0
    # Compare average of first 4 vs last 4 payments
    early = sum(d["amount"] for d in history[:4]) / 4
    recent = sum(d["amount"] for d in history[-4:]) / 4
    if early <= 0:
        return 0.0
    years = max(1, len(history) / 4)  # approximate years
    cagr = (recent / early) ** (1 / years) - 1
    return round(cagr * 100, 2)
