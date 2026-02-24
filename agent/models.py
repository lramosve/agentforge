"""Shared data models for the agent."""

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class ToolResult:
    """Structured result from a tool execution."""

    status: str  # "success" or "error"
    data: Any
    message: str
    execution_time: float

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "data": self.data,
            "message": self.message,
            "execution_time": self.execution_time,
        }


@dataclass
class VerificationResult:
    """Result of a verification check."""

    passed: bool
    confidence: float  # 0.0 - 1.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class AgentMetrics:
    """Metrics collected during agent execution."""

    task_id: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    iterations: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost_usd: float = 0.0
    tools_called: list[str] = field(default_factory=list)
    success: bool = False
    error: str | None = None

    @property
    def duration_seconds(self) -> float:
        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "duration_seconds": self.duration_seconds,
            "iterations": self.iterations,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "tools_called": self.tools_called,
            "success": self.success,
            "error": self.error,
        }
