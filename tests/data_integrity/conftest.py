# tests/data_integrity/conftest.py
"""
input: config.DATABASE_PATH
output: db_session, db_engine, execute_check, execute_query
pos: 为数据完整性测试提供数据库连接和查询工具

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import DATABASE_PATH


@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for the test session."""
    engine = create_engine(f"sqlite:///{DATABASE_PATH}")
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
