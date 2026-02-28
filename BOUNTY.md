# AgentForge — $500 Bounty Submission: Dividend Income Investor Feature

## Customer Niche

**FIRE (Financial Independence, Retire Early) Dividend Income Investors**

This is a 2M+ member community across Reddit (r/dividends, r/FIRE), Seeking Alpha, and dedicated forums. Their core question: **"How much passive income does my portfolio generate, and when will I reach financial independence?"**

### Why This Customer?

Ghostfolio tracks past dividend transactions — but provides zero forward-looking dividend features. There is no upcoming payment calendar, no income projections, and no goal tracking. FIRE investors need to know:

1. When their next dividend payments arrive (cash flow planning)
2. How much annual passive income their portfolio generates
3. Whether they're on track to hit their income replacement goal
4. Which stocks offer the best dividend characteristics

AgentForge now answers all four questions through natural language.

## New Data Source: yfinance

**Library**: `yfinance` (Python, open-source, no API key required)

**Data provided**:
- Dividend yield, annual dividend rate, payout ratio
- Ex-dividend dates (upcoming and historical)
- 5-year average yield and dividend growth history
- Current market price for income calculations

**Why yfinance?** Free, no rate limits for personal use, covers all US-listed stocks plus many international markets. Ghostfolio tracks what you own; yfinance provides the forward-looking dividend data Ghostfolio lacks.

## Stateful CRUD Operations

### SQLite Database (`data/agentforge.db`)

Two tables managed via SQLAlchemy:

**`dividend_goals`** — Income targets the user sets and tracks against:
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| target_monthly | float | Monthly income target (e.g., $3,000) |
| target_annual | float | Annual target (auto-computed if not provided) |
| currency | string | Currency code |
| deadline | string | Target date (e.g., "2028-12-31") |
| notes | text | Free-form notes |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**`dividend_watchlist`** — Stocks the user is watching for dividend characteristics:
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| symbol | string | Ticker symbol |
| dividend_yield | float | Yield snapshot at add time |
| annual_dividend | float | Annual dividend snapshot |
| notes | text | Free-form notes |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

### CRUD Operations

All operations accessible via both:
- **Agent tools** (natural language): "Set a $2000/month income goal", "Delete my goal"
- **REST API** (programmatic): `GET/POST/PUT/DELETE /api/agent/dividend-goals`

| Operation | Agent Tool | REST Endpoint |
|-----------|-----------|---------------|
| Create goal | `dividend_goal_manager(action="create")` | `POST /api/agent/dividend-goals` |
| Read goals | `dividend_goal_manager(action="list")` | `GET /api/agent/dividend-goals` |
| Update goal | `dividend_goal_manager(action="update")` | `PUT /api/agent/dividend-goals/{id}` |
| Delete goal | `dividend_goal_manager(action="delete")` | `DELETE /api/agent/dividend-goals/{id}` |

## New Agent Tools (4)

### 1. `dividend_calendar`
**Trigger**: "When are my next dividends?", "dividend calendar"
- Fetches portfolio holdings from Ghostfolio
- Looks up upcoming ex-dividend dates via yfinance
- Returns sorted list of upcoming payments with estimated amounts

### 2. `dividend_income_projection`
**Trigger**: "How much dividend income?", "projected passive income"
- Fetches holdings and position values from Ghostfolio
- Calculates projected annual/monthly income using yfinance dividend rates
- Cross-references against saved goals to show progress percentage

### 3. `dividend_goal_manager`
**Trigger**: "Set an income goal", "show my goals", "delete my goal"
- Full CRUD for dividend income goals stored in SQLite
- Supports create, list, update, delete operations
- Auto-computes annual from monthly (and vice versa)

### 4. `dividend_screener`
**Trigger**: "What's JNJ's dividend yield?", "screen stocks for dividends"
- Looks up any stock's dividend metrics via yfinance
- Returns yield, payout ratio, ex-date, 5-year growth rate, payment history
- Supports multi-stock lookup (comma-separated symbols)

## Architecture

```
User: "How much passive income does my portfolio generate?"
  │
  ├─ classify_query() → query_type: "dividend"
  ├─ call_model() → selects dividend_income_projection tool
  ├─ dividend_income_projection:
  │   ├─ GhostfolioClient.get_portfolio_details() → holdings + values
  │   ├─ DividendClient.get_projected_annual_income() → yfinance data
  │   └─ database.get_goals() → SQLite goal progress
  ├─ verify_response() → confidence score
  └─ Response: "Your portfolio generates ~$8,400/year ($700/month).
               You're 35% toward your $2,000/month goal."
```

## Impact

This feature transforms Ghostfolio from a **backward-looking transaction tracker** into a **forward-looking income planner**. FIRE investors can now:

1. **Plan cash flow** — know exactly when dividend payments arrive
2. **Track progress** — see how close they are to income replacement
3. **Set goals** — define and monitor income targets over time
4. **Research stocks** — screen any stock for dividend quality before buying

## Files Changed

| File | Change |
|------|--------|
| `agent/requirements.txt` | Added yfinance, sqlalchemy |
| `agent/config.py` | Added DB_PATH config |
| `agent/database.py` | **NEW** — SQLAlchemy models + CRUD helpers |
| `agent/dividend_client.py` | **NEW** — yfinance wrapper |
| `agent/tools/dividend_calendar.py` | **NEW** — Upcoming dividends tool |
| `agent/tools/dividend_income.py` | **NEW** — Income projection tool |
| `agent/tools/dividend_goals.py` | **NEW** — Goal CRUD tool |
| `agent/tools/dividend_screener.py` | **NEW** — Stock dividend lookup tool |
| `agent/tools/__init__.py` | Registered 4 new tools |
| `agent/prompts/system.py` | Added dividend capabilities |
| `agent/graph.py` | Added "dividend" query_type |
| `agent/router.py` | Added REST CRUD endpoints |
| `agent/main.py` | Init DB on startup |
| `evals/datasets/full_suite.json` | Added 8 dividend eval cases |
| `BOUNTY.md` | This document |

## Eval Coverage

8 new test cases covering:
- Happy path: calendar, projection, goal CRUD, screener (DIV_001–005, 008)
- Multi-step: income vs goal comparison (DIV_006)
- Edge case: non-dividend stock handling (DIV_007)
