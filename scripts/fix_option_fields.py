"""
修复期权持仓字段

input: 数据库中 is_option=1 但 option_type/strike_price/expiry_date 为 NULL 的持仓
output: 从 symbol 解析并更新这些字段
pos: 数据修复脚本 - 一次性修复历史数据

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.base import init_database, get_session, create_all_tables
from src.models.position import Position
from src.utils.option_parser import OptionParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_option_fields(dry_run: bool = False):
    """
    修复期权持仓的缺失字段

    Args:
        dry_run: 如果为 True，只打印要修改的内容，不实际修改
    """
    logger.info("=" * 60)
    logger.info("修复期权持仓字段")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 60)

    # 初始化数据库
    engine = init_database(config.DATABASE_URL, echo=False)
    session = get_session()

    try:
        # 查找需要修复的持仓：is_option=1 但 option_type 为 NULL
        positions = session.query(Position).filter(
            Position.is_option == 1,
            Position.option_type.is_(None)
        ).all()

        logger.info(f"找到 {len(positions)} 条需要修复的期权持仓")

        if len(positions) == 0:
            logger.info("无需修复，所有期权持仓字段完整")
            return

        # 统计
        fixed = 0
        failed = 0

        for pos in positions:
            # 解析期权符号
            parsed = OptionParser.parse(pos.symbol)

            if parsed:
                if dry_run:
                    logger.info(f"[DRY RUN] Position {pos.id}: {pos.symbol}")
                    logger.info(f"  → option_type: {parsed['option_type']}")
                    logger.info(f"  → strike_price: {parsed['strike']}")
                    logger.info(f"  → expiry_date: {parsed['expiry_date'].date()}")
                else:
                    pos.option_type = parsed['option_type']
                    pos.strike_price = parsed['strike']
                    pos.expiry_date = parsed['expiry_date'].date()

                    # 同时确保 underlying_symbol 正确
                    if not pos.underlying_symbol:
                        pos.underlying_symbol = parsed['underlying']

                fixed += 1
            else:
                logger.warning(f"Position {pos.id}: 无法解析期权符号 '{pos.symbol}'")
                failed += 1

        if not dry_run:
            session.commit()
            logger.info("已提交更改")

        # 打印摘要
        logger.info("\n" + "=" * 60)
        logger.info("修复摘要")
        logger.info("=" * 60)
        logger.info(f"总计需修复:  {len(positions)}")
        logger.info(f"成功修复:    {fixed}")
        logger.info(f"解析失败:    {failed}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"修复失败: {e}", exc_info=True)
        session.rollback()
        raise

    finally:
        session.close()


def verify_fix():
    """验证修复结果"""
    logger.info("\n验证修复结果...")

    engine = init_database(config.DATABASE_URL, echo=False)
    session = get_session()

    try:
        # 统计期权持仓
        total_options = session.query(Position).filter(
            Position.is_option == 1
        ).count()

        # 统计仍然缺失字段的持仓
        missing = session.query(Position).filter(
            Position.is_option == 1,
            Position.option_type.is_(None)
        ).count()

        complete = total_options - missing

        logger.info(f"期权持仓总数:     {total_options}")
        if total_options > 0:
            logger.info(f"字段完整:         {complete} ({complete/total_options*100:.1f}%)")
            logger.info(f"仍然缺失:         {missing} ({missing/total_options*100:.1f}%)")
        else:
            logger.info("无期权持仓记录")

        if missing == 0:
            logger.info("✅ 所有期权持仓字段已完整")
        else:
            logger.warning(f"⚠️ 仍有 {missing} 条持仓需要手动处理")

    finally:
        session.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='修复期权持仓缺失字段')
    parser.add_argument('--dry-run', action='store_true', help='只打印要修改的内容')
    parser.add_argument('--verify', action='store_true', help='只验证当前状态')

    args = parser.parse_args()

    if args.verify:
        verify_fix()
    else:
        fix_option_fields(dry_run=args.dry_run)
        if not args.dry_run:
            verify_fix()


if __name__ == '__main__':
    main()
