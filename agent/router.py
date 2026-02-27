"""API router for agent endpoints."""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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
