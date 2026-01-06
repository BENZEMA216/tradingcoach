#!/usr/bin/env python3
"""
Preload Market Data Script

Analyzes the trades database and batch-fetches all required market data
using the three-tier caching system.

Usage:
    python3 scripts/preload_market_data.py [--warmup-only] [--top-n N]
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from src.data_sources import YFinanceClient, CacheManager, BatchFetcher


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/preload_market_data.log')
    ]
)

logger = logging.getLogger(__name__)


def setup_components(cache_dir='cache/market_data'):
    """
    Initialize all components for data fetching

    Returns:
        tuple: (engine, session, client, cache, fetcher)
    """
    logger.info("Setting up components...")

    # Database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Data client (yfinance)
    client = YFinanceClient(
        rate_limit=2000,  # 2000 requests per hour
        rate_window_seconds=3600
    )

    # Check availability
    if not client.is_available():
        logger.error("yfinance is not available. Check your internet connection.")
        sys.exit(1)

    logger.info(f"Data client ready: {client}")

    # Cache manager
    cache = CacheManager(
        db_session=session,
        cache_dir=cache_dir,
        expiry_days=1,
        l1_max_size=100
    )

    logger.info(f"Cache manager ready: {cache}")

    # Batch fetcher
    fetcher = BatchFetcher(
        client=client,
        cache_manager=cache,
        batch_size=50,
        request_delay=0.2,  # 5 requests per second
        extra_days=200  # 200 extra days for technical indicators
    )

    logger.info(f"Batch fetcher ready: {fetcher}")

    return engine, session, client, cache, fetcher


def display_cache_stats(cache):
    """Display cache statistics"""
    stats = cache.get_stats()

    print("\n" + "=" * 60)
    print("CACHE STATISTICS")
    print("=" * 60)
    print(f"L1 (Memory):    {stats['l1_entries']}/{stats['l1_max_size']} entries")
    print(f"L2 (Database):  {stats['l2_records']} records, {stats['l2_symbols']} symbols")
    print(f"L3 (Disk):      {stats['l3_files']} files, {stats['l3_size_mb']:.2f} MB")
    print("=" * 60 + "\n")


def run_full_preload(session, fetcher, cache):
    """
    Run full preload: analyze all trades and fetch required data

    Args:
        session: Database session
        fetcher: BatchFetcher instance
        cache: CacheManager instance
    """
    print("\n" + "=" * 60)
    print("FULL PRELOAD MODE")
    print("=" * 60)

    start_time = datetime.now()

    # Display cache stats before
    print("\nCache stats before:")
    display_cache_stats(cache)

    # Fetch all required data
    print("\nFetching required market data...")
    stats = fetcher.fetch_required_data(session)

    # Display results
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 60)
    print("PRELOAD RESULTS")
    print("=" * 60)
    print(f"Symbols analyzed:    {stats['symbols_analyzed']}")
    print(f"Symbols fetched:     {stats['symbols_fetched']}")
    print(f"Symbols cached:      {stats['cached_symbols']} (cache hit)")
    print(f"Records fetched:     {stats['records_fetched']}")
    print(f"Duration:            {stats['duration_seconds']:.1f}s")
    print(f"Total time:          {duration:.1f}s")

    if stats['failed_symbols']:
        print(f"\nFailed symbols ({len(stats['failed_symbols'])}):")
        for failed in stats['failed_symbols'][:10]:  # Show first 10
            print(f"  - {failed['symbol']}: {failed['reason']}")
        if len(stats['failed_symbols']) > 10:
            print(f"  ... and {len(stats['failed_symbols']) - 10} more")

    print("=" * 60)

    # Display cache stats after
    print("\nCache stats after:")
    display_cache_stats(cache)


def run_warmup(session, fetcher, cache, top_n=20):
    """
    Run warmup mode: preload only top N most-traded symbols

    Args:
        session: Database session
        fetcher: BatchFetcher instance
        cache: CacheManager instance
        top_n: Number of top symbols to preload
    """
    print("\n" + "=" * 60)
    print(f"WARMUP MODE - Top {top_n} symbols")
    print("=" * 60)

    start_time = datetime.now()

    # Display cache stats before
    print("\nCache stats before:")
    display_cache_stats(cache)

    # Warmup cache
    print(f"\nWarming up cache with top {top_n} symbols...")
    fetcher.warmup_cache(session, top_n=top_n)

    # Display results
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 60)
    print("WARMUP RESULTS")
    print("=" * 60)
    print(f"Duration: {duration:.1f}s")
    print("=" * 60)

    # Display cache stats after
    print("\nCache stats after:")
    display_cache_stats(cache)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Preload market data for trading coach system'
    )
    parser.add_argument(
        '--warmup-only',
        action='store_true',
        help='Only warmup cache with top N symbols (faster)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=20,
        help='Number of top symbols to warmup (default: 20)'
    )
    parser.add_argument(
        '--cache-dir',
        type=str,
        default='cache/market_data',
        help='Cache directory path (default: cache/market_data)'
    )

    args = parser.parse_args()

    try:
        # Setup components
        engine, session, client, cache, fetcher = setup_components(args.cache_dir)

        # Run preload
        if args.warmup_only:
            run_warmup(session, fetcher, cache, top_n=args.top_n)
        else:
            run_full_preload(session, fetcher, cache)

        # Cleanup
        session.close()
        engine.dispose()

        print("\nPreload completed successfully!")

    except KeyboardInterrupt:
        print("\n\nPreload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Preload failed: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
