"""Langfuse observability integration for trace logging, cost tracking, and eval scores."""

import os
import logging

logger = logging.getLogger(__name__)

_langfuse = None


def _get_langfuse():
    """Lazy-initialize Langfuse client."""
    global _langfuse
    if _langfuse is not None:
        return _langfuse

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        logger.warning("Langfuse keys not configured — observability disabled")
        return None

    try:
        from langfuse import Langfuse

        _langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        return _langfuse
    except ImportError:
        logger.warning("langfuse package not installed — observability disabled")
        return None
    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse: {e}")
        return None


def trace_agent_run(
    conversation_id: str,
    input_message: str,
    output_message: str,
    tools_used: list[str],
    confidence: float,
    metrics: dict,
) -> None:
    """Log a complete agent run as a Langfuse trace."""
    client = _get_langfuse()
    if client is None:
        return

    try:
        trace = client.trace(
            name="agentforge-chat",
            session_id=conversation_id,
            input=input_message,
            output=output_message,
            metadata={
                "tools_used": tools_used,
                "confidence": confidence,
                "iterations": metrics.get("iterations", 0),
                "duration_seconds": metrics.get("duration_seconds", 0),
            },
        )

        # Add cost/token observation
        trace.generation(
            name="agent-response",
            model=os.getenv("AGENT_MODEL", "claude-sonnet-4-6"),
            input=input_message,
            output=output_message,
            metadata={
                "total_tokens": metrics.get("total_tokens", 0),
                "cost_usd": metrics.get("total_cost_usd", 0),
            },
        )

        # Score the trace with confidence
        trace.score(
            name="confidence",
            value=confidence,
            comment=f"Tools: {', '.join(tools_used) or 'none'}",
        )

        client.flush()
    except Exception as e:
        logger.warning(f"Failed to log trace to Langfuse: {e}")


def score_trace(
    trace_id: str,
    score_name: str,
    value: float,
    comment: str = "",
) -> None:
    """Add a score to an existing trace (e.g., user feedback)."""
    client = _get_langfuse()
    if client is None:
        return

    try:
        client.score(
            trace_id=trace_id,
            name=score_name,
            value=value,
            comment=comment,
        )
        client.flush()
    except Exception as e:
        logger.warning(f"Failed to score trace: {e}")
