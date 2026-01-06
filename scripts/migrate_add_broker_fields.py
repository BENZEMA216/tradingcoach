"""
数据库迁移脚本 - 添加券商和导入追踪字段

添加字段:
- broker_id: 券商ID
- import_batch_id: 导入批次ID
- source_row_number: 原始CSV行号

运行: python scripts/migrate_add_broker_fields.py
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_PATH


def migrate():
    """执行迁移"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 获取现有列
    cursor.execute("PRAGMA table_info(trades)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    print(f"现有列数: {len(existing_columns)}")

    # 需要添加的列
    new_columns = [
        ("broker_id", "VARCHAR(50)", "券商ID"),
        ("import_batch_id", "VARCHAR(64)", "导入批次ID"),
        ("source_row_number", "INTEGER", "原始CSV行号"),
    ]

    added = 0
    for col_name, col_type, comment in new_columns:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}")
                print(f"  + 添加列: {col_name} ({comment})")
                added += 1
            except sqlite3.OperationalError as e:
                print(f"  ! 添加 {col_name} 失败: {e}")
        else:
            print(f"  - 列已存在: {col_name}")

    # 创建索引
    indexes = [
        ("idx_broker_trade_date", "trades", "broker_id, trade_date"),
        ("idx_import_batch", "trades", "import_batch_id"),
    ]

    for idx_name, table, columns in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({columns})")
            print(f"  + 创建索引: {idx_name}")
        except sqlite3.OperationalError as e:
            print(f"  ! 创建索引 {idx_name} 失败: {e}")

    conn.commit()
    conn.close()

    print(f"\n迁移完成: 添加 {added} 列")


if __name__ == "__main__":
    print("=" * 50)
    print("数据库迁移: 添加券商和导入追踪字段")
    print("=" * 50)
    migrate()
