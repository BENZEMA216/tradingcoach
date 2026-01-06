#!/usr/bin/env python3
"""
市场环境数据填充脚本

为持仓填充 MarketEnvironment 数据，并建立关联

Usage:
    python3 scripts/fill_market_environment.py [--mode backfill|link|check|all]

Examples:
    # 完整流程：回填数据 + 关联持仓 + 检查质量
    python3 scripts/fill_market_environment.py --mode all

    # 只回填市场环境数据
    python3 scripts/fill_market_environment.py --mode backfill

    # 只关联持仓到市场环境
    python3 scripts/fill_market_environment.py --mode link

    # 只检查数据质量
    python3 scripts/fill_market_environment.py --mode check
"""

import sys
import os
import argparse
import logging
from datetime import datetime, date

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from src.data_sources.market_env_fetcher import MarketEnvironmentFetcher
from src.validators.data_quality import DataQualityChecker
from src.models.position import Position, PositionStatus

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/fill_market_environment.log')
    ]
)

logger = logging.getLogger(__name__)


def backfill_market_environment(session):
    """
    回填市场环境数据

    根据所有持仓的开仓和平仓日期，获取所需的市场环境数据
    """
    logger.info("=" * 60)
    logger.info("Step 1: Backfilling market environment data")
    logger.info("=" * 60)

    fetcher = MarketEnvironmentFetcher(session)

    # 获取所有已平仓的持仓
    positions = session.query(Position).filter(
        Position.status == PositionStatus.CLOSED
    ).all()

    logger.info(f"Found {len(positions)} closed positions")

    # 回填数据
    stats = fetcher.backfill_for_positions(positions)

    logger.info(f"Backfill completed:")
    logger.info(f"  - Success: {stats['success']}")
    logger.info(f"  - Failed: {stats['failed']}")
    logger.info(f"  - Skipped (already exists): {stats['skipped']}")

    return stats


def link_positions_to_environment(session):
    """
    将持仓与市场环境关联
    """
    logger.info("=" * 60)
    logger.info("Step 2: Linking positions to market environment")
    logger.info("=" * 60)

    fetcher = MarketEnvironmentFetcher(session)

    # 获取所有持仓
    positions = session.query(Position).all()

    logger.info(f"Found {len(positions)} positions to link")

    # 关联
    linked_count = fetcher.link_positions_to_environment(positions)

    logger.info(f"Linked {linked_count} positions to market environment")

    return linked_count


def check_data_quality(session):
    """
    检查数据质量
    """
    logger.info("=" * 60)
    logger.info("Step 3: Checking data quality")
    logger.info("=" * 60)

    checker = DataQualityChecker(session)

    # 生成完整报告
    report = checker.generate_full_report()

    if 'error' in report:
        logger.error(f"Error generating report: {report['error']}")
        return report

    # 输出报告
    logger.info(f"\nData Quality Report")
    logger.info(f"Generated at: {report['generated_at']}")
    logger.info(f"Date range: {report['date_range']['start']} to {report['date_range']['end']}")

    logger.info(f"\n--- Position Quality ---")
    pos_quality = report['position_quality']
    logger.info(f"Total positions checked: {pos_quality['checked_records']}")
    logger.info(f"Total issues: {pos_quality['total_issues']}")
    logger.info(f"Critical issues: {pos_quality['critical_count']}")
    logger.info(f"High issues: {pos_quality['high_count']}")
    logger.info(f"Is healthy: {pos_quality['is_healthy']}")

    if pos_quality['summary']:
        logger.info(f"\nIssue breakdown:")
        for issue_type, count in pos_quality['summary'].items():
            logger.info(f"  - {issue_type}: {count}")

    logger.info(f"\n--- Market Environment Coverage ---")
    env_coverage = report['market_environment_coverage']
    logger.info(f"Expected trading days: {env_coverage['expected_days']}")
    logger.info(f"Actual records: {env_coverage['actual_records']}")
    logger.info(f"Coverage: {env_coverage['coverage_pct']}%")
    logger.info(f"VIX coverage: {env_coverage['vix_coverage_pct']}%")
    logger.info(f"SPY coverage: {env_coverage['spy_coverage_pct']}%")

    logger.info(f"\n--- Overall Health ---")
    logger.info(f"Overall healthy: {report['overall_health']}")

    return report


def display_summary(session):
    """
    显示当前数据状态摘要
    """
    from src.models.market_environment import MarketEnvironment

    logger.info("\n" + "=" * 60)
    logger.info("Current Data Summary")
    logger.info("=" * 60)

    # 持仓统计
    total_positions = session.query(Position).count()
    closed_positions = session.query(Position).filter(
        Position.status == PositionStatus.CLOSED
    ).count()

    linked_entry = session.query(Position).filter(
        Position.entry_market_env_id.isnot(None)
    ).count()

    linked_exit = session.query(Position).filter(
        Position.exit_market_env_id.isnot(None)
    ).count()

    logger.info(f"\nPositions:")
    logger.info(f"  - Total: {total_positions}")
    logger.info(f"  - Closed: {closed_positions}")
    logger.info(f"  - With entry market env: {linked_entry} ({linked_entry/total_positions*100:.1f}%)")
    logger.info(f"  - With exit market env: {linked_exit} ({linked_exit/total_positions*100:.1f}%)")

    # 市场环境统计
    total_env = session.query(MarketEnvironment).count()
    with_vix = session.query(MarketEnvironment).filter(
        MarketEnvironment.vix.isnot(None)
    ).count()
    with_spy = session.query(MarketEnvironment).filter(
        MarketEnvironment.spy_close.isnot(None)
    ).count()

    logger.info(f"\nMarket Environment:")
    logger.info(f"  - Total records: {total_env}")
    logger.info(f"  - With VIX data: {with_vix}")
    logger.info(f"  - With SPY data: {with_spy}")


def main():
    parser = argparse.ArgumentParser(description='Fill market environment data')
    parser.add_argument(
        '--mode',
        choices=['backfill', 'link', 'check', 'all', 'summary'],
        default='all',
        help='Operation mode: backfill, link, check, all, or summary'
    )

    args = parser.parse_args()

    logger.info(f"Starting market environment fill script (mode: {args.mode})")
    logger.info(f"Database: {DATABASE_URL}")

    # Create database session
    engine = create_engine(DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if args.mode == 'summary':
            display_summary(session)
            return

        if args.mode in ['backfill', 'all']:
            backfill_market_environment(session)

        if args.mode in ['link', 'all']:
            link_positions_to_environment(session)

        if args.mode in ['check', 'all']:
            check_data_quality(session)

        # 最后显示摘要
        display_summary(session)

        logger.info("\n" + "=" * 60)
        logger.info("Script completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Script failed with error: {e}", exc_info=True)
        session.rollback()
        sys.exit(1)

    finally:
        session.close()


if __name__ == '__main__':
    main()
