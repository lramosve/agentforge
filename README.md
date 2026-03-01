# AgentForge

Production-ready financial AI agent with a chat widget, evaluation framework, and observability — built for [Ghostfolio](https://github.com/ghostfolio/ghostfolio).

**Live Demo**: [https://widget-blond-tau.vercel.app](https://widget-blond-tau.vercel.app)

---

## Architecture Overview

AgentForge follows a two-tier architecture: a **Python/FastAPI backend** running a LangGraph agent, and an **Angular 21 frontend** chat widget deployed independently.

```
                         ┌──────────────────────────────┐
                         │      Angular 21 Widget       │
                         │       (Vercel Deploy)        │
                         │                              │
                         │  ┌────────┐  ┌────────────┐  │
                         │  │ Chat   │  │ Conversation│  │
                         │  │ UI     │  │ Service     │  │
                         │  └───┬────┘  └────────────┘  │
                         │      │  SSE / REST            │
                         └──────┼───────────────────────┘
                                │
                    ┌───────────▼───────────────────────────┐
                    │        FastAPI Backend (Railway)       │
                    │                                       │
                    │  ┌─────────────────────────────────┐  │
                    │  │        LangGraph Agent           │  │
                    │  │                                  │  │
                    │  │  classify ─► agent ─► tools      │  │
                    │  │                │        │        │  │
                    │  │            verify ◄── collect    │  │
                    │  └─────────────────────────────────┘  │
                    │           │              │             │
                    │  ┌────────▼──┐   ┌──────▼──────────┐  │
                    │  │ Claude    │   │  11 Finance     │  │
                    │  │ Sonnet/   │   │  Tools          │  │
                    │  │ Haiku     │   │                 │  │
                    │  └───────────┘   └──────┬──────────┘  │
                    │                         │             │
                    │        ┌────────────────┼──────┐      │
                    │        │                │      │      │
                    │  ┌─────▼────┐  ┌───────▼┐  ┌──▼───┐  │
                    │  │Ghostfolio│  │yfinance│  │SQLite│  │
                    │  │  API     │  │        │  │  DB  │  │
                    │  └──────────┘  └────────┘  └──────┘  │
                    │                                       │
                    │         ┌──────────┐                  │
                    │         │ Langfuse │ (observability)  │
                    │         └──────────┘                  │
                    └───────────────────────────────────────┘
```

### Agent Pipeline

The LangGraph state machine processes each query through five nodes:

1. **Classify** — Categorize the query (general, dividend, tax, advice, compliance)
2. **Agent** — LLM reasoning with tool selection (Sonnet for initial pass, Haiku for summarization)
3. **Tools** — Execute selected tool(s) against data sources
4. **Collect** — Gather and structure tool results
5. **Verify** — Confidence scoring, fact-checking, and disclaimer injection

### Dual-Model Strategy

| Model | Role | Use Case |
|-------|------|----------|
| Claude Sonnet 4.6 | Primary | Initial reasoning, tool selection |
| Claude Haiku 4.5 | Fast | Summarization after tools return results |

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Agent Framework | LangGraph | >= 0.2.0 |
| LLM | Claude Sonnet 4.6 / Haiku 4.5 | Latest |
| Backend | Python / FastAPI | >= 0.115.0 |
| Frontend | Angular | 21.x |
| Database | SQLite + SQLAlchemy | >= 2.0.0 |
| Market Data | yfinance | >= 0.2.0 |
| Observability | Langfuse | >= 2.0.0 |
| Deployment | Vercel (widget) + Railway (backend) |

---

## Tools

| Tool | Description |
|------|-------------|
| `portfolio_analysis` | Holdings, allocation %, sector breakdown, total value |
| `portfolio_performance` | TWR, max drawdown, returns over date ranges |
| `market_data_lookup` | Current and historical prices for symbols |
| `transaction_history` | Activity log with categorization (BUY/SELL/DIVIDEND/FEE) |
| `tax_estimate` | Capital gains/losses and dividend income estimation |
| `compliance_check` | Concentration limits and diversification rule checks |
| `benchmark_comparison` | Portfolio vs benchmark performance comparison |
| `dividend_calendar` | Upcoming ex-dividend dates for portfolio holdings |
| `dividend_income_projection` | Projected annual/monthly passive income from dividends |
| `dividend_goal_manager` | CRUD operations for dividend income targets |
| `dividend_screener` | Dividend yield, payout ratio, growth history for any stock |

---

## Setup Guide

### Prerequisites

- Python 3.12+
- Node.js 20+
- An [Anthropic API key](https://console.anthropic.com/)
- A running [Ghostfolio](https://github.com/ghostfolio/ghostfolio) instance (or use Docker Compose below)
- (Optional) [Langfuse](https://langfuse.com/) account for observability

### Option 1: Docker Compose (Full Stack)

The fastest way to run everything locally, including Ghostfolio and its dependencies:

```bash
git clone https://github.com/lramosve/agentforge.git
cd agentforge

# Configure environment
cp agent/.env.example agent/.env
# Edit agent/.env and add your ANTHROPIC_API_KEY

# Start all services
docker-compose up
```

This starts:
- **Ghostfolio** at `http://localhost:3333`
- **AgentForge backend** at `http://localhost:8000`
- **PostgreSQL** at `localhost:5432`
- **Redis** at `localhost:6379`

### Option 2: Manual Setup

#### Backend

```bash
cd agent

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `agent/.env` with your credentials:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Ghostfolio connection
GHOSTFOLIO_API_URL=http://localhost:3333/api
GHOSTFOLIO_API_TOKEN=your-ghostfolio-token

# Optional: Langfuse observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Agent tuning (defaults shown)
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=30
AGENT_MAX_COST_USD=0.10
```

Start the backend:

```bash
uvicorn agent.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. Verify with:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

#### Frontend (Widget)

```bash
cd widget
npm install
```

For development (with hot reload):

```bash
npm start
# Opens at http://localhost:4200
```

For production build:

```bash
npm run build
# Output in dist/agentforge-widget/
```

> The widget connects to the backend URL configured in `widget/src/environments/environment.ts`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/agent/health` | Agent health status |
| `POST` | `/api/agent/chat` | Send message (synchronous response) |
| `POST` | `/api/agent/chat-stream` | Send message (SSE streaming response) |
| `GET` | `/api/agent/tools` | List available tools |
| `POST` | `/api/agent/feedback` | Submit feedback on a response |
| `GET` | `/api/agent/dividend-goals` | List dividend income goals |
| `POST` | `/api/agent/dividend-goals` | Create a dividend goal |
| `PUT` | `/api/agent/dividend-goals/{id}` | Update a dividend goal |
| `DELETE` | `/api/agent/dividend-goals/{id}` | Delete a dividend goal |

---

## Evaluation

Run the evaluation suite against the agent:

```bash
cd agentforge
python -m evals.run_evals --verbose
```

The suite includes 58 test cases across categories: happy path, edge cases, adversarial prompts, multi-step reasoning, and dividend features.

### Performance Targets

| Metric | Target |
|--------|--------|
| End-to-end latency (single tool) | < 5 seconds |
| Multi-step latency (3+ tools) | < 15 seconds |
| Tool success rate | > 95% |
| Eval pass rate | > 80% |
| Hallucination rate | < 5% |

---

## Project Structure

```
agentforge/
├── agent/                      # FastAPI backend
│   ├── tools/                  # 11 domain-specific finance tools
│   ├── verification/           # Fact-checking & confidence scoring
│   ├── prompts/                # System prompts
│   ├── main.py                 # FastAPI entry point
│   ├── graph.py                # LangGraph state machine
│   ├── router.py               # API route handlers
│   ├── config.py               # Environment-based configuration
│   ├── models.py               # Pydantic request/response models
│   ├── database.py             # SQLAlchemy models + CRUD helpers
│   ├── ghostfolio_client.py    # Ghostfolio REST API client
│   ├── dividend_client.py      # yfinance wrapper for market data
│   ├── observability.py        # Langfuse tracing integration
│   └── requirements.txt
├── widget/                     # Angular 21 chat widget
│   └── src/
│       ├── app/
│       │   ├── components/     # 9 standalone components
│       │   ├── services/       # AgentService, ConversationService, ExportService
│       │   └── models/         # TypeScript interfaces
│       └── styles/             # SCSS theming with --af-* CSS variables
├── evals/                      # Evaluation framework
│   ├── datasets/               # Test case definitions
│   │   └── full_suite.json     # 58 test cases
│   ├── results/                # Eval run outputs
│   └── run_evals.py            # Evaluation runner
├── docker-compose.yml          # Full-stack local development
├── Dockerfile                  # Backend container image
├── BOUNTY.md                   # Dividend feature documentation
└── README.md
```

---

## Deployment

### Backend (Railway)

The backend is deployed to [Railway](https://railway.app/) using the `Dockerfile`. Set the same environment variables from `.env.example` in the Railway dashboard.

### Widget (Vercel)

The Angular widget is deployed to [Vercel](https://vercel.com/). Deploy from the `widget/` directory:

```bash
cd widget
npx vercel --prod
```

---

## Integration with Ghostfolio

AgentForge is designed as a standalone agent that integrates with Ghostfolio's REST API. See the [Ghostfolio fork](https://github.com/lramosve/ghostfolio) for integration code.

---

## License

AGPL-3.0 — matching Ghostfolio's license for compatibility.
