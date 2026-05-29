"""
Database connection and session management

input: settings.DATABASE_URL, optional X-Workspace-Token, src.models.*
output: engine, SessionLocal, workspace-aware get_db dependency, 自动建表
pos: 后端数据库层 - 应用启动即可用，支持匿名 workspace 数据隔离
"""

import logging
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import threading

from fastapi import HTTPException, Request, status

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
from .services.workspace_service import workspace_service

logger = logging.getLogger(__name__)

# Create engine with SQLite settings
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_session_factory_cache: dict[str, sessionmaker] = {}
_session_factory_lock = threading.RLock()
_EMPTY_DATABASE_URL = "sqlite:///:memory:"


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


def get_session_factory_for_database_url(database_url: str) -> sessionmaker:
    """Return a cached session factory for a database URL and ensure schema exists."""
    with _session_factory_lock:
        cached = _session_factory_cache.get(database_url)
        if cached is not None:
            return cached

        kwargs = {}
        if database_url.startswith("sqlite"):
            kwargs = {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            }

        scoped_engine = create_engine(database_url, echo=settings.DEBUG, **kwargs)
        Base.metadata.create_all(bind=scoped_engine)
        factory = sessionmaker(autocommit=False, autoflush=False, bind=scoped_engine)
        _session_factory_cache[database_url] = factory
        return factory


def get_db(request: Request = None) -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    Use with FastAPI's Depends().
    """
    database_url = settings.DATABASE_URL

    if request is not None:
        workspace_token = request.headers.get("X-Workspace-Token")
        if workspace_token:
            workspace = workspace_service.resolve_token(workspace_token)
            if workspace is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired workspace token.",
                )
            database_url = workspace.database_url
        else:
            # Product Hunt beta must not fall back to the developer/global DB
            # when a visitor has not created a workspace yet.
            database_url = _EMPTY_DATABASE_URL

    factory = SessionLocal if database_url == settings.DATABASE_URL else get_session_factory_for_database_url(database_url)
    db = factory()
    try:
        yield db
    finally:
        db.close()


# Re-export models for convenience
__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "get_session_factory_for_database_url",
    "init_db",
    "Base",
    "Trade",
    "Position",
    "PositionStatus",
    "MarketData",
]
