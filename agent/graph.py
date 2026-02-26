"""LangGraph agent: the core reasoning loop with verification."""

import asyncio
import logging
import time
import uuid
from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agent.config import config
from agent.models import AgentMetrics
from agent.observability import trace_agent_run
from agent.prompts.system import DISCLAIMER_TEMPLATE, SYSTEM_PROMPT
from agent.tools import ALL_TOOLS
from agent.verification import ResponseVerifier


class AgentState(TypedDict):
    """State schema for the LangGraph agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    tool_results: list[dict]
    iterations: int
    confidence: float
    verification_passed: bool
    query_type: str
    metrics: dict
    total_input_tokens: int
    total_output_tokens: int
    model_used_last: str
    sonnet_input_tokens: int
    sonnet_output_tokens: int
    haiku_input_tokens: int
    haiku_output_tokens: int


logger = logging.getLogger(__name__)

# Initialize LLM with tool binding — Sonnet for reasoning, Haiku for summarization
llm = ChatAnthropic(
    model=config.PRIMARY_MODEL,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=4096,
    temperature=0,
)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

llm_fast = ChatAnthropic(
    model=config.FALLBACK_MODEL,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=4096,
    temperature=0,
)
llm_fast_with_tools = llm_fast.bind_tools(ALL_TOOLS)

verifier = ResponseVerifier()


async def _trace_in_background(
    conversation_id: str,
    input_message: str,
    output_message: str,
    tools_used: list[str],
    confidence: float,
    metrics: dict,
) -> None:
    """Fire-and-forget wrapper to run Langfuse tracing off the critical path."""
    try:
        await asyncio.to_thread(
            trace_agent_run,
            conversation_id=conversation_id,
            input_message=input_message,
            output_message=output_message,
            tools_used=tools_used,
            confidence=confidence,
            metrics=metrics,
        )
    except Exception as e:
        logger.warning(f"Background Langfuse trace failed: {e}")


def classify_query(state: AgentState) -> AgentState:
    """Classify the user's query type for verification routing."""
    messages = state["messages"]
    last_user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content.lower()
            break

    query_type = "general"
    if any(kw in last_user_msg for kw in ["tax", "capital gain", "dividend income", "deduct"]):
        query_type = "tax"
    elif any(kw in last_user_msg for kw in ["should i", "recommend", "suggest", "advice", "optimize"]):
        query_type = "advice"
    elif any(kw in last_user_msg for kw in ["compliance", "concentration", "diversif", "risk limit"]):
        query_type = "compliance"

    return {**state, "query_type": query_type}


def call_model(state: AgentState) -> AgentState:
    """Invoke the LLM with the current message history.

    Uses Haiku (fast model) for summarization passes (iteration > 0 with tool
    results already collected) and Sonnet for the initial reasoning pass.
    """
    iterations = state.get("iterations", 0)
    if iterations >= config.MAX_ITERATIONS:
        return {
            **state,
            "messages": [
                AIMessage(content="I've reached my reasoning limit for this query. Here's what I found so far based on the data collected.")
            ],
        }

    # Use Haiku for summarization pass (after tools have returned results)
    has_tool_results = len(state.get("tool_results", [])) > 0
    use_fast = iterations > 0 and has_tool_results
    model = llm_fast_with_tools if use_fast else llm_with_tools

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = model.invoke(messages)

    # Accumulate token usage from response metadata, split by model
    usage = response.response_metadata.get("usage", {})
    input_tok = usage.get("input_tokens", 0)
    output_tok = usage.get("output_tokens", 0)

    prev_input = state.get("total_input_tokens", 0)
    prev_output = state.get("total_output_tokens", 0)

    if use_fast:
        haiku_in = state.get("haiku_input_tokens", 0) + input_tok
        haiku_out = state.get("haiku_output_tokens", 0) + output_tok
        sonnet_in = state.get("sonnet_input_tokens", 0)
        sonnet_out = state.get("sonnet_output_tokens", 0)
    else:
        sonnet_in = state.get("sonnet_input_tokens", 0) + input_tok
        sonnet_out = state.get("sonnet_output_tokens", 0) + output_tok
        haiku_in = state.get("haiku_input_tokens", 0)
        haiku_out = state.get("haiku_output_tokens", 0)

    return {
        **state,
        "messages": [response],
        "iterations": iterations + 1,
        "total_input_tokens": prev_input + input_tok,
        "total_output_tokens": prev_output + output_tok,
        "model_used_last": "haiku" if use_fast else "sonnet",
        "sonnet_input_tokens": sonnet_in,
        "sonnet_output_tokens": sonnet_out,
        "haiku_input_tokens": haiku_in,
        "haiku_output_tokens": haiku_out,
    }


def collect_tool_results(state: AgentState) -> AgentState:
    """Extract tool results from the latest messages for verification."""
    tool_results = list(state.get("tool_results", []))
    for msg in state["messages"]:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            # Tool messages contain the result as string content
            try:
                import json
                data = json.loads(msg.content)
                if isinstance(data, dict) and "status" in data:
                    tool_results.append(data)
            except (json.JSONDecodeError, TypeError):
                pass
    return {**state, "tool_results": tool_results}


def verify_response(state: AgentState) -> AgentState:
    """Run verification checks on the agent's final response."""
    messages = state["messages"]
    last_ai_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            last_ai_msg = msg.content
            break

    if not last_ai_msg:
        return {**state, "confidence": 0.0, "verification_passed": False}

    result = verifier.verify(
        response_text=last_ai_msg,
        tool_results=state.get("tool_results", []),
        query_type=state.get("query_type", "general"),
    )

    # Append disclaimer for advice/tax queries
    query_type = state.get("query_type", "general")
    if query_type in ("tax", "advice") and DISCLAIMER_TEMPLATE.strip() not in last_ai_msg:
        amended = last_ai_msg + DISCLAIMER_TEMPLATE
        return {
            **state,
            "messages": [AIMessage(content=amended)],
            "confidence": result.confidence,
            "verification_passed": result.passed,
        }

    return {
        **state,
        "confidence": result.confidence,
        "verification_passed": result.passed,
    }


def should_continue(state: AgentState) -> str:
    """Route: if the last message has tool calls, go to tools; otherwise verify."""
    messages = state["messages"]
    last_message = messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "verify"


# Build the graph
tool_node = ToolNode(ALL_TOOLS)

graph_builder = StateGraph(AgentState)
graph_builder.add_node("classify", classify_query)
graph_builder.add_node("agent", call_model)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("collect", collect_tool_results)
graph_builder.add_node("verify", verify_response)

graph_builder.set_entry_point("classify")
graph_builder.add_edge("classify", "agent")
graph_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", "verify": "verify"})
graph_builder.add_edge("tools", "collect")
graph_builder.add_edge("collect", "agent")
graph_builder.add_edge("verify", END)

agent_graph = graph_builder.compile()


# In-memory conversation store (swap for Redis/DB in production)
_conversations: dict[str, list[BaseMessage]] = {}


async def run_agent(
    message: str,
    conversation_id: str | None = None,
    ghostfolio_token: str | None = None,
) -> dict:
    """Run the agent graph and return the response."""
    if not message or not message.strip():
        return {
            "response": "It looks like you sent an empty message. How can I help you with your portfolio today?",
            "conversation_id": conversation_id or str(uuid.uuid4()),
            "tools_used": [],
            "confidence": 0.0,
            "metrics": AgentMetrics(task_id=f"chat_{int(time.time())}").to_dict(),
        }

    conversation_id = conversation_id or str(uuid.uuid4())
    history = _conversations.get(conversation_id, [])
    history.append(HumanMessage(content=message))

    metrics = AgentMetrics(task_id=f"chat_{int(time.time())}")

    initial_state: AgentState = {
        "messages": history,
        "tool_results": [],
        "iterations": 0,
        "confidence": 0.0,
        "verification_passed": False,
        "query_type": "general",
        "metrics": {},
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "model_used_last": "sonnet",
        "sonnet_input_tokens": 0,
        "sonnet_output_tokens": 0,
        "haiku_input_tokens": 0,
        "haiku_output_tokens": 0,
    }

    # Run the graph
    final_state = await agent_graph.ainvoke(initial_state)

    # Extract response
    response_text = ""
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            response_text = msg.content
            break

    # Update conversation history
    _conversations[conversation_id] = final_state["messages"]

    # Collect tools used
    tools_used = []
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            tools_used.extend(tc["name"] for tc in msg.tool_calls)

    # Populate token usage and cost from accumulated state
    input_tokens = final_state.get("total_input_tokens", 0)
    output_tokens = final_state.get("total_output_tokens", 0)

    # Mixed-model pricing: Sonnet $3/$15 per 1M, Haiku $0.80/$4 per 1M
    sonnet_in = final_state.get("sonnet_input_tokens", 0)
    sonnet_out = final_state.get("sonnet_output_tokens", 0)
    haiku_in = final_state.get("haiku_input_tokens", 0)
    haiku_out = final_state.get("haiku_output_tokens", 0)
    cost = (
        (sonnet_in * 3.0 + sonnet_out * 15.0)
        + (haiku_in * 0.80 + haiku_out * 4.0)
    ) / 1_000_000

    metrics.success = True
    metrics.end_time = time.time()
    metrics.tools_called = tools_used
    metrics.iterations = final_state.get("iterations", 0)
    metrics.input_tokens = input_tokens
    metrics.output_tokens = output_tokens
    metrics.total_tokens = input_tokens + output_tokens
    metrics.total_cost_usd = cost

    # Trace to Langfuse — fire-and-forget to avoid blocking the response
    asyncio.create_task(_trace_in_background(
        conversation_id=conversation_id,
        input_message=message,
        output_message=response_text,
        tools_used=tools_used,
        confidence=final_state.get("confidence", 0.0),
        metrics=metrics.to_dict(),
    ))

    return {
        "response": response_text,
        "conversation_id": conversation_id,
        "tools_used": list(set(tools_used)),
        "confidence": final_state.get("confidence", 0.0),
        "metrics": metrics.to_dict(),
    }
