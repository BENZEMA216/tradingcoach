"""
Database connection and session management

input: settings.DATABASE_URL, src.models.*
output: engine, SessionLocal, get_db FastAPI dependency, 自动建表
pos: 后端数据库层 - 应用启动即可用，冷启动自动 create_all
"""

import logging
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Add project root to path to import existing models
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Importing the package registers all models (Trade/Position/MarketData/ImportHistory/...)
# against Base.metadata so create_all() picks them up.
from src import models  # noqa: F401
from src.models.base import Base
from src.models.trade import Trade
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData

from .configuration import settings

logger = logging.getLogger(__name__)

# Create engine with SQLite settings
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables registered on Base.metadata if they don't exist.

    Idempotent — safe to call on every cold start (Docker / Railway / local).
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured via Base.metadata.create_all()")


# Ensure schema exists at import time so a cold container or fresh checkout
# does not 500 on the first request. SQLite's create_all is a no-op when the
# tables already exist.
init_db()


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
    "init_db",
    "Base",
    "Trade",
    "Position",
    "PositionStatus",
    "MarketData",
]
