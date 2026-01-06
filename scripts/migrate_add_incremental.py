#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加增量导入支持

新增:
1. trades 表添加 trade_fingerprint 字段
2. import_history 表（导入历史记录）
3. position_snapshots 表（持仓快照）
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
from datetime import datetime


def get_db_path():
    """获取数据库路径"""
    db_path = project_root / "data" / "tradingcoach.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    return str(db_path)


def check_column_exists(conn, table, column):
    """检查列是否存在"""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def check_table_exists(conn, table):
    """检查表是否存在"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None


def migrate_trades_table(conn):
    """给 trades 表添加 trade_fingerprint 字段"""
    print("\n--- Migrating trades table ---")

    if check_column_exists(conn, 'trades', 'trade_fingerprint'):
        print("  ✓ trade_fingerprint column already exists")
        return False

    print("  Adding trade_fingerprint column...")
    conn.execute("""
        ALTER TABLE trades
        ADD COLUMN trade_fingerprint VARCHAR(64)
    """)

    print("  Creating unique index on trade_fingerprint...")
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_trade_fingerprint
        ON trades(trade_fingerprint)
        WHERE trade_fingerprint IS NOT NULL
    """)

    print("  ✓ trades table migrated")
    return True


def create_import_history_table(conn):
    """创建导入历史表"""
    print("\n--- Creating import_history table ---")

    if check_table_exists(conn, 'import_history'):
        print("  ✓ import_history table already exists")
        return False

    conn.execute("""
        CREATE TABLE import_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_time DATETIME NOT NULL,
            file_name VARCHAR(255),
            file_hash VARCHAR(64),
            file_type VARCHAR(20),
            total_rows INTEGER,
            new_trades INTEGER,
            duplicates_skipped INTEGER,
            errors INTEGER DEFAULT 0,
            date_range_start DATE,
            date_range_end DATE,
            status VARCHAR(20),
            error_message TEXT,
            processing_time_ms INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE INDEX idx_import_history_time
        ON import_history(import_time)
    """)

    conn.execute("""
        CREATE INDEX idx_import_history_file_hash
        ON import_history(file_hash)
    """)

    print("  ✓ import_history table created")
    return True


def create_position_snapshots_table(conn):
    """创建持仓快照表"""
    print("\n--- Creating position_snapshots table ---")

    if check_table_exists(conn, 'position_snapshots'):
        print("  ✓ position_snapshots table already exists")
        return False

    conn.execute("""
        CREATE TABLE position_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date DATE NOT NULL,
            source VARCHAR(50),
            account_id VARCHAR(50),
            total_positions INTEGER,
            total_market_value NUMERIC(20, 2),
            total_unrealized_pnl NUMERIC(20, 2),
            positions_json JSON,
            status VARCHAR(20),
            reconciliation_report JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE INDEX idx_snapshot_date
        ON position_snapshots(snapshot_date)
    """)

    print("  ✓ position_snapshots table created")
    return True


def backfill_fingerprints(conn):
    """为现有交易生成指纹（可选）"""
    print("\n--- Checking existing trades ---")

    cursor = conn.execute("""
        SELECT COUNT(*) FROM trades
        WHERE trade_fingerprint IS NULL
    """)
    null_count = cursor.fetchone()[0]

    if null_count == 0:
        print("  ✓ All trades have fingerprints")
        return

    print(f"  Found {null_count} trades without fingerprints")
    print("  Note: Run the incremental importer to generate fingerprints for existing trades")


def main():
    print("=" * 60)
    print("Database Migration: Incremental Import Support")
    print("=" * 60)

    db_path = get_db_path()
    print(f"\nDatabase: {db_path}")

    conn = sqlite3.connect(db_path)

    try:
        changes = []

        # 执行迁移
        if migrate_trades_table(conn):
            changes.append("trades.trade_fingerprint")

        if create_import_history_table(conn):
            changes.append("import_history table")

        if create_position_snapshots_table(conn):
            changes.append("position_snapshots table")

        # 检查现有数据
        backfill_fingerprints(conn)

        # 提交事务
        conn.commit()

        print("\n" + "=" * 60)
        if changes:
            print("Migration completed successfully!")
            print("\nChanges made:")
            for change in changes:
                print(f"  + {change}")
        else:
            print("No changes needed - database is up to date")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
