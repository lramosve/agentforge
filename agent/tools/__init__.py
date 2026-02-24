"""AgentForge finance tools for Ghostfolio."""

from agent.tools.portfolio_analysis import portfolio_analysis
from agent.tools.portfolio_performance import portfolio_performance
from agent.tools.market_data_lookup import market_data_lookup
from agent.tools.transaction_history import transaction_history
from agent.tools.tax_estimate import tax_estimate
from agent.tools.compliance_check import compliance_check
from agent.tools.benchmark_comparison import benchmark_comparison

ALL_TOOLS = [
    portfolio_analysis,
    portfolio_performance,
    market_data_lookup,
    transaction_history,
    tax_estimate,
    compliance_check,
    benchmark_comparison,
]

__all__ = [
    "portfolio_analysis",
    "portfolio_performance",
    "market_data_lookup",
    "transaction_history",
    "tax_estimate",
    "compliance_check",
    "benchmark_comparison",
    "ALL_TOOLS",
]
