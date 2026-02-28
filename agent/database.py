"""SQLite database layer for stateful dividend features."""

import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from agent.config import config

Base = declarative_base()


class DividendGoal(Base):
    __tablename__ = "dividend_goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    target_monthly = Column(Float, nullable=False)
    target_annual = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    deadline = Column(String, nullable=True)
    notes = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DividendWatchlistItem(Base):
    __tablename__ = "dividend_watchlist"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String, nullable=False)
    dividend_yield = Column(Float, default=0.0)
    annual_dividend = Column(Float, default=0.0)
    notes = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


_engine = None
_SessionFactory = None


def init_db() -> None:
    """Create the database engine and tables. Ensures the data/ directory exists."""
    global _engine, _SessionFactory
    db_path = config.DB_PATH
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(_engine)
    _SessionFactory = sessionmaker(bind=_engine)


def get_session() -> Session:
    """Return a new SQLAlchemy session."""
    if _SessionFactory is None:
        init_db()
    return _SessionFactory()


# ---------------------------------------------------------------------------
# CRUD helpers — DividendGoal
# ---------------------------------------------------------------------------

def create_goal(
    target_monthly: float,
    target_annual: float = 0.0,
    currency: str = "USD",
    deadline: str = "",
    notes: str = "",
) -> dict:
    if target_annual == 0.0 and target_monthly > 0:
        target_annual = target_monthly * 12
    elif target_monthly == 0.0 and target_annual > 0:
        target_monthly = target_annual / 12

    with get_session() as session:
        goal = DividendGoal(
            target_monthly=target_monthly,
            target_annual=target_annual,
            currency=currency,
            deadline=deadline or None,
            notes=notes,
        )
        session.add(goal)
        session.commit()
        session.refresh(goal)
        return _goal_to_dict(goal)


def get_goals() -> list[dict]:
    with get_session() as session:
        goals = session.query(DividendGoal).order_by(DividendGoal.created_at.desc()).all()
        return [_goal_to_dict(g) for g in goals]


def update_goal(goal_id: str, **kwargs) -> dict | None:
    with get_session() as session:
        goal = session.query(DividendGoal).filter_by(id=goal_id).first()
        if not goal:
            return None
        for key, value in kwargs.items():
            if hasattr(goal, key) and value is not None:
                setattr(goal, key, value)
        goal.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(goal)
        return _goal_to_dict(goal)


def delete_goal(goal_id: str) -> bool:
    with get_session() as session:
        goal = session.query(DividendGoal).filter_by(id=goal_id).first()
        if not goal:
            return False
        session.delete(goal)
        session.commit()
        return True


# ---------------------------------------------------------------------------
# CRUD helpers — DividendWatchlistItem
# ---------------------------------------------------------------------------

def create_watchlist_item(
    symbol: str,
    dividend_yield: float = 0.0,
    annual_dividend: float = 0.0,
    notes: str = "",
) -> dict:
    with get_session() as session:
        item = DividendWatchlistItem(
            symbol=symbol.upper(),
            dividend_yield=dividend_yield,
            annual_dividend=annual_dividend,
            notes=notes,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        return _watchlist_to_dict(item)


def get_watchlist() -> list[dict]:
    with get_session() as session:
        items = session.query(DividendWatchlistItem).order_by(DividendWatchlistItem.created_at.desc()).all()
        return [_watchlist_to_dict(i) for i in items]


def delete_watchlist_item(item_id: str) -> bool:
    with get_session() as session:
        item = session.query(DividendWatchlistItem).filter_by(id=item_id).first()
        if not item:
            return False
        session.delete(item)
        session.commit()
        return True


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _goal_to_dict(goal: DividendGoal) -> dict:
    return {
        "id": goal.id,
        "target_monthly": goal.target_monthly,
        "target_annual": goal.target_annual,
        "currency": goal.currency,
        "deadline": goal.deadline or "",
        "notes": goal.notes or "",
        "created_at": goal.created_at.isoformat() if goal.created_at else "",
        "updated_at": goal.updated_at.isoformat() if goal.updated_at else "",
    }


def _watchlist_to_dict(item: DividendWatchlistItem) -> dict:
    return {
        "id": item.id,
        "symbol": item.symbol,
        "dividend_yield": item.dividend_yield,
        "annual_dividend": item.annual_dividend,
        "notes": item.notes or "",
        "created_at": item.created_at.isoformat() if item.created_at else "",
        "updated_at": item.updated_at.isoformat() if item.updated_at else "",
    }
