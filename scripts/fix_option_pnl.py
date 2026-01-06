#!/usr/bin/env python3
"""
修复期权盈亏计算 - 添加 ×100 合约乘数

期权合约每张代表100股标的资产，盈亏计算需要乘以100

Usage:
    python scripts/fix_option_pnl.py           # 执行修复
    python scripts/fix_option_pnl.py --dry-run # 演练模式
"""

import sys
import os
import argparse
import logging
import re
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from src.models.position import Position, PositionStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 期权合约乘数
OPTION_MULTIPLIER = 100

# 期权代码正则：标的代码 + 年月日 + C/P + 行权价
OPTION_SYMBOL_PATTERN = re.compile(r'^([A-Z]+)(\d{6})(C|P)(\d+)$')


def is_valid_option_symbol(symbol: str) -> bool:
    """验证是否是有效的期权代码格式"""
    return OPTION_SYMBOL_PATTERN.match(symbol) is not None


def fix_option_pnl(dry_run: bool = False):
    """修复所有期权持仓的盈亏计算"""

    # Create database session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # 查询所有期权持仓
        option_positions = session.query(Position).filter(
            Position.is_option == 1,
            Position.close_price != None  # 只处理已平仓的
        ).all()

        logger.info(f"Found {len(option_positions)} positions marked as options")

        fixed_count = 0
        total_pnl_diff = 0
        wrong_option_flag_count = 0

        for pos in option_positions:
            if pos.open_price is None or pos.close_price is None:
                continue

            # 验证是否真的是期权代码
            if not is_valid_option_symbol(pos.symbol):
                logger.warning(f"Position {pos.id} ({pos.symbol}): NOT a valid option symbol, fixing is_option flag")
                if not dry_run:
                    pos.is_option = 0
                wrong_option_flag_count += 1
                continue

            open_price = float(pos.open_price)
            close_price = float(pos.close_price)
            quantity = int(pos.quantity)

            # 计算正确的盈亏（带乘数）
            if pos.direction == 'long':
                price_diff = close_price - open_price
            else:
                price_diff = open_price - close_price

            new_realized_pnl = round(price_diff * quantity * OPTION_MULTIPLIER, 2)

            # 计算百分比
            new_realized_pnl_pct = round((price_diff / open_price) * 100, 2) if open_price > 0 else 0

            # 计算净盈亏
            total_fees = float(pos.total_fees) if pos.total_fees else 0
            new_net_pnl = round(new_realized_pnl - total_fees, 2)

            # 计算净盈亏百分比
            cost_basis = open_price * quantity * OPTION_MULTIPLIER
            new_net_pnl_pct = round((new_net_pnl / cost_basis) * 100, 2) if cost_basis > 0 else 0

            # 记录差异
            old_net_pnl = float(pos.net_pnl) if pos.net_pnl else 0
            pnl_diff = new_net_pnl - old_net_pnl
            total_pnl_diff += pnl_diff

            if abs(pnl_diff) > 0.01:  # 有明显差异才更新
                logger.info(
                    f"Position {pos.id} ({pos.symbol}): "
                    f"Old PnL=${old_net_pnl:.2f} -> New PnL=${new_net_pnl:.2f} "
                    f"(Diff: ${pnl_diff:.2f})"
                )

                if not dry_run:
                    pos.realized_pnl = Decimal(str(new_realized_pnl))
                    pos.realized_pnl_pct = Decimal(str(new_realized_pnl_pct))
                    pos.net_pnl = Decimal(str(new_net_pnl))
                    pos.net_pnl_pct = Decimal(str(new_net_pnl_pct))

                fixed_count += 1

        if not dry_run:
            session.commit()
            logger.info("Changes committed to database")
        else:
            session.rollback()
            logger.info("DRY RUN - No changes saved")

        # 打印总结
        logger.info("=" * 60)
        logger.info("FIX OPTION PNL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total positions checked:   {len(option_positions)}")
        logger.info(f"Wrong option flags fixed:  {wrong_option_flag_count}")
        logger.info(f"Option PnL recalculated:   {fixed_count}")
        logger.info(f"Total PnL adjustment:      ${total_pnl_diff:.2f}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error fixing option PnL: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description='Fix option PnL calculation (add x100 multiplier)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')

    args = parser.parse_args()
    fix_option_pnl(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
