"""
持仓对账器

input: 券商持仓快照CSV, 系统Position表
output: 对账报告(匹配/差异/缺失)
pos: 对账模块核心 - 验证系统计算持仓与券商记录的一致性

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
import json
import logging

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.base import init_database, get_session
from src.importers.english_csv_parser import PositionSnapshotParser

logger = logging.getLogger(__name__)


class ReconciliationStatus:
    """对账状态"""
    MATCHED = "matched"           # 完全匹配
    QUANTITY_MISMATCH = "quantity_mismatch"  # 数量不匹配
    MISSING_IN_SYSTEM = "missing_in_system"  # 系统中缺失
    MISSING_IN_BROKER = "missing_in_broker"  # 券商快照中缺失
    COST_MISMATCH = "cost_mismatch"  # 成本不匹配（可接受）


class ReconciliationItem:
    """对账项"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.symbol_name = None
        self.status = None

        # 券商数据
        self.broker_quantity = None
        self.broker_avg_cost = None
        self.broker_unrealized_pnl = None
        self.broker_current_price = None

        # 系统数据
        self.system_quantity = None
        self.system_avg_cost = None
        self.system_trades_count = None

        # 差异
        self.quantity_diff = None
        self.cost_diff = None
        self.notes = []

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'symbol_name': self.symbol_name,
            'status': self.status,
            'broker_quantity': self.broker_quantity,
            'broker_avg_cost': self.broker_avg_cost,
            'broker_unrealized_pnl': self.broker_unrealized_pnl,
            'system_quantity': self.system_quantity,
            'system_avg_cost': self.system_avg_cost,
            'system_trades_count': self.system_trades_count,
            'quantity_diff': self.quantity_diff,
            'cost_diff': self.cost_diff,
            'notes': self.notes,
        }


class ReconciliationReport:
    """对账报告"""

    def __init__(self):
        self.snapshot_date = None
        self.generated_at = datetime.now()
        self.items: List[ReconciliationItem] = []

        # 汇总
        self.total_positions = 0
        self.matched_count = 0
        self.quantity_mismatch_count = 0
        self.missing_in_system_count = 0
        self.missing_in_broker_count = 0
        self.cost_mismatch_count = 0

    def add_item(self, item: ReconciliationItem):
        self.items.append(item)
        self.total_positions += 1

        if item.status == ReconciliationStatus.MATCHED:
            self.matched_count += 1
        elif item.status == ReconciliationStatus.QUANTITY_MISMATCH:
            self.quantity_mismatch_count += 1
        elif item.status == ReconciliationStatus.MISSING_IN_SYSTEM:
            self.missing_in_system_count += 1
        elif item.status == ReconciliationStatus.MISSING_IN_BROKER:
            self.missing_in_broker_count += 1
        elif item.status == ReconciliationStatus.COST_MISMATCH:
            self.cost_mismatch_count += 1

    def to_dict(self) -> Dict:
        return {
            'snapshot_date': str(self.snapshot_date) if self.snapshot_date else None,
            'generated_at': self.generated_at.isoformat(),
            'summary': {
                'total_positions': self.total_positions,
                'matched': self.matched_count,
                'quantity_mismatch': self.quantity_mismatch_count,
                'missing_in_system': self.missing_in_system_count,
                'missing_in_broker': self.missing_in_broker_count,
                'cost_mismatch': self.cost_mismatch_count,
            },
            'items': [item.to_dict() for item in self.items],
        }

    def print_summary(self):
        """打印对账摘要"""
        print("\n" + "=" * 60)
        print("RECONCILIATION REPORT")
        print("=" * 60)
        print(f"Snapshot Date:    {self.snapshot_date}")
        print(f"Generated At:     {self.generated_at}")
        print()
        print("Summary:")
        print(f"  Total Positions:      {self.total_positions}")
        print(f"  ✓ Matched:            {self.matched_count}")
        print(f"  ⚠ Quantity Mismatch:  {self.quantity_mismatch_count}")
        print(f"  ✗ Missing in System:  {self.missing_in_system_count}")
        print(f"  ✗ Missing in Broker:  {self.missing_in_broker_count}")
        print(f"  ~ Cost Mismatch:      {self.cost_mismatch_count}")
        print()

        # 按状态分组显示
        if self.matched_count > 0:
            print("Matched Positions:")
            for item in self.items:
                if item.status == ReconciliationStatus.MATCHED:
                    print(f"  ✓ {item.symbol}: {item.broker_quantity} shares")

        if self.quantity_mismatch_count > 0:
            print("\nQuantity Mismatches:")
            for item in self.items:
                if item.status == ReconciliationStatus.QUANTITY_MISMATCH:
                    print(f"  ⚠ {item.symbol}: Broker={item.broker_quantity}, System={item.system_quantity} (diff={item.quantity_diff})")
                    for note in item.notes:
                        print(f"      {note}")

        if self.missing_in_system_count > 0:
            print("\nMissing in System:")
            for item in self.items:
                if item.status == ReconciliationStatus.MISSING_IN_SYSTEM:
                    print(f"  ✗ {item.symbol}: {item.broker_quantity} shares @ ${item.broker_avg_cost:.2f}")
                    for note in item.notes:
                        print(f"      {note}")

        if self.missing_in_broker_count > 0:
            print("\nMissing in Broker Snapshot:")
            for item in self.items:
                if item.status == ReconciliationStatus.MISSING_IN_BROKER:
                    print(f"  ✗ {item.symbol}: {item.system_quantity} shares (system)")
                    for note in item.notes:
                        print(f"      {note}")

        print("=" * 60)


class PositionReconciler:
    """持仓对账器"""

    def __init__(self, snapshot_path: str):
        """
        初始化对账器

        Args:
            snapshot_path: 持仓快照CSV文件路径
        """
        self.snapshot_path = Path(snapshot_path)
        self.session = None
        self.report = ReconciliationReport()

    def reconcile(self) -> ReconciliationReport:
        """执行对账"""
        logger.info("Starting position reconciliation...")

        try:
            # 1. 解析券商快照
            broker_positions = self._parse_broker_snapshot()
            logger.info(f"Loaded {len(broker_positions)} positions from broker snapshot")

            # 2. 获取系统计算的持仓
            system_positions = self._get_system_positions()
            logger.info(f"Found {len(system_positions)} positions in system")

            # 3. 对账
            self._compare_positions(broker_positions, system_positions)

            # 4. 保存快照到数据库
            self._save_snapshot(broker_positions)

            self.report.print_summary()
            return self.report

        except Exception as e:
            logger.error(f"Reconciliation failed: {e}", exc_info=True)
            raise

        finally:
            if self.session:
                self.session.close()

    def _parse_broker_snapshot(self) -> Dict[str, Dict]:
        """解析券商快照"""
        parser = PositionSnapshotParser(str(self.snapshot_path))
        parser.parse()
        positions = parser.get_positions_list()

        # 转换为字典（按symbol索引）
        result = {}
        for pos in positions:
            symbol = pos['symbol']
            result[symbol] = pos

        # 从文件名提取日期
        # Positions-Margin Universal Account(2663)-20251221-002024.csv
        import re
        match = re.search(r'-(\d{8})-', self.snapshot_path.name)
        if match:
            date_str = match.group(1)
            self.report.snapshot_date = datetime.strptime(date_str, '%Y%m%d').date()

        return result

    def _get_system_positions(self) -> Dict[str, Dict]:
        """获取系统中的持仓（基于未配对的交易）"""
        engine = init_database(config.DATABASE_URL, echo=False)
        self.session = get_session()

        from sqlalchemy import text

        # 计算每个标的的净持仓
        # 使用简化的FIFO计算：买入数量 - 卖出数量
        result = self.session.execute(text("""
            SELECT
                symbol,
                symbol_name,
                SUM(CASE WHEN direction IN ('buy', 'BUY') THEN filled_quantity ELSE 0 END) as total_bought,
                SUM(CASE WHEN direction IN ('sell', 'SELL') THEN filled_quantity ELSE 0 END) as total_sold,
                SUM(CASE WHEN direction IN ('buy', 'BUY') THEN filled_quantity * filled_price ELSE 0 END) as total_buy_cost,
                COUNT(*) as trade_count
            FROM trades
            WHERE status = 'FILLED' OR status = '全部成交'
            GROUP BY symbol
            HAVING SUM(CASE WHEN direction IN ('buy', 'BUY') THEN filled_quantity ELSE 0 END) -
                   SUM(CASE WHEN direction IN ('sell', 'SELL') THEN filled_quantity ELSE 0 END) != 0
        """))

        positions = {}
        for row in result.fetchall():
            symbol, symbol_name, bought, sold, buy_cost, trade_count = row

            net_quantity = (bought or 0) - (sold or 0)
            if net_quantity != 0:
                avg_cost = (buy_cost / bought) if bought and bought > 0 else 0

                positions[symbol] = {
                    'symbol': symbol,
                    'symbol_name': symbol_name,
                    'quantity': net_quantity,
                    'avg_cost': avg_cost,
                    'trade_count': trade_count,
                }

        return positions

    def _compare_positions(self, broker: Dict[str, Dict], system: Dict[str, Dict]):
        """对比持仓"""
        all_symbols = set(broker.keys()) | set(system.keys())

        for symbol in sorted(all_symbols):
            item = ReconciliationItem(symbol)

            broker_pos = broker.get(symbol)
            system_pos = system.get(symbol)

            if broker_pos:
                item.symbol_name = broker_pos.get('symbol_name')
                item.broker_quantity = broker_pos.get('quantity')
                item.broker_avg_cost = broker_pos.get('avg_cost')
                item.broker_unrealized_pnl = broker_pos.get('unrealized_pnl')
                item.broker_current_price = broker_pos.get('current_price')

            if system_pos:
                item.system_quantity = system_pos.get('quantity')
                item.system_avg_cost = system_pos.get('avg_cost')
                item.system_trades_count = system_pos.get('trade_count')

            # 确定状态
            if broker_pos and not system_pos:
                item.status = ReconciliationStatus.MISSING_IN_SYSTEM
                item.notes.append("Position exists in broker but not in system trades")

            elif system_pos and not broker_pos:
                item.status = ReconciliationStatus.MISSING_IN_BROKER
                item.notes.append("Position exists in system but not in broker snapshot")

            elif broker_pos and system_pos:
                # 比较数量
                broker_qty = item.broker_quantity or 0
                system_qty = item.system_quantity or 0
                item.quantity_diff = broker_qty - system_qty

                if abs(item.quantity_diff) < 0.01:  # 允许小误差
                    # 数量匹配，检查成本
                    broker_cost = item.broker_avg_cost or 0
                    system_cost = item.system_avg_cost or 0

                    if system_cost > 0:
                        item.cost_diff = abs(broker_cost - system_cost) / system_cost
                    else:
                        item.cost_diff = 0

                    if item.cost_diff < 0.05:  # 5%误差内
                        item.status = ReconciliationStatus.MATCHED
                    else:
                        item.status = ReconciliationStatus.COST_MISMATCH
                        item.notes.append(f"Cost differs by {item.cost_diff*100:.1f}%")
                else:
                    item.status = ReconciliationStatus.QUANTITY_MISMATCH
                    item.notes.append(f"Need to check trade history for {symbol}")

            self.report.add_item(item)

    def _save_snapshot(self, positions: Dict[str, Dict]):
        """保存快照到数据库"""
        if self.session is None:
            return

        try:
            from sqlalchemy import text

            # 计算汇总
            total_value = sum(
                (p.get('market_value') or 0)
                for p in positions.values()
            )
            total_pnl = sum(
                (p.get('unrealized_pnl') or 0)
                for p in positions.values()
            )

            # 转换positions为可序列化格式
            positions_json = []
            for symbol, pos in positions.items():
                pos_copy = {k: v for k, v in pos.items()}
                # 转换date对象
                if 'expiry_date' in pos_copy and pos_copy['expiry_date']:
                    pos_copy['expiry_date'] = str(pos_copy['expiry_date'])
                positions_json.append(pos_copy)

            self.session.execute(text("""
                INSERT INTO position_snapshots (
                    snapshot_date, source, total_positions,
                    total_market_value, total_unrealized_pnl,
                    positions_json, status, reconciliation_report
                ) VALUES (
                    :snapshot_date, :source, :total_positions,
                    :total_market_value, :total_unrealized_pnl,
                    :positions_json, :status, :reconciliation_report
                )
            """), {
                'snapshot_date': self.report.snapshot_date,
                'source': 'futu_csv',
                'total_positions': len(positions),
                'total_market_value': total_value,
                'total_unrealized_pnl': total_pnl,
                'positions_json': json.dumps(positions_json),
                'status': 'reconciled',
                'reconciliation_report': json.dumps(self.report.to_dict()),
            })
            self.session.commit()
            logger.info("Snapshot saved to database")

        except Exception as e:
            logger.warning(f"Failed to save snapshot: {e}")


def main():
    """命令行入口"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description='Reconcile broker position snapshot with system positions'
    )
    parser.add_argument(
        'snapshot_path',
        type=str,
        help='Path to position snapshot CSV file'
    )

    args = parser.parse_args()

    snapshot_path = Path(args.snapshot_path)
    if not snapshot_path.exists():
        logger.error(f"File not found: {snapshot_path}")
        sys.exit(1)

    reconciler = PositionReconciler(str(snapshot_path))
    report = reconciler.reconcile()

    # 输出JSON报告
    print("\nJSON Report:")
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
