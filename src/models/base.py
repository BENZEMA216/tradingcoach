"""
Database base configuration and session management

Supports per-thread database URLs so anonymous workspace imports can run
without leaking through the legacy global session helpers.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
import logging
import threading

# 配置日志
logger = logging.getLogger(__name__)

# 创建Base类
Base = declarative_base()

# 全局engine和session变量（保留给旧调用方）
_engine = None
_session_factory = None
_scoped_session = None
_session_registry = {}
_registry_lock = threading.RLock()
_thread_local = threading.local()


def init_database(database_url: str, echo: bool = False):
    """
    初始化数据库连接

    Args:
        database_url: 数据库连接URL
        echo: 是否打印SQL语句（调试用）

    Returns:
        engine: SQLAlchemy Engine对象
    """
    global _engine, _session_factory, _scoped_session

    with _registry_lock:
        logger.info(f"Initializing database: {database_url}")

        entry = _session_registry.get(database_url)
        if entry is None:
            # 创建engine
            # 对于SQLite，使用StaticPool避免多线程问题
            if database_url.startswith('sqlite'):
                engine = create_engine(
                    database_url,
                    echo=echo,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool
                )
            else:
                engine = create_engine(
                    database_url,
                    echo=echo,
                    pool_size=5,
                    pool_recycle=3600
                )

            # 创建session factory
            session_factory = sessionmaker(bind=engine)
            scoped = scoped_session(session_factory)
            entry = (engine, session_factory, scoped)
            _session_registry[database_url] = entry

        _engine, _session_factory, _scoped_session = entry
        _thread_local.database_url = database_url

        logger.info("Database initialized successfully")
        return _engine


def get_engine():
    """获取数据库engine"""
    current_url = getattr(_thread_local, "database_url", None)
    if current_url and current_url in _session_registry:
        return _session_registry[current_url][0]
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


def get_session():
    """
    获取数据库session（线程安全）

    Returns:
        Session: SQLAlchemy Session对象
    """
    current_url = getattr(_thread_local, "database_url", None)
    if current_url and current_url in _session_registry:
        return _session_registry[current_url][2]()
    if _scoped_session is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _scoped_session()


def create_all_tables():
    """创建所有表"""
    logger.info("Creating all tables...")
    Base.metadata.create_all(get_engine())
    logger.info("All tables created successfully")


def drop_all_tables():
    """删除所有表（谨慎使用！）"""
    logger.warning("Dropping all tables...")
    Base.metadata.drop_all(get_engine())
    logger.warning("All tables dropped")


def close_session():
    """关闭当前session"""
    current_url = getattr(_thread_local, "database_url", None)
    if current_url and current_url in _session_registry:
        _session_registry[current_url][2].remove()
    elif _scoped_session is not None:
        _scoped_session.remove()
