"""Wrapper around yfinance for dividend data. All methods are synchronous —
agent tools should call them via ``asyncio.to_thread()``."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import yfinance as yf

logger = logging.getLogger(__name__)


class DividendClient:
    """Provides dividend metrics for any publicly traded stock."""

    # ------------------------------------------------------------------
    # Single-stock helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_dividend_info(symbol: str) -> dict:
        """Return yield, payout ratio, ex-dividend date, and more for *symbol*."""
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

        ex_date_raw = info.get("exDividendDate")
        if isinstance(ex_date_raw, (int, float)):
            ex_date = datetime.fromtimestamp(ex_date_raw, tz=timezone.utc).strftime("%Y-%m-%d")
        elif isinstance(ex_date_raw, str):
            ex_date = ex_date_raw
        else:
            ex_date = ""

        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName") or info.get("longName", symbol),
            "dividend_yield": round((info.get("dividendYield") or 0) * 100, 2),
            "annual_dividend": round(info.get("dividendRate") or 0, 4),
            "payout_ratio": round((info.get("payoutRatio") or 0) * 100, 2),
            "ex_dividend_date": ex_date,
            "five_year_avg_yield": round((info.get("fiveYearAvgDividendYield") or 0), 2),
            "market_price": round(info.get("currentPrice") or info.get("regularMarketPrice") or 0, 2),
            "currency": info.get("currency", "USD"),
        }

    @staticmethod
    def get_dividend_history(symbol: str, years: int = 5) -> list[dict]:
        """Return historical dividend payments for the last *years*."""
        ticker = yf.Ticker(symbol)
        divs = ticker.dividends
        if divs is None or divs.empty:
            return []

        cutoff = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - years)
        records: list[dict] = []
        for ts, amount in divs.items():
            dt = ts.to_pydatetime()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                records.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "amount": round(float(amount), 4),
                })
        return records

    # ------------------------------------------------------------------
    # Multi-stock helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_upcoming_dividends(symbols: list[str]) -> list[dict]:
        """Return upcoming ex-dividend dates for a list of symbols."""
        now = datetime.now(timezone.utc)
        upcoming: list[dict] = []

        for sym in symbols:
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info or {}

                ex_raw = info.get("exDividendDate")
                if isinstance(ex_raw, (int, float)):
                    ex_dt = datetime.fromtimestamp(ex_raw, tz=timezone.utc)
                    if ex_dt >= now:
                        upcoming.append({
                            "symbol": sym.upper(),
                            "name": info.get("shortName") or info.get("longName", sym),
                            "ex_date": ex_dt.strftime("%Y-%m-%d"),
                            "amount": round(info.get("dividendRate", 0) / 4, 4),  # approximate quarterly
                            "yield_pct": round((info.get("dividendYield") or 0) * 100, 2),
                        })
            except Exception as exc:
                logger.debug("Skipping %s in upcoming dividends: %s", sym, exc)

        upcoming.sort(key=lambda d: d["ex_date"])
        return upcoming

    @staticmethod
    def get_projected_annual_income(holdings: list[dict]) -> dict:
        """Calculate projected annual dividend income from a list of holdings.

        Each item in *holdings* should have at minimum ``symbol`` and ``value``
        (current market value of that position).
        """
        by_holding: list[dict] = []
        total_annual = 0.0
        quarterly = {"Q1": 0.0, "Q2": 0.0, "Q3": 0.0, "Q4": 0.0}

        for h in holdings:
            sym = h.get("symbol", "")
            position_value = h.get("value", 0)
            if not sym or position_value <= 0:
                continue
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info or {}
                div_rate = info.get("dividendRate") or 0
                div_yield = info.get("dividendYield") or 0

                # Shares approximation: value / price
                price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
                shares = position_value / price if price > 0 else 0
                annual_income = shares * div_rate

                total_annual += annual_income
                by_holding.append({
                    "symbol": sym.upper(),
                    "name": info.get("shortName") or sym,
                    "annual_income": round(annual_income, 2),
                    "monthly_income": round(annual_income / 12, 2),
                    "yield_pct": round(div_yield * 100, 2),
                    "position_value": round(position_value, 2),
                })

                # Approximate even quarterly split
                q_amount = annual_income / 4
                for q in quarterly:
                    quarterly[q] += q_amount

            except Exception as exc:
                logger.debug("Skipping %s in income projection: %s", sym, exc)

        by_holding.sort(key=lambda x: x["annual_income"], reverse=True)

        return {
            "total_annual": round(total_annual, 2),
            "total_monthly": round(total_annual / 12, 2),
            "by_holding": by_holding,
            "by_quarter": {k: round(v, 2) for k, v in quarterly.items()},
        }
