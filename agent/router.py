"""API router for agent endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.graph import run_agent

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


@router.get("/health")
async def agent_health():
    return {"status": "ok", "agent": "agentforge"}
