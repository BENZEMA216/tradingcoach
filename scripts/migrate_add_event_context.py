#!/usr/bin/env python3
"""
input: config.DATABASE_PATH, src/models/event_context.py
output: 数据库中新增 event_context 表
pos: 数据库迁移脚本 - 添加事件上下文表

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

用法:
    python scripts/migrate_add_event_context.py              # 执行迁移
    python scripts/migrate_add_event_context.py --dry-run    # 预览迁移
    python scripts/migrate_add_event_context.py --verify     # 验证表结构
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from config import DATABASE_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# SQL for creating the event_context table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS event_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 关联信息
    position_id INTEGER REFERENCES positions(id),
    symbol VARCHAR(50) NOT NULL,
    underlying_symbol VARCHAR(50),

    -- 事件基本信息
    event_type VARCHAR(30) NOT NULL,
    event_date DATE NOT NULL,
    event_time DATETIME,
    event_title VARCHAR(500) NOT NULL,
    event_description TEXT,

    -- 事件影响评估
    event_impact VARCHAR(20) DEFAULT 'unknown',
    event_importance INTEGER DEFAULT 5,
    is_surprise BOOLEAN DEFAULT 0,
    surprise_direction VARCHAR(20),
    surprise_magnitude NUMERIC(10, 4),

    -- 市场反应指标
    price_before NUMERIC(15, 4),
    price_after NUMERIC(15, 4),
    price_change NUMERIC(15, 4),
    price_change_pct NUMERIC(10, 4),
    event_day_high NUMERIC(15, 4),
    event_day_low NUMERIC(15, 4),
    event_day_range_pct NUMERIC(10, 4),

    -- 成交量
    volume_on_event NUMERIC(20, 0),
    volume_avg_20d NUMERIC(20, 0),
    volume_spike NUMERIC(10, 2),

    -- 波动率
    volatility_before NUMERIC(10, 4),
    volatility_after NUMERIC(10, 4),
    volatility_spike NUMERIC(10, 4),

    -- 跳空
    gap_pct NUMERIC(10, 4),

    -- 持仓影响
    position_pnl_on_event NUMERIC(20, 2),
    position_pnl_pct_on_event NUMERIC(10, 4),
    pnl_5d_before NUMERIC(20, 2),
    pnl_5d_after NUMERIC(20, 2),

    -- 数据来源
    source VARCHAR(50),
    source_url VARCHAR(500),
    source_data JSON,
    confidence NUMERIC(5, 2) DEFAULT 100,

    -- 关联
    event_group_id VARCHAR(50),
    market_env_id INTEGER REFERENCES market_environment(id),

    -- 用户标记
    user_notes TEXT,
    is_key_event BOOLEAN DEFAULT 0,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS ix_event_context_position_id ON event_context(position_id);",
    "CREATE INDEX IF NOT EXISTS ix_event_context_symbol ON event_context(symbol);",
    "CREATE INDEX IF NOT EXISTS ix_event_context_underlying_symbol ON event_context(underlying_symbol);",
    "CREATE INDEX IF NOT EXISTS ix_event_context_event_type ON event_context(event_type);",
    "CREATE INDEX IF NOT EXISTS ix_event_context_event_date ON event_context(event_date);",
    "CREATE INDEX IF NOT EXISTS ix_event_symbol_date ON event_context(symbol, event_date);",
    "CREATE INDEX IF NOT EXISTS ix_event_type_date ON event_context(event_type, event_date);",
    "CREATE INDEX IF NOT EXISTS ix_event_position_date ON event_context(position_id, event_date);",
    "CREATE INDEX IF NOT EXISTS ix_event_importance ON event_context(event_importance, event_date);",
    "CREATE INDEX IF NOT EXISTS ix_event_group_id ON event_context(event_group_id);",
    "CREATE INDEX IF NOT EXISTS ix_event_is_key_event ON event_context(is_key_event);",
]


def table_exists(engine, table_name: str) -> bool:
    """检查表是否存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def get_table_columns(engine, table_name: str) -> list:
    """获取表的列信息"""
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return []
    return [col['name'] for col in inspector.get_columns(table_name)]


def migrate(dry_run: bool = False):
    """执行迁移"""
    engine = create_engine(f"sqlite:///{DATABASE_PATH}")

    if table_exists(engine, 'event_context'):
        logger.info("event_context 表已存在，检查是否需要更新...")
        existing_cols = get_table_columns(engine, 'event_context')
        logger.info(f"现有列: {existing_cols}")
        logger.info("迁移完成（表已存在）")
        return True

    if dry_run:
        logger.info("=== 预览模式 ===")
        logger.info("将创建 event_context 表")
        logger.info("SQL:")
        logger.info(CREATE_TABLE_SQL)
        logger.info("\n索引:")
        for idx_sql in CREATE_INDEXES_SQL:
            logger.info(f"  {idx_sql}")
        return True

    logger.info("创建 event_context 表...")

    with engine.connect() as conn:
        # 创建表
        conn.execute(text(CREATE_TABLE_SQL))

        # 创建索引
        for idx_sql in CREATE_INDEXES_SQL:
            conn.execute(text(idx_sql))

        conn.commit()

    logger.info("event_context 表创建成功")
    return True


def verify():
    """验证表结构"""
    engine = create_engine(f"sqlite:///{DATABASE_PATH}")

    if not table_exists(engine, 'event_context'):
        logger.error("event_context 表不存在")
        return False

    expected_columns = [
        'id', 'position_id', 'symbol', 'underlying_symbol',
        'event_type', 'event_date', 'event_time', 'event_title', 'event_description',
        'event_impact', 'event_importance', 'is_surprise', 'surprise_direction', 'surprise_magnitude',
        'price_before', 'price_after', 'price_change', 'price_change_pct',
        'event_day_high', 'event_day_low', 'event_day_range_pct',
        'volume_on_event', 'volume_avg_20d', 'volume_spike',
        'volatility_before', 'volatility_after', 'volatility_spike',
        'gap_pct',
        'position_pnl_on_event', 'position_pnl_pct_on_event', 'pnl_5d_before', 'pnl_5d_after',
        'source', 'source_url', 'source_data', 'confidence',
        'event_group_id', 'market_env_id',
        'user_notes', 'is_key_event',
        'created_at', 'updated_at'
    ]

    actual_columns = get_table_columns(engine, 'event_context')

    missing = set(expected_columns) - set(actual_columns)
    extra = set(actual_columns) - set(expected_columns)

    if missing:
        logger.warning(f"缺失列: {missing}")
    if extra:
        logger.info(f"额外列: {extra}")

    logger.info(f"表 event_context 共有 {len(actual_columns)} 列")

    # 检查索引
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='event_context'"
        )).fetchall()
        indexes = [r[0] for r in result if r[0]]
        logger.info(f"索引: {indexes}")

    if not missing:
        logger.info("✓ 表结构验证通过")
        return True
    else:
        logger.error("✗ 表结构验证失败")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="添加 event_context 表迁移脚本"
    )
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    parser.add_argument('--verify', action='store_true', help='验证表结构')

    args = parser.parse_args()

    if args.verify:
        success = verify()
        sys.exit(0 if success else 1)

    success = migrate(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
