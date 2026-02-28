"""AgentForge — FastAPI entry point for the financial AI agent."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load .env BEFORE any other agent imports so env vars are available
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.router import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    from agent.database import init_db
    init_db()
    yield


app = FastAPI(
    title="AgentForge",
    description="Production-ready financial AI agent for Ghostfolio",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/api/agent")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agentforge"}
