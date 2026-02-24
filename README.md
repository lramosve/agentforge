# AgentForge

Production-ready financial AI agent with chat widget, evaluation framework, and observability — built for [Ghostfolio](https://github.com/ghostfolio/ghostfolio).

## Architecture

```
agentforge/
├── agent/              # LangGraph agent backend (Python/FastAPI)
│   ├── tools/          # 7 domain-specific finance tools
│   ├── verification/   # Fact-checking, hallucination detection, confidence scoring
│   └── prompts/        # System prompts and prompt templates
├── widget/             # Chat widget UI component (Angular)
│   └── src/
│       ├── components/ # Angular chat components
│       └── styles/     # Widget styles
├── evals/              # Evaluation framework
│   ├── datasets/       # 50+ test cases (happy path, edge, adversarial, multi-step)
│   └── results/        # Eval run outputs
├── observability/      # Langfuse integration and dashboards
├── tests/              # Test suites
│   ├── unit/           # Unit tests for individual tools
│   ├── integration/    # End-to-end agent flow tests
│   └── adversarial/    # Security and prompt injection tests
└── docs/               # Architecture docs, API reference, contributing guide
```

## Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | LangGraph |
| LLM | Claude Sonnet 4.6 / Claude Haiku 4.5 |
| Backend | Python / FastAPI |
| Chat Widget | Angular |
| Observability | Langfuse |
| Evals | Langfuse Evals + Custom Framework |
| Deployment | Vercel (widget) + Railway (agent) |

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

## Quick Start

### Agent Backend

```bash
cd agent
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # Add your API keys
uvicorn main:app --reload
```

### Widget (for Ghostfolio integration)

```bash
cd widget
npm install
npm run build
```

## Evaluation

```bash
cd evals
python run_evals.py --dataset datasets/full_suite.json --output results/
```

## Performance Targets

| Metric | Target |
|--------|--------|
| End-to-end latency (single tool) | < 5 seconds |
| Multi-step latency (3+ tools) | < 15 seconds |
| Tool success rate | > 95% |
| Eval pass rate | > 80% |
| Hallucination rate | < 5% |

## Integration with Ghostfolio

This package is designed as a standalone agent that integrates with Ghostfolio's REST API. See the [Ghostfolio fork](https://github.com/lramosve/ghostfolio) for integration code.

## License

AGPL-3.0 — matching Ghostfolio's license for compatibility.
