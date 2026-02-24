"""Tool: Analyze portfolio holdings, allocation, and sector breakdown."""

import time

from langchain_core.tools import tool

from agent.ghostfolio_client import GhostfolioClient


@tool
async def portfolio_analysis(
    account_filter: str = "",
    asset_class_filter: str = "",
    tag_filter: str = "",
) -> dict:
    """Analyze a user's portfolio: holdings, allocation percentages, sector/asset class
    breakdown, and total value. Use this when the user asks about their portfolio
    composition, what they own, how their money is allocated, or sector exposure.

    Args:
        account_filter: Optional account ID to filter holdings by.
        asset_class_filter: Optional asset class to filter (EQUITY, FIXED_INCOME, etc.).
        tag_filter: Optional tag name to filter holdings by.
    """
    start = time.time()
    client = GhostfolioClient()

    try:
        params = {}
        if account_filter:
            params["accounts"] = account_filter
        if asset_class_filter:
            params["assetClasses"] = asset_class_filter
        if tag_filter:
            params["tags"] = tag_filter

        details = await client.get_portfolio_details(filters=params or None)
        holdings = details.get("holdings", {})

        # Compute sector allocation
        sector_allocation = {}
        asset_class_allocation = {}
        total_value = 0

        holdings_summary = []
        for key, holding in holdings.items():
            alloc = holding.get("allocationInPercentage", 0)
            value = holding.get("value", 0)
            total_value += value

            holdings_summary.append({
                "name": holding.get("name", key),
                "symbol": holding.get("symbol", ""),
                "currency": holding.get("currency", ""),
                "asset_class": holding.get("assetClass", ""),
                "asset_sub_class": holding.get("assetSubClass", ""),
                "allocation_pct": round(alloc * 100, 2),
                "value": round(value, 2),
            })

            ac = holding.get("assetClass", "Unknown")
            asset_class_allocation[ac] = asset_class_allocation.get(ac, 0) + alloc

            for sector_info in holding.get("sectors", []):
                name = sector_info.get("name", "Unknown")
                weight = sector_info.get("weight", 0) * alloc
                sector_allocation[name] = sector_allocation.get(name, 0) + weight

        # Sort holdings by allocation descending
        holdings_summary.sort(key=lambda h: h["allocation_pct"], reverse=True)

        # Build warnings
        warnings = []
        for h in holdings_summary:
            if h["allocation_pct"] > 20:
                warnings.append(
                    f"High concentration: {h['name']} at {h['allocation_pct']}%"
                )
        for ac, pct in asset_class_allocation.items():
            if pct > 0.4:
                warnings.append(
                    f"High {ac} concentration: {round(pct * 100, 1)}%"
                )

        return {
            "status": "success",
            "data": {
                "total_value": round(total_value, 2),
                "holdings_count": len(holdings_summary),
                "holdings": holdings_summary[:20],  # Top 20
                "asset_class_allocation": {
                    k: round(v * 100, 2) for k, v in asset_class_allocation.items()
                },
                "sector_allocation": {
                    k: round(v * 100, 2)
                    for k, v in sorted(
                        sector_allocation.items(), key=lambda x: x[1], reverse=True
                    )[:10]
                },
                "warnings": warnings,
            },
            "message": f"Portfolio has {len(holdings_summary)} holdings worth {round(total_value, 2)}",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to analyze portfolio: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
