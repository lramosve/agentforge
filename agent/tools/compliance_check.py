"""Tool: Check portfolio against diversification and concentration rules."""

import time

from langchain_core.tools import tool

from agent.ghostfolio_client import GhostfolioClient


# Default concentration thresholds
SINGLE_HOLDING_LIMIT = 0.20  # 20%
SINGLE_SECTOR_LIMIT = 0.40  # 40%
SINGLE_ASSET_CLASS_LIMIT = 0.60  # 60%
MIN_HOLDINGS_DIVERSIFIED = 5


@tool
async def compliance_check(
    single_holding_limit: float = 20.0,
    single_sector_limit: float = 40.0,
    single_asset_class_limit: float = 60.0,
) -> dict:
    """Check the portfolio against diversification rules and concentration limits.
    Use this when the user asks about portfolio risk, diversification, concentration,
    or regulatory compliance.

    Args:
        single_holding_limit: Max percentage for a single holding (default 20%).
        single_sector_limit: Max percentage for a single sector (default 40%).
        single_asset_class_limit: Max percentage for a single asset class (default 60%).
    """
    start = time.time()
    client = GhostfolioClient()

    try:
        details = await client.get_portfolio_details()
        holdings = details.get("holdings", {})

        violations = []
        warnings = []
        passes = []

        # Check 1: Single holding concentration
        for key, holding in holdings.items():
            alloc_pct = holding.get("allocationInPercentage", 0) * 100
            name = holding.get("name", key)
            if alloc_pct > single_holding_limit:
                violations.append({
                    "rule": "Single Holding Concentration",
                    "detail": f"{name} is {alloc_pct:.1f}% of portfolio (limit: {single_holding_limit}%)",
                    "severity": "HIGH",
                })
            elif alloc_pct > single_holding_limit * 0.8:
                warnings.append({
                    "rule": "Single Holding Approaching Limit",
                    "detail": f"{name} is {alloc_pct:.1f}% (limit: {single_holding_limit}%)",
                    "severity": "MEDIUM",
                })

        # Check 2: Asset class concentration
        asset_class_totals = {}
        for holding in holdings.values():
            ac = holding.get("assetClass", "Unknown")
            alloc = holding.get("allocationInPercentage", 0) * 100
            asset_class_totals[ac] = asset_class_totals.get(ac, 0) + alloc

        for ac, total in asset_class_totals.items():
            if total > single_asset_class_limit:
                violations.append({
                    "rule": "Asset Class Concentration",
                    "detail": f"{ac} is {total:.1f}% (limit: {single_asset_class_limit}%)",
                    "severity": "MEDIUM",
                })

        # Check 3: Sector concentration
        sector_totals = {}
        for holding in holdings.values():
            alloc = holding.get("allocationInPercentage", 0)
            for sector in holding.get("sectors", []):
                name = sector.get("name", "Unknown")
                weight = sector.get("weight", 0) * alloc * 100
                sector_totals[name] = sector_totals.get(name, 0) + weight

        for sector, total in sector_totals.items():
            if total > single_sector_limit:
                violations.append({
                    "rule": "Sector Concentration",
                    "detail": f"{sector} is {total:.1f}% (limit: {single_sector_limit}%)",
                    "severity": "MEDIUM",
                })

        # Check 4: Minimum diversification
        num_holdings = len(holdings)
        if num_holdings < MIN_HOLDINGS_DIVERSIFIED:
            warnings.append({
                "rule": "Minimum Diversification",
                "detail": f"Only {num_holdings} holdings (recommended: {MIN_HOLDINGS_DIVERSIFIED}+)",
                "severity": "LOW",
            })
        else:
            passes.append(f"Diversification: {num_holdings} holdings (OK)")

        # Summary
        compliant = len(violations) == 0

        return {
            "status": "success",
            "data": {
                "compliant": compliant,
                "violations": violations,
                "warnings": warnings,
                "passes": passes,
                "holdings_count": num_holdings,
                "asset_class_breakdown": {
                    k: round(v, 1) for k, v in asset_class_totals.items()
                },
                "thresholds_used": {
                    "single_holding_limit": single_holding_limit,
                    "single_sector_limit": single_sector_limit,
                    "single_asset_class_limit": single_asset_class_limit,
                },
            },
            "message": f"{'COMPLIANT' if compliant else f'{len(violations)} VIOLATION(S)'} — {len(warnings)} warning(s)",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed compliance check: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
