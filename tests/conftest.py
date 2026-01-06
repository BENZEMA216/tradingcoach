"""
Global Test Configuration - 全局测试配置

input: 项目模块
output: 全局 fixtures, 测试工具
pos: 测试基础设施根配置

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Base


# ==================== 数据库 Fixtures ====================

@pytest.fixture(scope="session")
def test_engine():
    """创建内存数据库引擎（session 级别共享）"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """创建测试数据库会话（每个测试隔离）"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ==================== API Client Fixtures ====================

@pytest.fixture(scope="function")
def client():
    """创建 FastAPI TestClient"""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.database import get_db

    # 使用内存数据库
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ==================== 工厂 Fixtures ====================

@pytest.fixture
def trade_factory():
    """提供 Trade 工厂"""
    from tests.factories import TradeFactory
    return TradeFactory


@pytest.fixture
def position_factory():
    """提供 Position 工厂"""
    from tests.factories import PositionFactory
    return PositionFactory


@pytest.fixture
def sample_trades(trade_factory):
    """生成示例交易列表"""
    return [trade_factory.build() for _ in range(10)]


@pytest.fixture
def sample_positions(position_factory):
    """生成示例持仓列表"""
    return [position_factory.build() for _ in range(10)]


# ==================== 辅助函数 ====================

def pytest_configure(config):
    """pytest 配置钩子"""
    # 添加自定义标记说明
    config.addinivalue_line("markers", "slow: 标记为慢速测试")
    config.addinivalue_line("markers", "benchmark: 性能基准测试")
    config.addinivalue_line("markers", "integration: API 集成测试")
    config.addinivalue_line("markers", "contract: 契约测试")


def pytest_collection_modifyitems(config, items):
    """根据标记修改测试收集"""
    # 如果没有指定 --run-slow，跳过 slow 测试
    if not config.getoption("--run-slow", default=False):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests",
    )
    parser.addoption(
        "--run-benchmark",
        action="store_true",
        default=False,
        help="run benchmark tests",
    )
