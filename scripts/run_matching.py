#!/usr/bin/env python3
"""
运行FIFO交易配对

将数据库中的交易记录配对成持仓记录
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.base import init_database, get_session
from src.matchers import match_trades_from_database

# 数据库路径
DB_PATH = project_root / 'data' / 'tradingcoach.db'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / 'logs' / 'matching.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='运行FIFO交易配对，生成持仓记录',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 演练模式（不保存）
  python scripts/run_matching.py --dry-run

  # 正式运行
  python scripts/run_matching.py

  # 启用详细日志
  python scripts/run_matching.py --verbose
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='演练模式：执行配对但不保存到数据库'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出（DEBUG级别日志）'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # 显示配置
    logger.info("=" * 60)
    logger.info("FIFO Matching - 交易配对工具")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN (演练)' if args.dry_run else 'PRODUCTION (正式)'}")
    logger.info(f"Log Level: {logging.getLevelName(logging.getLogger().level)}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.warning("⚠️  DRY RUN MODE - No changes will be saved to database")

    try:
        # 初始化数据库连接
        if not DB_PATH.exists():
            logger.error(f"❌ Database not found: {DB_PATH}")
            logger.error("Please run scripts/init_db.py first to create the database")
            return 1

        logger.debug(f"Initializing database: {DB_PATH}")
        init_database(f"sqlite:///{DB_PATH}", echo=args.verbose)

        # 获取数据库会话
        session = get_session()

        # 执行配对
        logger.info("\nStarting matching process...\n")
        result = match_trades_from_database(session, dry_run=args.dry_run)

        # 显示结果
        print("\n" + "=" * 60)
        print("MATCHING COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Total Trades Processed:  {result['total_trades']}")
        print(f"Symbols Processed:       {result['symbols_processed']}")
        print(f"Positions Created:       {result['positions_created']}")
        print(f"  - Closed Positions:    {result['closed_positions']}")
        print(f"  - Open Positions:      {result['open_positions']}")

        if result['warnings']:
            print(f"\n⚠️  Warnings ({len(result['warnings'])}):")
            for warning in result['warnings']:
                print(f"  - {warning}")

        print("=" * 60)

        if args.dry_run:
            print("\n✓ DRY RUN completed - No changes saved")
        else:
            print("\n✓ All changes committed to database")

        return 0

    except KeyboardInterrupt:
        logger.warning("\n\nProcess interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"\n❌ Error during matching: {e}", exc_info=True)
        return 1

    finally:
        # 清理
        if 'session' in locals():
            session.close()


if __name__ == '__main__':
    sys.exit(main())
