"""HTTP client for Ghostfolio REST API."""

import httpx

from agent.config import config


class GhostfolioClient:
    """Async client for interacting with the Ghostfolio API."""

    _shared_client: httpx.AsyncClient | None = None

    def __init__(self, token: str | None = None):
        self.base_url = config.GHOSTFOLIO_API_URL.rstrip("/")
        self.token = token or config.GHOSTFOLIO_API_TOKEN

    @classmethod
    def _get_client(cls) -> httpx.AsyncClient:
        if cls._shared_client is None or cls._shared_client.is_closed:
            cls._shared_client = httpx.AsyncClient(timeout=10.0)
        return cls._shared_client

    @classmethod
    async def close(cls) -> None:
        """Close the shared HTTP client for clean shutdown."""
        if cls._shared_client is not None and not cls._shared_client.is_closed:
            await cls._shared_client.aclose()
            cls._shared_client = None

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get(self, path: str, params: dict | None = None) -> dict:
        """Make an authenticated GET request to Ghostfolio API."""
        client = self._get_client()
        response = await client.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    # --- Portfolio endpoints ---

    async def get_portfolio_details(self, filters: dict | None = None) -> dict:
        """GET /api/v1/portfolio/details"""
        return await self._get("/v1/portfolio/details", params=filters)

    async def get_portfolio_holdings(self, filters: dict | None = None) -> dict:
        """GET /api/v1/portfolio/holdings"""
        return await self._get("/v1/portfolio/holdings", params=filters)

    async def get_portfolio_performance(
        self, date_range: str = "max"
    ) -> dict:
        """GET /api/v2/portfolio/performance"""
        return await self._get(
            "/v2/portfolio/performance", params={"range": date_range}
        )

    async def get_portfolio_dividends(
        self, date_range: str = "max", group_by: str = "month"
    ) -> dict:
        """GET /api/v1/portfolio/dividends"""
        return await self._get(
            "/v1/portfolio/dividends",
            params={"range": date_range, "groupBy": group_by},
        )

    async def get_portfolio_investments(
        self, date_range: str = "max", group_by: str = "month"
    ) -> dict:
        """GET /api/v1/portfolio/investments"""
        return await self._get(
            "/v1/portfolio/investments",
            params={"range": date_range, "groupBy": group_by},
        )

    async def get_portfolio_report(self) -> dict:
        """GET /api/v1/portfolio/report"""
        return await self._get("/v1/portfolio/report")

    # --- Order / Activity endpoints ---

    async def get_orders(self, filters: dict | None = None) -> dict:
        """GET /api/v1/order"""
        return await self._get("/v1/order", params=filters)

    # --- Account endpoints ---

    async def get_accounts(self) -> dict:
        """GET /api/v1/account"""
        return await self._get("/v1/account")

    # --- Symbol / Market data endpoints ---

    async def get_symbol(self, data_source: str, symbol: str) -> dict:
        """GET /api/v1/symbol/:dataSource/:symbol"""
        return await self._get(f"/v1/symbol/{data_source}/{symbol}")

    async def get_benchmarks(self) -> dict:
        """GET /api/v1/benchmarks"""
        return await self._get("/v1/benchmarks")

    # --- Exchange rate ---

    async def get_exchange_rate(
        self, currency_from: str, currency_to: str
    ) -> dict:
        """GET /api/v1/exchange-rate/:from/:to"""
        return await self._get(
            f"/v1/exchange-rate/{currency_from}/{currency_to}"
        )

    # --- Info ---

    async def get_info(self) -> dict:
        """GET /api/v1/info"""
        return await self._get("/v1/info")
