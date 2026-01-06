#!/usr/bin/env python3
"""
计算离场后走势

获取每个已平仓持仓在平仓后5/10/20个交易日的涨跌幅
"""

import sys
import logging
from pathlib import Path
from datetime import timedelta

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.base import init_database, get_session
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.utils.option_parser import OptionParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_future_price(session, symbol: str, close_date, days: int):
    """
    获取平仓后N个交易日的收盘价

    由于我们只有交易日的数据，所以需要查找close_date之后的第N条记录
    """
    from sqlalchemy import func

    # 查找close_date之后的所有交易日数据，按日期排序
    future_data = session.query(MarketData).filter(
        MarketData.symbol == symbol,
        MarketData.date > close_date
    ).order_by(MarketData.date).limit(days + 5).all()  # 多取一些以防节假日

    if len(future_data) >= days:
        return future_data[days - 1]  # 返回第N个交易日的数据

    return None


def calculate_post_exit_returns(session, position: Position) -> dict:
    """
    计算单个持仓的离场后走势

    Returns:
        dict: {'5d': pct, '10d': pct, '20d': pct}
    """
    if not position.close_date or not position.close_price:
        return {}

    # 获取标的symbol（期权需要提取underlying）
    symbol = position.symbol
    if OptionParser.is_option_symbol(symbol):
        symbol = OptionParser.extract_underlying(symbol)

    close_price = float(position.close_price)
    close_date = position.close_date

    results = {}

    for days, key in [(5, '5d'), (10, '10d'), (20, '20d')]:
        future_data = get_future_price(session, symbol, close_date, days)
        if future_data and future_data.close:
            future_price = float(future_data.close)
            pct_change = ((future_price - close_price) / close_price) * 100
            results[key] = round(pct_change, 4)

    return results


def main():
    """主函数"""
    # 初始化数据库
    db_path = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'
    init_database(f'sqlite:///{db_path}', echo=False)

    logger.info("Database connection established")

    session = get_session()
    try:
        # 获取所有已平仓持仓
        positions = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        total = len(positions)
        updated = 0
        skipped = 0
        errors = 0

        logger.info(f"Processing {total} closed positions...")

        for i, position in enumerate(positions):
            try:
                returns = calculate_post_exit_returns(session, position)

                if returns:
                    if '5d' in returns:
                        position.post_exit_5d_pct = returns['5d']
                    if '10d' in returns:
                        position.post_exit_10d_pct = returns['10d']
                    if '20d' in returns:
                        position.post_exit_20d_pct = returns['20d']
                    updated += 1
                else:
                    skipped += 1

                # 每100条打印进度
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: {i + 1}/{total}")

            except Exception as e:
                errors += 1
                logger.error(f"Failed to calculate for position {position.id}: {e}")

        session.commit()

        # 打印统计
        print("\n" + "=" * 50)
        print("离场后走势计算完成")
        print("=" * 50)
        print(f"总持仓数: {total}")
        print(f"成功更新: {updated}")
        print(f"跳过(无数据): {skipped}")
        print(f"错误: {errors}")
        print("=" * 50)

        # 显示一些样本数据
        sample = session.query(Position).filter(
            Position.post_exit_5d_pct.isnot(None)
        ).limit(5).all()

        if sample:
            print("\n样本数据:")
            print("-" * 50)
            for pos in sample:
                print(f"  {pos.symbol}: 5D={pos.post_exit_5d_pct}%, "
                      f"10D={pos.post_exit_10d_pct}%, "
                      f"20D={pos.post_exit_20d_pct}%")

    finally:
        session.close()


if __name__ == '__main__':
    main()
