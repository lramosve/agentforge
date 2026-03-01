"""Tool: Project annual and monthly dividend income from current portfolio."""

import asyncio
import time

from langchain_core.tools import tool

from agent.database import get_goals
from agent.dividend_client import DividendClient
from agent.ghostfolio_client import GhostfolioClient


@tool
async def dividend_income_projection(
    include_growth: bool = False,
) -> dict:
    """Project annual and monthly dividend income from the user's current portfolio.
    Use this when the user asks about their dividend income, passive income,
    projected income, or how much their portfolio generates.

    Args:
        include_growth: Whether to include 5-year dividend growth projections (slower).
    """
    start = time.time()

    try:
        # Fetch portfolio holdings
        gf = GhostfolioClient()
        holdings_data = await gf.get_portfolio_holdings()
        raw_holdings = holdings_data.get("holdings", [])

        holdings = [
            {"symbol": h.get("symbol", ""), "value": h.get("valueInBaseCurrency", 0)}
            for h in raw_holdings
            if h.get("symbol") and h.get("valueInBaseCurrency", 0) > 0
        ]

        if not holdings:
            return {
                "status": "success",
                "data": {
                    "total_annual": 0,
                    "total_monthly": 0,
                    "by_holding": [],
                    "by_quarter": {},
                    "goal_progress": None,
                },
                "message": "No holdings with value found in your portfolio.",
                "execution_time": round(time.time() - start, 3),
            }

        # Project income (synchronous yfinance calls, run in thread)
        client = DividendClient()
        projection = await asyncio.to_thread(
            client.get_projected_annual_income, holdings
        )

        # Check against saved goals
        goals = await asyncio.to_thread(get_goals)
        goal_progress = None
        if goals:
            primary = goals[0]  # most recent goal
            target = primary["target_annual"]
            current = projection["total_annual"]
            goal_progress = {
                "goal_id": primary["id"],
                "target_monthly": primary["target_monthly"],
                "target_annual": target,
                "current_annual": current,
                "current_monthly": projection["total_monthly"],
                "progress_pct": round((current / target * 100) if target > 0 else 0, 1),
                "remaining_annual": round(max(0, target - current), 2),
                "currency": primary["currency"],
            }

        return {
            "status": "success",
            "data": {
                **projection,
                "goal_progress": goal_progress,
            },
            "message": f"Projected annual dividend income: ${projection['total_annual']:,.2f} (${projection['total_monthly']:,.2f}/month)",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to project dividend income: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
