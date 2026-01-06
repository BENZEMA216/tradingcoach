# tests/data_integrity/conftest.py
"""
input: tests/fixtures/test_data.sql (测试模式) 或 config.DATABASE_PATH (生产监控模式)
output: db_session, db_engine, execute_check, execute_query
pos: 为数据完整性测试提供数据库连接和查询工具

模式说明:
- 默认: 使用内存数据库 + 固定测试数据 (CI/CD 友好)
- --use-production-db: 使用生产数据库 (数据质量监控)

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models import Base
from config import DATABASE_PATH

# 测试数据路径
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
TEST_DATA_SQL = FIXTURES_DIR / "test_data.sql"


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--use-production-db",
        action="store_true",
        default=False,
        help="使用生产数据库进行数据质量监控（默认使用测试数据）",
    )


@pytest.fixture(scope="session")
def use_production_db(request):
    """检查是否使用生产数据库"""
    return request.config.getoption("--use-production-db")


@pytest.fixture(scope="session")
def db_engine(use_production_db):
    """Create database engine for the test session."""
    if use_production_db:
        # 生产模式：连接实际数据库
        engine = create_engine(f"sqlite:///{DATABASE_PATH}")
    else:
        # 测试模式：使用内存数据库
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        # 创建表结构
        Base.metadata.create_all(bind=engine)

        # 加载测试数据
        if TEST_DATA_SQL.exists():
            with engine.connect() as conn:
                with open(TEST_DATA_SQL, 'r') as f:
                    # 分离多条 SQL 语句执行
                    sql_script = f.read()
                    for statement in sql_script.split(';'):
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            try:
                                conn.execute(text(statement))
                            except Exception as e:
                                # 跳过注释和空语句
                                if 'syntax error' not in str(e).lower():
                                    pass
                conn.commit()

    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="session")
def db_connection(db_engine):
    """Create a database connection for raw SQL queries."""
    connection = db_engine.connect()
    yield connection
    connection.close()


def execute_check(session, sql: str) -> int:
    """Execute a SQL check and return the count."""
    result = session.execute(text(sql)).scalar()
    return result if result else 0


def execute_query(session, sql: str):
    """Execute a SQL query and return all results."""
    return session.execute(text(sql)).fetchall()
