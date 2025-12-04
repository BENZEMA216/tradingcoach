"""
Database connection and session management
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Add project root to path to import existing models
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.base import Base
from src.models.trade import Trade
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData

from .config import settings

# Create engine with SQLite settings
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    Use with FastAPI's Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Re-export models for convenience
__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "Base",
    "Trade",
    "Position",
    "PositionStatus",
    "MarketData",
]
