"""Agent configuration loaded from environment variables."""

import os


class AgentConfig:
    """Configuration for the AgentForge agent."""

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GHOSTFOLIO_API_URL: str = os.getenv("GHOSTFOLIO_API_URL", "http://localhost:3333/api")
    GHOSTFOLIO_API_TOKEN: str = os.getenv("GHOSTFOLIO_API_TOKEN", "")

    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    MAX_ITERATIONS: int = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
    TIMEOUT_SECONDS: float = float(os.getenv("AGENT_TIMEOUT_SECONDS", "30"))
    MAX_COST_USD: float = float(os.getenv("AGENT_MAX_COST_USD", "0.10"))

    PRIMARY_MODEL: str = "claude-sonnet-4-6"
    FALLBACK_MODEL: str = "claude-haiku-4-5-20251001"


config = AgentConfig()
