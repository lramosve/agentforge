"""Tool: Get portfolio performance metrics over a date range."""

import time

from langchain_core.tools import tool

from agent.ghostfolio_client import GhostfolioClient


@tool
async def portfolio_performance(
    date_range: str = "ytd",
) -> dict:
    """Get portfolio performance metrics including time-weighted return, max drawdown,
    and value change over a specified date range. Use this when the user asks about
    how their portfolio has performed, returns, gains/losses, or growth.

    Args:
        date_range: Time period to analyze. Options: '1d', '1w', '1m', '3m', '6m',
                    'ytd', '1y', '3y', '5y', 'max'. Defaults to 'ytd'.
    """
    start = time.time()
    client = GhostfolioClient()

    valid_ranges = {"1d", "1w", "1m", "3m", "6m", "ytd", "1y", "3y", "5y", "max"}
    if date_range not in valid_ranges:
        date_range = "ytd"

    try:
        perf = await client.get_portfolio_performance(date_range=date_range)
        chart = perf.get("chart", [])

        current_value = chart[-1].get("netWorth", 0) if chart else 0
        start_value = chart[0].get("netWorth", 0) if chart else 0

        performance_data = perf.get("performance", {})

        return {
            "status": "success",
            "data": {
                "date_range": date_range,
                "current_value": round(current_value, 2),
                "start_value": round(start_value, 2),
                "net_performance": performance_data.get("netPerformance", 0),
                "net_performance_pct": performance_data.get(
                    "netPerformancePercentage", 0
                ),
                "gross_performance": performance_data.get("grossPerformance", 0),
                "gross_performance_pct": performance_data.get(
                    "grossPerformancePercentage", 0
                ),
                "total_investment": performance_data.get("totalInvestment", 0),
                "fees": performance_data.get("fees", 0),
                "dividends": performance_data.get("dividends", 0),
                "data_points": len(chart),
            },
            "message": f"Performance over {date_range}: {performance_data.get('netPerformancePercentage', 0):.2%}",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to get performance: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
