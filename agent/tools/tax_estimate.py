"""Tool: Estimate capital gains/losses and dividend income for tax purposes."""

import time

from langchain_core.tools import tool

from agent.ghostfolio_client import GhostfolioClient


DISCLAIMER = (
    "DISCLAIMER: This is a rough estimate for informational purposes only. "
    "Tax calculations depend on your jurisdiction, holding periods, tax-loss "
    "harvesting, and other factors. Consult a qualified tax professional for "
    "accurate tax advice."
)


@tool
async def tax_estimate(
    date_range: str = "ytd",
) -> dict:
    """Estimate capital gains/losses and dividend income from portfolio activity.
    Use this when the user asks about taxes, capital gains, tax liability,
    or dividend income for tax reporting.

    IMPORTANT: Always present results with the tax disclaimer.

    Args:
        date_range: Period for the estimate: 'ytd', '1y', '3y', '5y', 'max'.
                    Defaults to 'ytd'.
    """
    start = time.time()
    client = GhostfolioClient()

    try:
        # Get performance data (contains gains/losses and dividends)
        perf = await client.get_portfolio_performance(date_range=date_range)
        performance = perf.get("performance", {})

        # Get dividend data
        dividends_data = await client.get_portfolio_dividends(
            date_range=date_range, group_by="month"
        )
        dividends_list = dividends_data.get("dividends", [])
        total_dividends = sum(d.get("investment", 0) for d in dividends_list)

        net_perf = performance.get("netPerformance", 0)
        gross_perf = performance.get("grossPerformance", 0)
        fees = performance.get("fees", 0)

        # Estimate: gains are gross performance; dividends are separate income
        estimated_gains = gross_perf
        gains_type = "Capital Gains" if estimated_gains > 0 else "Capital Losses"

        return {
            "status": "success",
            "data": {
                "date_range": date_range,
                "estimated_capital_gains_losses": round(estimated_gains, 2),
                "gains_type": gains_type,
                "total_dividend_income": round(total_dividends, 2),
                "total_fees_deductible": round(fees, 2),
                "net_performance": round(net_perf, 2),
                "monthly_dividends": [
                    {
                        "date": d.get("date", ""),
                        "amount": round(d.get("investment", 0), 2),
                    }
                    for d in dividends_list[-12:]  # Last 12 months
                ],
                "disclaimer": DISCLAIMER,
            },
            "message": f"{gains_type}: {round(estimated_gains, 2)}, Dividends: {round(total_dividends, 2)}",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {"disclaimer": DISCLAIMER},
            "message": f"Failed to estimate taxes: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
