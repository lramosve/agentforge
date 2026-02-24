"""Tool: Compare portfolio performance against benchmarks."""

import time

from langchain_core.tools import tool

from agent.ghostfolio_client import GhostfolioClient


@tool
async def benchmark_comparison(
    date_range: str = "ytd",
) -> dict:
    """Compare the user's portfolio performance against market benchmarks.
    Use this when the user asks how they're doing compared to the market,
    S&P 500, or other indices.

    Args:
        date_range: Period to compare: '1m', '3m', '6m', 'ytd', '1y', '3y',
                    '5y', 'max'. Defaults to 'ytd'.
    """
    start = time.time()
    client = GhostfolioClient()

    try:
        # Get portfolio performance
        perf = await client.get_portfolio_performance(date_range=date_range)
        portfolio_perf = perf.get("performance", {})
        portfolio_return = portfolio_perf.get("netPerformancePercentage", 0)

        # Get benchmarks
        benchmarks = await client.get_benchmarks()
        benchmark_list = benchmarks if isinstance(benchmarks, list) else benchmarks.get("benchmarks", [])

        comparisons = []
        for bm in benchmark_list:
            bm_name = bm.get("name", "Unknown")
            bm_perf = bm.get("performances", {})

            # Find the matching date range performance
            bm_return = None
            if date_range in bm_perf:
                bm_return = bm_perf[date_range]
            elif "ytd" in bm_perf:
                bm_return = bm_perf["ytd"]

            if bm_return is not None:
                diff = portfolio_return - bm_return
                comparisons.append({
                    "benchmark": bm_name,
                    "benchmark_return_pct": round(bm_return * 100, 2),
                    "portfolio_return_pct": round(portfolio_return * 100, 2),
                    "difference_pct": round(diff * 100, 2),
                    "outperforming": diff > 0,
                })

        return {
            "status": "success",
            "data": {
                "date_range": date_range,
                "portfolio_return_pct": round(portfolio_return * 100, 2),
                "comparisons": comparisons,
                "benchmarks_available": len(benchmark_list),
            },
            "message": f"Portfolio: {portfolio_return * 100:.2f}% ({date_range}) vs {len(comparisons)} benchmark(s)",
            "execution_time": round(time.time() - start, 3),
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"Failed benchmark comparison: {str(e)}",
            "execution_time": round(time.time() - start, 3),
        }
