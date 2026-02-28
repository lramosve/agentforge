"""AgentForge finance tools for Ghostfolio."""

from agent.tools.portfolio_analysis import portfolio_analysis
from agent.tools.portfolio_performance import portfolio_performance
from agent.tools.market_data_lookup import market_data_lookup
from agent.tools.transaction_history import transaction_history
from agent.tools.tax_estimate import tax_estimate
from agent.tools.compliance_check import compliance_check
from agent.tools.benchmark_comparison import benchmark_comparison
from agent.tools.dividend_calendar import dividend_calendar
from agent.tools.dividend_income import dividend_income_projection
from agent.tools.dividend_goals import dividend_goal_manager
from agent.tools.dividend_screener import dividend_screener

ALL_TOOLS = [
    portfolio_analysis,
    portfolio_performance,
    market_data_lookup,
    transaction_history,
    tax_estimate,
    compliance_check,
    benchmark_comparison,
    dividend_calendar,
    dividend_income_projection,
    dividend_goal_manager,
    dividend_screener,
]

__all__ = [
    "portfolio_analysis",
    "portfolio_performance",
    "market_data_lookup",
    "transaction_history",
    "tax_estimate",
    "compliance_check",
    "benchmark_comparison",
    "dividend_calendar",
    "dividend_income_projection",
    "dividend_goal_manager",
    "dividend_screener",
    "ALL_TOOLS",
]
