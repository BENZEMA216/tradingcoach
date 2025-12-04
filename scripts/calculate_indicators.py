#!/usr/bin/env python3
"""
Calculate Indicators Script

计算并更新market_data表中的技术指标

Usage:
    python3 scripts/calculate_indicators.py [--symbols AAPL,MSFT] [--all]
"""

import sys
import os
import argparse
import logging
import pandas as pd
from datetime import datetime, date, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from src.indicators import IndicatorCalculator
from src.data_sources import CacheManager
from src.models.trade import Trade


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/calculate_indicators.log')
    ]
)

logger = logging.getLogger(__name__)


def get_unique_symbols(session) -> list:
    """
    获取数据库中所有唯一的交易symbol

    Args:
        session: Database session

    Returns:
        list: Unique symbols
    """
    from sqlalchemy import func

    symbols = session.query(Trade.symbol).distinct().all()
    return [s[0] for s in symbols]


def calculate_indicators_for_symbols(
    session,
    cache_manager,
    calculator,
    symbols: list
) -> dict:
    """
    为指定symbols计算技术指标

    Args:
        session: Database session
        cache_manager: CacheManager instance
        calculator: IndicatorCalculator instance
        symbols: List of symbols to process

    Returns:
        dict: Statistics
    """
    stats = {
        'total_symbols': len(symbols),
        'success_count': 0,
        'failed_symbols': [],
        'total_records_updated': 0,
        'skipped_symbols': []
    }

    logger.info(f"Starting indicator calculation for {len(symbols)} symbols...")

    for i, symbol in enumerate(symbols, 1):
        try:
            logger.info(f"[{i}/{len(symbols)}] Processing {symbol}...")

            # 从缓存获取所有OHLCV数据（不限制日期范围）
            # 这样可以为所有历史数据计算技术指标
            df = cache_manager.get_all_data(symbol)

            if df is None or df.empty:
                logger.warning(f"  No data found for {symbol}, skipping")
                stats['skipped_symbols'].append(symbol)
                continue

            logger.info(f"  Found {len(df)} records for {symbol} (full history)")

            # 计算指标
            df_with_indicators = calculator.calculate_all_indicators(df)

            # 更新数据库
            updated_count = calculator.update_market_data_indicators(
                session,
                symbol,
                df_with_indicators
            )

            logger.info(f"  Updated {updated_count} records for {symbol}")

            stats['success_count'] += 1
            stats['total_records_updated'] += updated_count

        except Exception as e:
            logger.error(f"  Failed to process {symbol}: {e}", exc_info=True)
            stats['failed_symbols'].append({
                'symbol': symbol,
                'error': str(e)
            })

    return stats


def display_stats(stats: dict):
    """Display calculation statistics"""
    print("\n" + "=" * 60)
    print("INDICATOR CALCULATION RESULTS")
    print("=" * 60)
    print(f"Total symbols:         {stats['total_symbols']}")
    print(f"Successfully processed: {stats['success_count']}")
    print(f"Skipped (no data):     {len(stats['skipped_symbols'])}")
    print(f"Failed:                {len(stats['failed_symbols'])}")
    print(f"Total records updated:  {stats['total_records_updated']}")

    if stats['skipped_symbols']:
        print(f"\nSkipped symbols ({len(stats['skipped_symbols'])}):")
        for symbol in stats['skipped_symbols'][:10]:
            print(f"  - {symbol}")
        if len(stats['skipped_symbols']) > 10:
            print(f"  ... and {len(stats['skipped_symbols']) - 10} more")

    if stats['failed_symbols']:
        print(f"\nFailed symbols ({len(stats['failed_symbols'])}):")
        for failed in stats['failed_symbols'][:5]:
            print(f"  - {failed['symbol']}: {failed['error']}")
        if len(stats['failed_symbols']) > 5:
            print(f"  ... and {len(stats['failed_symbols']) - 5} more")

    print("=" * 60 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Calculate technical indicators for market data'
    )
    parser.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated list of symbols to process (e.g., AAPL,MSFT,TSLA)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all symbols in database'
    )
    parser.add_argument(
        '--cache-dir',
        type=str,
        default='cache/market_data',
        help='Cache directory path (default: cache/market_data)'
    )

    args = parser.parse_args()

    try:
        # Setup database
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        logger.info("Database connection established")

        # Setup cache manager
        cache_manager = CacheManager(
            db_session=session,
            cache_dir=args.cache_dir
        )

        logger.info(f"CacheManager initialized: {cache_manager}")

        # Setup indicator calculator
        calculator = IndicatorCalculator()

        logger.info(f"IndicatorCalculator ready: {calculator}")

        # Determine symbols to process
        if args.symbols:
            symbols = [s.strip() for s in args.symbols.split(',')]
            logger.info(f"Processing specified symbols: {symbols}")
        elif args.all:
            symbols = get_unique_symbols(session)
            logger.info(f"Processing all symbols from database: {len(symbols)} symbols")
        else:
            print("Error: Please specify either --symbols or --all")
            parser.print_help()
            sys.exit(1)

        # Calculate indicators
        start_time = datetime.now()

        stats = calculate_indicators_for_symbols(
            session,
            cache_manager,
            calculator,
            symbols
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        stats['duration_seconds'] = duration

        # Display results
        display_stats(stats)

        print(f"Duration: {duration:.1f}s")
        print("\nIndicator calculation completed successfully!")

        # Cleanup
        session.close()
        engine.dispose()

    except KeyboardInterrupt:
        print("\n\nCalculation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Calculation failed: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
