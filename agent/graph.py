"""LangGraph agent: the core reasoning loop with verification."""

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


# Initialize LLM with tool binding
llm = ChatAnthropic(
    model=config.PRIMARY_MODEL,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=4096,
    temperature=0,
)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

verifier = ResponseVerifier()


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
    """Invoke the LLM with the current message history."""
    iterations = state.get("iterations", 0)
    if iterations >= config.MAX_ITERATIONS:
        return {
            **state,
            "messages": [
                AIMessage(content="I've reached my reasoning limit for this query. Here's what I found so far based on the data collected.")
            ],
        }

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)

    return {
        **state,
        "messages": [response],
        "iterations": iterations + 1,
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

    metrics.success = True
    metrics.end_time = time.time()
    metrics.tools_called = tools_used
    metrics.iterations = final_state.get("iterations", 0)

    # Trace to Langfuse
    trace_agent_run(
        conversation_id=conversation_id,
        input_message=message,
        output_message=response_text,
        tools_used=tools_used,
        confidence=final_state.get("confidence", 0.0),
        metrics=metrics.to_dict(),
    )

    return {
        "response": response_text,
        "conversation_id": conversation_id,
        "tools_used": list(set(tools_used)),
        "confidence": final_state.get("confidence", 0.0),
        "metrics": metrics.to_dict(),
    }
