"""
数据库迁移脚本 - 添加新评分字段

新增字段:
- market_env_score: 市场环境评分
- behavior_score: 交易行为评分
- execution_score: 执行质量评分
- options_greeks_score: 期权希腊字母评分
- score_details: 评分详情 (JSON)
- behavior_analysis: 行为分析 (JSON)

新增表:
- market_snapshots: 市场快照表
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import DATABASE_PATH


def migrate():
    """执行数据库迁移"""
    print(f"Connecting to database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # ==================== 1. 添加 positions 表新字段 ====================

    new_columns = [
        ("market_env_score", "REAL", "市场环境评分 (0-100)"),
        ("behavior_score", "REAL", "交易行为评分 (0-100)"),
        ("execution_score", "REAL", "执行质量评分 (0-100)"),
        ("options_greeks_score", "REAL", "期权希腊字母评分 (0-100)"),
        ("score_details", "TEXT", "评分详情 (JSON)"),
        ("behavior_analysis", "TEXT", "行为分析结果 (JSON)"),
    ]

    # 检查现有列
    cursor.execute("PRAGMA table_info(positions)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    for col_name, col_type, comment in new_columns:
        if col_name not in existing_columns:
            print(f"Adding column: {col_name} ({col_type}) - {comment}")
            cursor.execute(f"ALTER TABLE positions ADD COLUMN {col_name} {col_type}")
        else:
            print(f"Column already exists: {col_name}")

    # ==================== 2. 创建 market_snapshots 表 ====================

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='market_snapshots'
    """)

    if not cursor.fetchone():
        print("Creating table: market_snapshots")
        cursor.execute("""
            CREATE TABLE market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,

                -- VIX 数据
                vix_close REAL,
                vix_ma5 REAL,
                vix_ma20 REAL,

                -- SPY 数据
                spy_close REAL,
                spy_ma5 REAL,
                spy_ma20 REAL,
                spy_ma50 REAL,
                spy_rsi_14 REAL,
                spy_change_pct REAL,

                -- QQQ 数据
                qqq_close REAL,
                qqq_change_pct REAL,

                -- 市场状态
                market_trend TEXT,  -- bullish/bearish/neutral
                volatility_regime TEXT,  -- low/medium/high/extreme

                -- 板块表现 (JSON)
                sector_performance TEXT,

                -- 特殊日期标记
                is_fomc_day INTEGER DEFAULT 0,
                is_opex_day INTEGER DEFAULT 0,
                is_earnings_season INTEGER DEFAULT 0,

                -- 时间戳
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(date)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_snapshots_date
            ON market_snapshots(date)
        """)
    else:
        print("Table already exists: market_snapshots")

    # ==================== 3. 创建新索引 ====================

    indexes = [
        ("idx_pos_market_env_score", "positions", "market_env_score"),
        ("idx_pos_behavior_score", "positions", "behavior_score"),
        ("idx_pos_execution_score", "positions", "execution_score"),
    ]

    for idx_name, table, column in indexes:
        try:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})
            """)
            print(f"Created index: {idx_name}")
        except sqlite3.OperationalError as e:
            print(f"Index {idx_name} already exists or error: {e}")

    # ==================== 4. 提交更改 ====================

    conn.commit()
    print("\nMigration completed successfully!")

    # 验证
    print("\n=== Verification ===")
    cursor.execute("PRAGMA table_info(positions)")
    columns = cursor.fetchall()
    print(f"Positions table columns: {len(columns)}")

    new_cols = [c[1] for c in columns if c[1] in [col[0] for col in new_columns]]
    print(f"New columns added: {new_cols}")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")

    conn.close()


def rollback():
    """回滚迁移（谨慎使用）"""
    print("WARNING: This will remove newly added columns!")
    confirm = input("Type 'YES' to confirm: ")

    if confirm != 'YES':
        print("Rollback cancelled")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # SQLite 不支持 DROP COLUMN，需要重建表
    # 这里只删除 market_snapshots 表
    cursor.execute("DROP TABLE IF EXISTS market_snapshots")
    print("Dropped table: market_snapshots")

    conn.commit()
    conn.close()
    print("Rollback completed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database migration for scoring system")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
