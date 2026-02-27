"""AgentForge — FastAPI entry point for the financial AI agent."""

import base64
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load .env BEFORE any other agent imports so env vars are available
load_dotenv()

# Configure OTEL exporter for Langfuse v3 — must happen before OTEL/langfuse imports
_lf_pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
_lf_sk = os.getenv("LANGFUSE_SECRET_KEY", "")
_lf_host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
if _lf_pk and _lf_sk:
    _auth = base64.b64encode(f"{_lf_pk}:{_lf_sk}".encode()).decode()
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", f"{_lf_host.rstrip('/')}/api/public/otel")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_HEADERS", f"Authorization=Basic {_auth}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.router import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
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
