"""
迁移脚本：为 trades 表添加 A 股相关字段

input: 现有数据库 trades 表
output: 添加 7 个新列（exchange, seat_code, shareholder_code, transfer_fee, handling_fee, regulation_fee, other_fees）
pos: 数据库迁移脚本 - 一次性执行

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
from pathlib import Path
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from sqlalchemy import text
from src.models.base import init_database, get_engine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 需要添加的新列
NEW_COLUMNS = [
    # A股交易所和账户信息
    ("exchange", "VARCHAR(10)", "交易所代码（sse=上交所, szse=深交所）"),
    ("seat_code", "VARCHAR(20)", "席位代码/营业部代码"),
    ("shareholder_code", "VARCHAR(30)", "股东代码/证券账号"),
    # A股费用字段
    ("transfer_fee", "NUMERIC(10, 4)", "过户费（A股，万分之0.1）"),
    ("handling_fee", "NUMERIC(10, 4)", "经手费（交易所收取）"),
    ("regulation_fee", "NUMERIC(10, 4)", "证管费（证监会收取）"),
    ("other_fees", "NUMERIC(10, 4)", "其他费用"),
]


def get_existing_columns(engine, table_name: str) -> set:
    """获取表的现有列名"""
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        return {row[1] for row in result}


def add_column(engine, table_name: str, column_name: str, column_type: str, comment: str, dry_run: bool = False):
    """添加单个列"""
    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"

    if dry_run:
        logger.info(f"[DRY RUN] 将执行: {sql}")
        logger.info(f"  → 说明: {comment}")
    else:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        logger.info(f"已添加列: {column_name} ({column_type}) - {comment}")


def migrate_trades_table(dry_run: bool = False):
    """
    迁移 trades 表，添加 A 股相关字段

    Args:
        dry_run: 如果为 True，只打印要执行的 SQL，不实际修改
    """
    logger.info("=" * 60)
    logger.info("迁移 trades 表：添加 A 股相关字段")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 60)

    # 初始化数据库
    engine = init_database(config.DATABASE_URL, echo=False)

    # 获取现有列
    existing_columns = get_existing_columns(engine, "trades")
    logger.info(f"trades 表现有 {len(existing_columns)} 列")

    # 检查需要添加的列
    columns_to_add = []
    columns_exist = []

    for col_name, col_type, comment in NEW_COLUMNS:
        if col_name in existing_columns:
            columns_exist.append(col_name)
        else:
            columns_to_add.append((col_name, col_type, comment))

    if columns_exist:
        logger.info(f"以下列已存在: {', '.join(columns_exist)}")

    if not columns_to_add:
        logger.info("无需迁移，所有列已存在")
        return

    logger.info(f"需要添加 {len(columns_to_add)} 个新列")

    # 添加新列
    added = 0
    failed = 0

    for col_name, col_type, comment in columns_to_add:
        try:
            add_column(engine, "trades", col_name, col_type, comment, dry_run)
            added += 1
        except Exception as e:
            logger.error(f"添加列 {col_name} 失败: {e}")
            failed += 1

    # 打印摘要
    logger.info("\n" + "=" * 60)
    logger.info("迁移摘要")
    logger.info("=" * 60)
    logger.info(f"计划添加:  {len(columns_to_add)}")
    logger.info(f"成功添加:  {added}")
    logger.info(f"添加失败:  {failed}")
    logger.info(f"已存在跳过: {len(columns_exist)}")
    logger.info("=" * 60)


def verify_migration():
    """验证迁移结果"""
    logger.info("\n验证迁移结果...")

    engine = init_database(config.DATABASE_URL, echo=False)
    existing_columns = get_existing_columns(engine, "trades")

    missing = []
    present = []

    for col_name, _, _ in NEW_COLUMNS:
        if col_name in existing_columns:
            present.append(col_name)
        else:
            missing.append(col_name)

    logger.info(f"trades 表总列数: {len(existing_columns)}")
    logger.info(f"新列已存在: {len(present)}")

    if present:
        logger.info(f"  ✅ {', '.join(present)}")

    if missing:
        logger.warning(f"新列缺失: {len(missing)}")
        logger.warning(f"  ❌ {', '.join(missing)}")
    else:
        logger.info("✅ 所有新列已添加完成")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='迁移 trades 表添加 A 股字段')
    parser.add_argument('--dry-run', action='store_true', help='只打印要执行的 SQL')
    parser.add_argument('--verify', action='store_true', help='只验证当前状态')

    args = parser.parse_args()

    if args.verify:
        verify_migration()
    else:
        migrate_trades_table(dry_run=args.dry_run)
        if not args.dry_run:
            verify_migration()


if __name__ == '__main__':
    main()
