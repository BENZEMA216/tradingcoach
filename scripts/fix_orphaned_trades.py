"""
修复孤立交易 - 为无开仓记录的平仓交易创建特殊持仓

input: 数据库中 position_id=NULL 的交易记录
output: 为每条孤立交易创建特殊 Position 并建立关联
pos: 数据修复脚本 - 一次性修复历史数据

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from sqlalchemy import text
from src.models.base import init_database, get_session, get_engine
from src.models.position import Position, PositionStatus
from src.models.trade import TradeDirection
from src.utils.option_parser import OptionParser


@dataclass
class OrphanedTrade:
    """孤立交易的轻量级数据类（避免 ORM 模式不匹配问题）"""
    id: int
    symbol: str
    symbol_name: Optional[str]
    direction: str
    filled_price: float
    filled_quantity: int
    filled_time: datetime
    trade_date: datetime
    market: str
    currency: Optional[str]
    total_fee: Optional[float]
    is_option: bool
    underlying_symbol: Optional[str]
    option_type: Optional[str]
    strike_price: Optional[float]
    expiration_date: Optional[datetime]

    @property
    def direction_enum(self) -> TradeDirection:
        # 数据库存储大写，enum 用小写
        return TradeDirection(self.direction.lower())

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_datetime(val) -> Optional[datetime]:
    """解析日期时间，处理字符串和 datetime 对象"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        # 尝试多种格式
        for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
    return None


def parse_date(val):
    """解析日期，处理字符串和 date 对象"""
    from datetime import date
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except ValueError:
            pass
        try:
            return datetime.strptime(val, '%Y-%m-%d %H:%M:%S').date()
        except ValueError:
            pass
    return None


def query_orphaned_trades() -> List[OrphanedTrade]:
    """使用 raw SQL 查询孤立交易（避免 ORM 模式不匹配）"""
    engine = get_engine()

    sql = """
    SELECT id, symbol, symbol_name, direction, filled_price, filled_quantity,
           filled_time, trade_date, market, currency, total_fee,
           is_option, underlying_symbol, option_type, strike_price, expiration_date
    FROM trades
    WHERE position_id IS NULL
    ORDER BY filled_time
    """

    trades = []
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        for row in result:
            trades.append(OrphanedTrade(
                id=row[0],
                symbol=row[1],
                symbol_name=row[2],
                direction=row[3],
                filled_price=float(row[4]) if row[4] else 0.0,
                filled_quantity=int(row[5]) if row[5] else 0,
                filled_time=parse_datetime(row[6]),
                trade_date=parse_date(row[7]),
                market=row[8],
                currency=row[9],
                total_fee=float(row[10]) if row[10] else None,
                is_option=bool(row[11]) if row[11] else False,
                underlying_symbol=row[12],
                option_type=row[13],
                strike_price=float(row[14]) if row[14] else None,
                expiration_date=parse_date(row[15]),
            ))

    return trades


def fix_orphaned_trades(dry_run: bool = False):
    """
    为孤立交易创建特殊持仓

    孤立交易定义：position_id = NULL 的交易记录
    处理方式：为每条交易创建一个标记为 "无开仓记录" 的特殊持仓

    Args:
        dry_run: 如果为 True，只打印要修改的内容，不实际修改
    """
    logger.info("=" * 60)
    logger.info("修复孤立交易")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 60)

    # 初始化数据库
    engine = init_database(config.DATABASE_URL, echo=False)
    session = get_session()

    try:
        # 查找孤立交易：position_id 为 NULL（使用 raw SQL）
        orphaned_trades = query_orphaned_trades()

        logger.info(f"找到 {len(orphaned_trades)} 条孤立交易")

        if len(orphaned_trades) == 0:
            logger.info("无孤立交易需要处理")
            return

        # 打印详情
        logger.info("\n孤立交易列表:")
        for trade in orphaned_trades:
            logger.info(f"  - {trade.id}: {trade.symbol} {trade.direction} "
                       f"{trade.filled_quantity}股 @ ${trade.filled_price} "
                       f"({trade.filled_time})")

        # 统计
        created = 0
        failed = 0

        for trade in orphaned_trades:
            try:
                position = create_special_position(trade, dry_run)

                if dry_run:
                    logger.info(f"[DRY RUN] 将为 Trade {trade.id} 创建特殊持仓")
                    logger.info(f"  → symbol: {trade.symbol}")
                    logger.info(f"  → direction: {get_position_direction(trade)}")
                    logger.info(f"  → close_price: {trade.filled_price}")
                    logger.info(f"  → notes: 无开仓记录 - 仅平仓交易")
                else:
                    # 保存持仓
                    session.add(position)
                    session.flush()  # 获取 position.id

                    # 更新交易的 position_id（使用 raw SQL）
                    session.execute(
                        text("UPDATE trades SET position_id = :pos_id WHERE id = :trade_id"),
                        {"pos_id": position.id, "trade_id": trade.id}
                    )

                    logger.info(f"创建持仓 {position.id} 关联交易 {trade.id}")

                created += 1

            except Exception as e:
                logger.error(f"处理交易 {trade.id} 失败: {e}", exc_info=True)
                failed += 1

        if not dry_run:
            session.commit()
            logger.info("已提交更改")

        # 打印摘要
        logger.info("\n" + "=" * 60)
        logger.info("修复摘要")
        logger.info("=" * 60)
        logger.info(f"总计孤立交易:  {len(orphaned_trades)}")
        logger.info(f"成功处理:      {created}")
        logger.info(f"处理失败:      {failed}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"修复失败: {e}", exc_info=True)
        session.rollback()
        raise

    finally:
        session.close()


def get_position_direction(trade: OrphanedTrade) -> str:
    """
    根据交易方向推断持仓方向

    - SELL / BUY_TO_COVER 是平仓交易
    - SELL 平掉的是 long 持仓
    - BUY_TO_COVER 平掉的是 short 持仓
    """
    direction = trade.direction_enum
    if direction == TradeDirection.SELL:
        return 'long'  # 卖出平掉的是多头仓位
    elif direction == TradeDirection.BUY_TO_COVER:
        return 'short'  # 买券还券平掉的是空头仓位
    elif direction == TradeDirection.BUY:
        return 'long'  # 买入建立多头（虽然孤立BUY很少见）
    elif direction == TradeDirection.SELL_SHORT:
        return 'short'  # 卖空建立空头
    else:
        return 'long'  # 默认


def create_special_position(trade: OrphanedTrade, dry_run: bool = False) -> Position:
    """
    为孤立交易创建特殊持仓

    特殊持仓特点：
    - status = CLOSED
    - open_price = NULL (无开仓记录)
    - close_price = 交易成交价
    - open_time = NULL
    - close_time = 交易成交时间
    - realized_pnl = NULL (无法计算)
    - notes = "无开仓记录 - 仅平仓交易"

    Args:
        trade: 孤立交易记录
        dry_run: 是否干运行

    Returns:
        Position: 创建的特殊持仓（dry_run时返回未保存的对象）
    """
    direction = get_position_direction(trade)

    # 判断是开仓还是平仓交易
    trade_direction = trade.direction_enum
    is_closing = trade_direction in [TradeDirection.SELL, TradeDirection.BUY_TO_COVER]

    # 解析期权信息
    option_info = None
    if trade.is_option:
        option_info = OptionParser.parse(trade.symbol)

    # 处理 expiry_date
    expiry = None
    if option_info and option_info.get('expiry_date'):
        expiry = option_info['expiry_date'].date() if hasattr(option_info['expiry_date'], 'date') else option_info['expiry_date']
    elif trade.expiration_date:
        expiry = trade.expiration_date.date() if hasattr(trade.expiration_date, 'date') else trade.expiration_date

    # 创建持仓
    position = Position(
        symbol=trade.symbol,
        symbol_name=trade.symbol_name,
        direction=direction,
        status=PositionStatus.CLOSED if is_closing else PositionStatus.OPEN,
        quantity=trade.filled_quantity,
        market=trade.market,
        currency=trade.currency,
        # 期权字段
        is_option=trade.is_option,
        underlying_symbol=trade.underlying_symbol,
        option_type=option_info['option_type'] if option_info else trade.option_type,
        strike_price=option_info['strike'] if option_info else trade.strike_price,
        expiry_date=expiry,
    )

    if is_closing:
        # 平仓交易：填写平仓信息
        # 注意：open_time, open_date, open_price 有 NOT NULL 约束
        # 用平仓信息作为占位符
        position.open_time = trade.filled_time  # 占位符，非实际开仓时间
        position.open_date = trade.trade_date   # 占位符
        position.open_price = trade.filled_price  # 占位符，用平仓价
        position.open_fee = 0.0

        position.close_time = trade.filled_time
        position.close_date = trade.trade_date
        position.close_price = trade.filled_price
        position.close_fee = float(trade.total_fee) if trade.total_fee else 0.0

        # 持仓时间设为 0（同一时间）
        position.holding_period_days = 0
        position.holding_period_hours = 0.0

        # 盈亏为 0（无实际开仓价，使用占位符导致 pnl=0）
        position.realized_pnl = 0.0
        position.realized_pnl_pct = 0.0
        position.net_pnl = -position.close_fee  # 只有费用损失
        position.net_pnl_pct = 0.0
        position.total_fees = position.close_fee

        position.notes = "无开仓记录 - 仅平仓交易 (open_*字段为占位符)"
    else:
        # 开仓交易：填写开仓信息（孤立开仓=未平仓持仓）
        position.open_time = trade.filled_time
        position.open_date = trade.trade_date
        position.open_price = trade.filled_price
        position.open_fee = float(trade.total_fee) if trade.total_fee else 0.0

        position.close_time = None
        position.close_date = None
        position.close_price = None
        position.close_fee = None

        position.holding_period_days = None
        position.holding_period_hours = None
        position.realized_pnl = None
        position.net_pnl = None

        position.notes = "孤立开仓记录"

    return position


def verify_fix():
    """验证修复结果"""
    logger.info("\n验证修复结果...")

    engine = init_database(config.DATABASE_URL, echo=False)

    with engine.connect() as conn:
        # 统计孤立交易
        orphaned = conn.execute(text("SELECT COUNT(*) FROM trades WHERE position_id IS NULL")).scalar()

        # 统计特殊持仓
        special_positions = conn.execute(
            text("SELECT COUNT(*) FROM positions WHERE notes LIKE '%无开仓记录%'")
        ).scalar()

        # 总交易数
        total_trades = conn.execute(text("SELECT COUNT(*) FROM trades")).scalar()

        # 总持仓数
        total_positions = conn.execute(text("SELECT COUNT(*) FROM positions")).scalar()

    logger.info(f"总交易数:       {total_trades}")
    logger.info(f"孤立交易数:     {orphaned}")
    logger.info(f"总持仓数:       {total_positions}")
    logger.info(f"特殊持仓数:     {special_positions}")

    if orphaned == 0:
        logger.info("✅ 所有交易都已关联持仓")
    else:
        logger.warning(f"⚠️ 仍有 {orphaned} 条交易未关联持仓")


def list_orphaned():
    """列出当前的孤立交易"""
    engine = init_database(config.DATABASE_URL, echo=False)

    orphaned_trades = query_orphaned_trades()

    if not orphaned_trades:
        logger.info("没有孤立交易")
        return

    logger.info(f"\n找到 {len(orphaned_trades)} 条孤立交易:\n")

    # 按 symbol 分组
    by_symbol = {}
    for trade in orphaned_trades:
        if trade.symbol not in by_symbol:
            by_symbol[trade.symbol] = []
        by_symbol[trade.symbol].append(trade)

    for symbol, trades in by_symbol.items():
        logger.info(f"【{symbol}】")
        for trade in trades:
            logger.info(f"  ID {trade.id}: {trade.direction} {trade.filled_quantity}股 "
                       f"@ ${trade.filled_price} ({trade.filled_time})")
        logger.info("")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='修复孤立交易 - 创建特殊持仓')
    parser.add_argument('--dry-run', action='store_true', help='只打印要修改的内容')
    parser.add_argument('--verify', action='store_true', help='只验证当前状态')
    parser.add_argument('--list', action='store_true', help='列出孤立交易')

    args = parser.parse_args()

    if args.list:
        list_orphaned()
    elif args.verify:
        verify_fix()
    else:
        fix_orphaned_trades(dry_run=args.dry_run)
        if not args.dry_run:
            verify_fix()


if __name__ == '__main__':
    main()
