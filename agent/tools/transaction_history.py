"""Tool: Retrieve and categorize transaction/activity history."""

import time
from collections import Counter

from langchain_core.tools import tool

from agent.ghostfolio_client import GhostfolioClient


@tool
async def transaction_history(
    account_filter: str = "",
    type_filter: str = "",
) -> dict:
    """Retrieve the user's transaction history (activities) with categorization
    and pattern detection. Use this when the user asks about their trades,
    purchases, sales, dividends received, or transaction patterns.

    Args:
        account_filter: Optional account ID to filter transactions.
        type_filter: Optional activity type filter: 'BUY', 'SELL', 'DIVIDEND',
                     'FEE', 'INTEREST', 'LIABILITY'.
    """
    start = time.time()
    client = GhostfolioClient()

    try:
        params = {}
        if account_filter:
            params["accounts"] = account_filter

        orders = await client.get_orders(filters=params or None)
        activities = orders.get("activities", orders) if isinstance(orders, dict) else orders

        if not isinstance(activities, list):
            activities = []

        # Apply type filter locally if provided
        valid_types = {"BUY", "SELL", "DIVIDEND", "FEE", "INTEREST", "LIABILITY"}
        if type_filter and type_filter.upper() in valid_types:
            activities = [
                a for a in activities if a.get("type") == type_filter.upper()
            ]

        # Categorize
        type_counts = Counter(a.get("type", "UNKNOWN") for a in activities)
        total_fees = sum(a.get("fee", 0) for a in activities)

        # Recent activities (last 20)
        recent = sorted(activities, key=lambda a: a.get("date", ""), reverse=True)[:20]
        recent_summary = []
        for a in recent:
            recent_summary.append({
                "date": a.get("date", ""),
                "type": a.get("type", ""),
                "symbol": a.get("SymbolProfile", {}).get("symbol", "")
                if isinstance(a.get("SymbolProfile"), dict)
                else "",
                "quantity": a.get("quantity", 0),
                "unit_price": a.get("unitPrice", 0),
                "fee": a.get("fee", 0),
                "currency": a.get("currency", ""),
            })

        return {
            "status": "success",
            "data": {
                "total_activities": len(activities),
                "type_breakdown": dict(type_counts),
                "total_fees_paid": round(total_fees, 2),
                "recent_activities": recent_summary,
            },
            "message": f"Found {len(activities)} activities",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to get transactions: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
