#!/usr/bin/env python3
"""
Enrich Position Indicators Script

为每个持仓填充入场/出场时的技术指标快照

Usage:
    python3 scripts/enrich_position_indicators.py [--all] [--force]
"""

import sys
import os
import argparse
import logging
import json
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/enrich_position_indicators.log')
    ]
)

logger = logging.getLogger(__name__)


def get_indicator_snapshot(session, symbol: str, target_date) -> dict:
    """
    获取指定日期的技术指标快照

    Args:
        session: Database session
        symbol: 股票代码
        target_date: 目标日期

    Returns:
        dict: 指标快照
    """
    # 查找最接近目标日期的市场数据（允许前后3天的偏差）
    start_search = target_date - timedelta(days=3)
    end_search = target_date + timedelta(days=3)

    market_data = session.query(MarketData).filter(
        and_(
            MarketData.symbol == symbol,
            MarketData.date >= start_search,
            MarketData.date <= end_search
        )
    ).order_by(
        # 按日期与目标日期的距离排序
        MarketData.date
    ).all()

    if not market_data:
        return None

    # 找到最接近目标日期的记录
    closest = min(market_data, key=lambda x: abs((x.date - target_date).days))

    # 构建指标快照
    snapshot = {
        'date': closest.date.isoformat(),
        'close': float(closest.close) if closest.close else None,
        'volume': closest.volume,
    }

    # 添加技术指标
    indicator_fields = [
        ('rsi_14', 'rsi_14'),
        ('macd', 'macd'),
        ('macd_signal', 'macd_signal'),
        ('macd_hist', 'macd_hist'),
        ('adx', 'adx'),
        ('plus_di', 'plus_di'),
        ('minus_di', 'minus_di'),
        ('bb_upper', 'bb_upper'),
        ('bb_middle', 'bb_middle'),
        ('bb_lower', 'bb_lower'),
        ('bb_width', 'bb_width'),
        ('atr_14', 'atr_14'),
        ('ma_5', 'ma_5'),
        ('ma_10', 'ma_10'),
        ('ma_20', 'ma_20'),
        ('ma_50', 'ma_50'),
        ('ma_200', 'ma_200'),
        ('stoch_k', 'stoch_k'),
        ('stoch_d', 'stoch_d'),
        ('volume_sma_20', 'volume_sma_20'),
    ]

    for db_field, snapshot_field in indicator_fields:
        value = getattr(closest, db_field, None)
        if value is not None:
            snapshot[snapshot_field] = float(value)

    # 计算额外指标
    # BB Position (价格在布林带中的位置)
    if closest.bb_upper and closest.bb_lower and closest.close:
        bb_range = float(closest.bb_upper) - float(closest.bb_lower)
        if bb_range > 0:
            bb_position = (float(closest.close) - float(closest.bb_lower)) / bb_range
            snapshot['bb_position'] = round(bb_position, 4)

    # Volume Ratio (当日成交量/20日均量)
    if closest.volume and closest.volume_sma_20:
        volume_ratio = closest.volume / float(closest.volume_sma_20)
        snapshot['volume_ratio'] = round(volume_ratio, 2)

    # MA趋势 (价格相对MA20的位置)
    if closest.ma_20 and closest.close:
        ma20_position = (float(closest.close) - float(closest.ma_20)) / float(closest.ma_20) * 100
        snapshot['ma20_deviation_pct'] = round(ma20_position, 2)

    return snapshot


def enrich_positions(session, force: bool = False) -> dict:
    """
    为所有持仓填充技术指标快照

    Args:
        session: Database session
        force: 是否强制覆盖已有数据

    Returns:
        dict: 统计信息
    """
    stats = {
        'total': 0,
        'enriched': 0,
        'skipped': 0,
        'no_data': 0,
        'errors': []
    }

    # 查询已平仓的持仓
    query = session.query(Position).filter(
        Position.status == PositionStatus.CLOSED
    )

    if not force:
        # 只处理没有指标数据的持仓
        query = query.filter(
            (Position.entry_indicators == None) |
            (Position.exit_indicators == None)
        )

    positions = query.all()
    stats['total'] = len(positions)

    logger.info(f"Processing {len(positions)} positions...")

    for i, pos in enumerate(positions, 1):
        try:
            # 对于期权，使用标的资产的市场数据
            query_symbol = pos.underlying_symbol if pos.is_option and pos.underlying_symbol else pos.symbol

            # 获取入场指标
            entry_snapshot = None
            if pos.open_date:
                entry_snapshot = get_indicator_snapshot(
                    session,
                    query_symbol,
                    pos.open_date
                )

            # 获取出场指标
            exit_snapshot = None
            if pos.close_date:
                exit_snapshot = get_indicator_snapshot(
                    session,
                    query_symbol,
                    pos.close_date
                )

            if entry_snapshot is None and exit_snapshot is None:
                stats['no_data'] += 1
                if i % 100 == 0:
                    logger.info(f"[{i}/{len(positions)}] No market data for {pos.symbol}")
                continue

            # 更新持仓记录
            if entry_snapshot:
                pos.entry_indicators = entry_snapshot
            if exit_snapshot:
                pos.exit_indicators = exit_snapshot

            stats['enriched'] += 1

            if i % 100 == 0:
                logger.info(f"[{i}/{len(positions)}] Enriched {pos.symbol} ({pos.open_date} - {pos.close_date})")
                session.commit()

        except Exception as e:
            stats['errors'].append({
                'position_id': pos.id,
                'symbol': pos.symbol,
                'error': str(e)
            })
            logger.error(f"Error processing position {pos.id}: {e}")

    # 最终提交
    session.commit()

    return stats


def display_stats(stats: dict):
    """Display enrichment statistics"""
    print("\n" + "=" * 60)
    print("POSITION INDICATOR ENRICHMENT RESULTS")
    print("=" * 60)
    print(f"Total positions:    {stats['total']}")
    print(f"Enriched:           {stats['enriched']}")
    print(f"No market data:     {stats['no_data']}")
    print(f"Errors:             {len(stats['errors'])}")

    if stats['errors']:
        print(f"\nErrors ({len(stats['errors'])}):")
        for err in stats['errors'][:5]:
            print(f"  - Position {err['position_id']} ({err['symbol']}): {err['error']}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more")

    print("=" * 60 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Enrich positions with entry/exit technical indicators'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all closed positions'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force overwrite existing indicator data'
    )

    args = parser.parse_args()

    # 确保logs目录存在
    os.makedirs('logs', exist_ok=True)

    try:
        # Setup database
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        logger.info("Database connection established")

        # 统计当前状态
        total_closed = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).count()

        with_entry = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.entry_indicators != None
        ).count()

        with_exit = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.exit_indicators != None
        ).count()

        logger.info(f"Current status: {total_closed} closed positions, "
                   f"{with_entry} with entry indicators, {with_exit} with exit indicators")

        # Enrich positions
        start_time = datetime.now()

        stats = enrich_positions(session, force=args.force)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Display results
        display_stats(stats)

        print(f"Duration: {duration:.1f}s")
        print("\nPosition indicator enrichment completed successfully!")

        # Cleanup
        session.close()
        engine.dispose()

    except KeyboardInterrupt:
        print("\n\nEnrichment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
