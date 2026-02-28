"""API router for agent endpoints."""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.database import create_goal, delete_goal, get_goals, update_goal
from agent.graph import run_agent, stream_agent
from agent.observability import score_trace
from agent.tools import ALL_TOOLS

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    ghostfolio_token: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    tools_used: list[str]
    confidence: float
    metrics: dict
    trace_id: str
    tool_results: list[dict] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AgentForge financial agent."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        result = await run_agent(
            message=request.message,
            conversation_id=request.conversation_id,
            ghostfolio_token=request.ghostfolio_token,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    """Stream agent response as Server-Sent Events."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def event_generator():
        try:
            async for event in stream_agent(
                message=request.message,
                conversation_id=request.conversation_id,
                ghostfolio_token=request.ghostfolio_token,
            ):
                event_type = event.get("type", "token")
                event_data = json.dumps(event.get("data", {}))
                yield f"event: {event_type}\ndata: {event_data}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


class ToolInfo(BaseModel):
    name: str
    description: str


class ToolsResponse(BaseModel):
    tools: list[ToolInfo]


@router.get("/tools", response_model=ToolsResponse)
async def list_tools():
    """Return all available agent tools with their names and descriptions."""
    tools = [
        ToolInfo(name=t.name, description=t.description) for t in ALL_TOOLS
    ]
    return ToolsResponse(tools=tools)


class FeedbackRequest(BaseModel):
    trace_id: str
    score: float  # 1.0 = thumbs up, 0.0 = thumbs down
    comment: str = ""


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback (thumbs up/down) for an agent response."""
    if request.score not in (0.0, 1.0):
        raise HTTPException(status_code=400, detail="Score must be 0 or 1")
    await asyncio.to_thread(
        score_trace,
        trace_id=request.trace_id,
        score_name="user-feedback",
        value=request.score,
        comment=request.comment,
    )
    return {"status": "ok"}


@router.get("/health")
async def agent_health():
    return {"status": "ok", "agent": "agentforge"}


# ---------------------------------------------------------------------------
# Dividend Goal CRUD endpoints
# ---------------------------------------------------------------------------

class DividendGoalCreate(BaseModel):
    target_monthly: float = 0.0
    target_annual: float = 0.0
    currency: str = "USD"
    deadline: str = ""
    notes: str = ""


class DividendGoalUpdate(BaseModel):
    target_monthly: float | None = None
    target_annual: float | None = None
    currency: str | None = None
    deadline: str | None = None
    notes: str | None = None


class DividendGoalResponse(BaseModel):
    id: str
    target_monthly: float
    target_annual: float
    currency: str
    deadline: str
    notes: str
    created_at: str
    updated_at: str


@router.get("/dividend-goals", response_model=list[DividendGoalResponse])
async def list_dividend_goals():
    """List all dividend income goals."""
    goals = await asyncio.to_thread(get_goals)
    return goals


@router.post("/dividend-goals", response_model=DividendGoalResponse, status_code=201)
async def create_dividend_goal(body: DividendGoalCreate):
    """Create a new dividend income goal."""
    if body.target_monthly <= 0 and body.target_annual <= 0:
        raise HTTPException(status_code=400, detail="Provide a target_monthly or target_annual > 0")
    goal = await asyncio.to_thread(
        create_goal,
        target_monthly=body.target_monthly,
        target_annual=body.target_annual,
        currency=body.currency,
        deadline=body.deadline,
        notes=body.notes,
    )
    return goal


@router.put("/dividend-goals/{goal_id}", response_model=DividendGoalResponse)
async def update_dividend_goal(goal_id: str, body: DividendGoalUpdate):
    """Update an existing dividend income goal."""
    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = await asyncio.to_thread(update_goal, goal_id, **kwargs)
    if not updated:
        raise HTTPException(status_code=404, detail="Goal not found")
    return updated


@router.delete("/dividend-goals/{goal_id}")
async def delete_dividend_goal(goal_id: str):
    """Delete a dividend income goal."""
    deleted = await asyncio.to_thread(delete_goal, goal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"status": "ok", "deleted": goal_id}
