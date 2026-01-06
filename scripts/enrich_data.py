#!/usr/bin/env python3
"""
数据补全脚本 - 为阶段一功能准备数据

补全内容：
1. 关联 Trades 与 Positions
2. 解析期权的 underlying_symbol, strike_price, expiry_date
3. 计算 MAE/MFE 风险指标
4. 更新离场后走势数据

Usage:
    python scripts/enrich_data.py --all           # 执行所有补全
    python scripts/enrich_data.py --link-trades   # 仅关联 trades
    python scripts/enrich_data.py --parse-options # 仅解析期权信息
    python scripts/enrich_data.py --calc-mae-mfe  # 仅计算 MAE/MFE
    python scripts/enrich_data.py --dry-run       # 演练模式
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL
from src.models.trade import Trade, TradeDirection
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.utils.symbol_parser import parse_symbol, SymbolType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataEnricher:
    """数据补全器"""

    def __init__(self, session: Session, dry_run: bool = False):
        self.session = session
        self.dry_run = dry_run
        self.stats = {
            'trades_linked': 0,
            'options_parsed': 0,
            'mae_mfe_calculated': 0,
            'errors': []
        }

    def run_all(self):
        """执行所有数据补全"""
        logger.info("=" * 60)
        logger.info("Starting Data Enrichment Process")
        logger.info("=" * 60)

        self.link_trades_to_positions()
        self.parse_option_symbols()
        self.calculate_mae_mfe()

        if not self.dry_run:
            self.session.commit()
            logger.info("All changes committed to database")
        else:
            self.session.rollback()
            logger.info("DRY RUN - No changes saved")

        self._print_summary()

    def link_trades_to_positions(self):
        """关联 Trades 与 Positions"""
        logger.info("\n--- Linking Trades to Positions ---")

        # 获取所有已平仓的 positions
        positions = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        logger.info(f"Found {len(positions)} closed positions to process")

        linked_count = 0
        for pos in positions:
            # 查找该 position 的开仓交易
            # 条件：同 symbol, 同方向(buy for long), 时间匹配
            if pos.direction == 'long':
                open_direction = TradeDirection.BUY
                close_direction = TradeDirection.SELL
            else:
                open_direction = TradeDirection.SELL_SHORT
                close_direction = TradeDirection.BUY_TO_COVER

            # 查找开仓交易（时间在 open_time 前后 1 秒内）
            open_trades = self.session.query(Trade).filter(
                and_(
                    Trade.symbol == pos.symbol,
                    Trade.direction == open_direction,
                    Trade.filled_time >= pos.open_time - timedelta(seconds=1),
                    Trade.filled_time <= pos.open_time + timedelta(seconds=1)
                )
            ).all()

            # 查找平仓交易
            close_trades = self.session.query(Trade).filter(
                and_(
                    Trade.symbol == pos.symbol,
                    Trade.direction == close_direction,
                    Trade.filled_time >= pos.close_time - timedelta(seconds=1),
                    Trade.filled_time <= pos.close_time + timedelta(seconds=1)
                )
            ).all()

            # 更新关联
            for trade in open_trades + close_trades:
                if trade.position_id != pos.id:
                    trade.position_id = pos.id
                    linked_count += 1

        self.stats['trades_linked'] = linked_count
        logger.info(f"Linked {linked_count} trades to positions")

    def parse_option_symbols(self):
        """解析期权的 underlying_symbol, strike_price, expiry_date"""
        logger.info("\n--- Parsing Option Symbols ---")

        # 获取所有期权 positions（is_option=1 但 underlying_symbol 为空）
        option_positions = self.session.query(Position).filter(
            and_(
                Position.is_option == 1,
                (Position.underlying_symbol == None) | (Position.underlying_symbol == '')
            )
        ).all()

        logger.info(f"Found {len(option_positions)} options needing parsing")

        parsed_count = 0
        fixed_non_options = 0

        for pos in option_positions:
            symbol_info = parse_symbol(pos.symbol, pos.symbol_name)

            if symbol_info['is_option'] and symbol_info['underlying_symbol']:
                # 这是真正的期权，更新信息
                pos.underlying_symbol = symbol_info['underlying_symbol']
                pos.strike_price = symbol_info.get('strike_price')
                pos.option_type = symbol_info.get('option_type', '').lower() if symbol_info.get('option_type') else None

                if symbol_info.get('expiration_date'):
                    pos.expiry_date = symbol_info['expiration_date']

                parsed_count += 1
                logger.debug(f"Parsed {pos.symbol} -> underlying={pos.underlying_symbol}, "
                           f"strike={pos.strike_price}, type={pos.option_type}")
            else:
                # 这不是期权，修正 is_option 标记
                pos.is_option = 0
                fixed_non_options += 1
                logger.debug(f"Fixed non-option: {pos.symbol} -> is_option=0")

        # 同时更新 trades 表的期权信息
        option_trades = self.session.query(Trade).filter(
            and_(
                Trade.is_option == 1,
                (Trade.underlying_symbol == None) | (Trade.underlying_symbol == '')
            )
        ).all()

        for trade in option_trades:
            symbol_info = parse_symbol(trade.symbol, trade.symbol_name)

            if symbol_info['is_option'] and symbol_info['underlying_symbol']:
                trade.underlying_symbol = symbol_info['underlying_symbol']
                trade.strike_price = symbol_info.get('strike_price')
                trade.option_type = symbol_info.get('option_type')

                if symbol_info.get('expiration_date'):
                    trade.expiration_date = symbol_info['expiration_date']
            else:
                # 修正非期权
                trade.is_option = 0

        self.stats['options_parsed'] = parsed_count
        self.stats['non_options_fixed'] = fixed_non_options
        logger.info(f"Parsed {parsed_count} option positions, fixed {fixed_non_options} non-options")

    def calculate_mae_mfe(self):
        """计算 MAE/MFE 风险指标"""
        logger.info("\n--- Calculating MAE/MFE ---")

        # 获取已平仓但没有 MAE/MFE 的 positions
        positions = self.session.query(Position).filter(
            and_(
                Position.status == PositionStatus.CLOSED,
                Position.mae == None
            )
        ).all()

        logger.info(f"Found {len(positions)} positions needing MAE/MFE calculation")

        calculated_count = 0
        for pos in positions:
            # 确定要查询的 symbol（期权用 underlying，股票用自己）
            query_symbol = pos.underlying_symbol if pos.is_option and pos.underlying_symbol else pos.symbol

            # 获取持仓期间的市场数据
            if not pos.open_time or not pos.close_time:
                continue

            market_data = self.session.query(MarketData).filter(
                and_(
                    MarketData.symbol == query_symbol,
                    MarketData.date >= pos.open_date,
                    MarketData.date <= pos.close_date
                )
            ).order_by(MarketData.date).all()

            if not market_data or len(market_data) < 1:
                logger.debug(f"No market data for {query_symbol} from {pos.open_date} to {pos.close_date}")
                continue

            # 计算 MAE 和 MFE
            mae, mfe, mae_date, mfe_date = self._calc_mae_mfe_from_data(
                pos, market_data
            )

            if mae is not None:
                pos.mae = Decimal(str(mae))
                pos.mae_pct = Decimal(str(mae / float(pos.open_price * pos.quantity) * 100)) if pos.open_price else None

            if mfe is not None:
                pos.mfe = Decimal(str(mfe))
                pos.mfe_pct = Decimal(str(mfe / float(pos.open_price * pos.quantity) * 100)) if pos.open_price else None

            calculated_count += 1

        self.stats['mae_mfe_calculated'] = calculated_count
        logger.info(f"Calculated MAE/MFE for {calculated_count} positions")

    def _calc_mae_mfe_from_data(
        self,
        pos: Position,
        market_data: List[MarketData]
    ) -> Tuple[Optional[float], Optional[float], Optional[datetime], Optional[datetime]]:
        """
        从市场数据计算 MAE/MFE

        MAE (Maximum Adverse Excursion): 持仓期间最大不利偏移（最大浮亏）
        MFE (Maximum Favorable Excursion): 持仓期间最大有利偏移（最大浮盈）

        注意：期权使用标的股票价格计算 MAE/MFE，因为期权价格由标的价格驱动
        """
        if not market_data or not pos.open_price:
            return None, None, None, None

        open_price = float(pos.open_price)
        quantity = int(pos.quantity)
        is_long = pos.direction == 'long'

        # 期权合约乘数：每张期权代表100股标的资产
        multiplier = 100 if pos.is_option else 1

        mae = 0  # 最大亏损（负数）
        mfe = 0  # 最大盈利（正数）
        mae_date = None
        mfe_date = None

        for md in market_data:
            if md.low is None or md.high is None:
                continue

            low = float(md.low)
            high = float(md.high)

            if is_long:
                # 做多：最低价产生最大亏损，最高价产生最大盈利
                adverse = (low - open_price) * quantity * multiplier
                favorable = (high - open_price) * quantity * multiplier
            else:
                # 做空：最高价产生最大亏损，最低价产生最大盈利
                adverse = (open_price - high) * quantity * multiplier
                favorable = (open_price - low) * quantity * multiplier

            if adverse < mae:
                mae = adverse
                mae_date = md.date

            if favorable > mfe:
                mfe = favorable
                mfe_date = md.date

        return mae, mfe, mae_date, mfe_date

    def _print_summary(self):
        """打印执行总结"""
        logger.info("\n" + "=" * 60)
        logger.info("DATA ENRICHMENT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Trades Linked:        {self.stats['trades_linked']}")
        logger.info(f"Options Parsed:       {self.stats['options_parsed']}")
        logger.info(f"Non-Options Fixed:    {self.stats.get('non_options_fixed', 0)}")
        logger.info(f"MAE/MFE Calculated:   {self.stats['mae_mfe_calculated']}")

        if self.stats['errors']:
            logger.info(f"\nErrors ({len(self.stats['errors'])}):")
            for err in self.stats['errors'][:10]:
                logger.info(f"  - {err}")

        logger.info("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Enrich trading data for Phase 1 features')
    parser.add_argument('--all', action='store_true', help='Run all enrichment tasks')
    parser.add_argument('--link-trades', action='store_true', help='Link trades to positions')
    parser.add_argument('--parse-options', action='store_true', help='Parse option symbols')
    parser.add_argument('--calc-mae-mfe', action='store_true', help='Calculate MAE/MFE')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')

    args = parser.parse_args()

    # Default to --all if no specific task is specified
    if not (args.link_trades or args.parse_options or args.calc_mae_mfe):
        args.all = True

    # Create database session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    enricher = DataEnricher(session, dry_run=args.dry_run)

    try:
        if args.all:
            enricher.run_all()
        else:
            if args.link_trades:
                enricher.link_trades_to_positions()
            if args.parse_options:
                enricher.parse_option_symbols()
            if args.calc_mae_mfe:
                enricher.calculate_mae_mfe()

            if not args.dry_run:
                session.commit()
                logger.info("Changes committed to database")
            else:
                session.rollback()
                logger.info("DRY RUN - No changes saved")

            enricher._print_summary()

    except Exception as e:
        logger.error(f"Error during data enrichment: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
