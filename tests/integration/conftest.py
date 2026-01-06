"""
Integration test fixtures - 集成测试配置

input: backend/app/main.py, tests/factories.py
output: TestClient fixture, test database setup
pos: 集成测试基础设施 - 提供 FastAPI TestClient 和测试数据库

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models import Base
from backend.app.main import app
from backend.app.database import get_db


# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create in-memory test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with overridden database dependency."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_with_data(client, test_db):
    """Create test client with sample data loaded."""
    from tests.factories import PositionFactory, TradeFactory
    from src.models import Position, Trade
    from src.models.position import PositionStatus

    # Create sample positions
    for i in range(10):
        pos = PositionFactory.build()
        db_pos = Position(
            symbol=pos.symbol,
            symbol_name=pos.symbol_name,
            direction=pos.direction,
            status=PositionStatus.CLOSED,
            open_time=pos.open_time,
            close_time=pos.close_time,
            open_date=pos.open_date,
            close_date=pos.close_date,
            holding_period_days=pos.holding_period_days,
            open_price=pos.open_price,
            close_price=pos.close_price,
            quantity=pos.quantity,
            realized_pnl=pos.realized_pnl,
            net_pnl=pos.net_pnl,
            total_fees=pos.total_fees,
            overall_score=pos.overall_score,
            score_grade=pos.score_grade,
            entry_quality_score=pos.entry_quality_score,
            exit_quality_score=pos.exit_quality_score,
            trend_quality_score=pos.trend_quality_score,
            risk_mgmt_score=pos.risk_mgmt_score,
            market="美股",
            currency="USD",
        )
        test_db.add(db_pos)

    test_db.commit()

    return client
