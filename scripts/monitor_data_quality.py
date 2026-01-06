#!/usr/bin/env python3
"""
Production Data Quality Monitor - 生产数据质量监控

input: data/tradingcoach.db (生产数据库)
output: 数据质量报告，问题列表
pos: 独立的数据质量监控脚本，与代码测试分离

用途:
    - 定期监控生产数据质量
    - 导入新数据后验证数据完整性
    - 不用于 CI/CD（使用 pytest tests/data_integrity 代替）

使用方法:
    python scripts/monitor_data_quality.py           # 完整检查
    python scripts/monitor_data_quality.py --quick   # 快速检查
    python scripts/monitor_data_quality.py --fix     # 检查并提示修复

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
import os
import argparse
from datetime import datetime
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from config import DATABASE_PATH


class DataQualityChecker:
    """数据质量检查器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.issues: List[Dict] = []
        self.warnings: List[Dict] = []

    def close(self):
        self.conn.close()

    def add_issue(self, check_id: str, severity: str, message: str, count: int, details: str = None):
        """记录问题"""
        item = {
            'check_id': check_id,
            'severity': severity,
            'message': message,
            'count': count,
            'details': details
        }
        if severity in ['CRITICAL', 'HIGH']:
            self.issues.append(item)
        else:
            self.warnings.append(item)

    # ==================== 交易表检查 ====================

    def check_trade_required_fields(self):
        """DI-TRADE-001: 检查必填字段"""
        sql = """
            SELECT COUNT(*) FROM trades
            WHERE symbol IS NULL
               OR direction IS NULL
               OR filled_quantity IS NULL
               OR filled_time IS NULL
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-TRADE-001', 'CRITICAL', '交易记录缺少必填字段', count)
        return count == 0

    def check_trade_positive_quantity(self):
        """DI-TRADE-002: 检查数量为正数"""
        sql = "SELECT COUNT(*) FROM trades WHERE filled_quantity <= 0"
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-TRADE-002', 'HIGH', '交易数量不为正数', count)
        return count == 0

    def check_trade_positive_price(self):
        """DI-TRADE-003: 检查价格为正数"""
        sql = "SELECT COUNT(*) FROM trades WHERE filled_price <= 0"
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-TRADE-003', 'HIGH', '交易价格不为正数', count)
        return count == 0

    def check_trade_valid_direction(self):
        """DI-TRADE-004: 检查交易方向有效"""
        # 支持大小写两种格式
        sql = """
            SELECT COUNT(*) FROM trades
            WHERE UPPER(direction) NOT IN ('BUY', 'SELL', 'SELL_SHORT', 'BUY_TO_COVER')
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-TRADE-004', 'HIGH', '交易方向无效', count)
        return count == 0

    def check_trade_fingerprint_unique(self):
        """DI-TRADE-005: 检查指纹唯一性"""
        sql = """
            SELECT trade_fingerprint, COUNT(*) as cnt
            FROM trades
            WHERE trade_fingerprint IS NOT NULL
            GROUP BY trade_fingerprint
            HAVING cnt > 1
        """
        duplicates = self.conn.execute(sql).fetchall()
        if duplicates:
            self.add_issue('DI-TRADE-005', 'HIGH', '交易指纹重复', len(duplicates))
        return len(duplicates) == 0

    # ==================== 持仓表检查 ====================

    def check_position_required_fields(self):
        """DI-POS-001: 检查必填字段"""
        sql = """
            SELECT COUNT(*) FROM positions
            WHERE symbol IS NULL
               OR direction IS NULL
               OR open_time IS NULL
               OR open_price IS NULL
               OR quantity IS NULL
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-POS-001', 'CRITICAL', '持仓记录缺少必填字段', count)
        return count == 0

    def check_position_valid_direction(self):
        """DI-POS-002: 检查持仓方向有效"""
        sql = "SELECT COUNT(*) FROM positions WHERE direction NOT IN ('long', 'short')"
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-POS-002', 'HIGH', '持仓方向无效', count)
        return count == 0

    def check_closed_position_has_close_fields(self):
        """DI-POS-003: 检查已平仓持仓有平仓字段"""
        sql = """
            SELECT COUNT(*) FROM positions
            WHERE status = 'closed'
              AND (close_time IS NULL OR close_price IS NULL)
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-POS-003', 'HIGH', '已平仓持仓缺少平仓信息', count)
        return count == 0

    def check_position_pnl_calculation(self):
        """DI-POS-004: 检查盈亏计算正确性"""
        sql = """
            SELECT COUNT(*) FROM positions
            WHERE status = 'closed'
              AND realized_pnl IS NOT NULL
              AND close_price IS NOT NULL
              AND open_price IS NOT NULL
              AND (
                  (direction = 'long' AND is_option = 0 AND ABS(realized_pnl - (close_price - open_price) * quantity) > 1)
                  OR
                  (direction = 'short' AND is_option = 0 AND ABS(realized_pnl - (open_price - close_price) * quantity) > 1)
                  OR
                  (direction = 'long' AND is_option = 1 AND ABS(realized_pnl - (close_price - open_price) * quantity * 100) > 1)
                  OR
                  (direction = 'short' AND is_option = 1 AND ABS(realized_pnl - (open_price - close_price) * quantity * 100) > 1)
              )
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-POS-004', 'MEDIUM', '盈亏计算可能有误', count)
        return count == 0

    def check_option_fields_consistency(self):
        """DI-POS-005: 检查期权字段一致性"""
        sql = """
            SELECT COUNT(*) FROM positions
            WHERE is_option = 1
              AND (underlying_symbol IS NULL OR option_type IS NULL)
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-POS-005', 'MEDIUM', '期权持仓缺少期权字段', count)
        return count == 0

    def check_option_classification(self):
        """DI-POS-006: 检查期权分类正确性"""
        # 检查 symbol 看起来像期权但 is_option=0 的情况
        sql = """
            SELECT COUNT(*) FROM positions
            WHERE is_option = 0
              AND symbol GLOB '*[0-9][0-9][0-9][0-9][0-9][0-9][CP][0-9]*'
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-POS-006', 'HIGH', '疑似期权被标记为非期权', count,
                         '可使用 scripts/fix_option_classification.py 修复')
        return count == 0

    # ==================== 配对规则检查 ====================

    def check_position_has_trades(self):
        """DI-MATCH-001: 检查持仓有关联交易"""
        sql = """
            SELECT p.id, p.symbol
            FROM positions p
            LEFT JOIN trades t ON t.position_id = p.id
            WHERE t.id IS NULL
        """
        orphans = self.conn.execute(sql).fetchall()
        if orphans:
            self.add_issue('DI-MATCH-001', 'HIGH', '持仓无关联交易', len(orphans))
        return len(orphans) == 0

    def check_trade_position_link(self):
        """DI-MATCH-002: 检查交易的 position_id 有效"""
        sql = """
            SELECT COUNT(*) FROM trades t
            WHERE t.position_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM positions p WHERE p.id = t.position_id)
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-MATCH-002', 'HIGH', '交易关联的持仓不存在', count)
        return count == 0

    def check_direction_consistency(self):
        """DI-MATCH-003: 检查方向一致性"""
        # 做多持仓应该有 buy 开仓（支持大小写）
        sql = """
            SELECT COUNT(DISTINCT p.id)
            FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE LOWER(p.direction) = 'long'
              AND NOT EXISTS (
                  SELECT 1 FROM trades t2
                  WHERE t2.position_id = p.id AND UPPER(t2.direction) = 'BUY'
              )
        """
        count = self.conn.execute(sql).fetchone()[0]
        if count > 0:
            self.add_issue('DI-MATCH-003', 'MEDIUM', '做多持仓无买入交易', count)
        return count == 0

    # ==================== 运行所有检查 ====================

    def run_all_checks(self, quick: bool = False) -> Tuple[int, int]:
        """运行所有检查"""
        checks = [
            # 交易表检查
            self.check_trade_required_fields,
            self.check_trade_positive_quantity,
            self.check_trade_positive_price,
            self.check_trade_valid_direction,
            self.check_trade_fingerprint_unique,
            # 持仓表检查
            self.check_position_required_fields,
            self.check_position_valid_direction,
            self.check_closed_position_has_close_fields,
            self.check_option_fields_consistency,
            self.check_option_classification,
        ]

        if not quick:
            checks.extend([
                self.check_position_pnl_calculation,
                self.check_position_has_trades,
                self.check_trade_position_link,
                self.check_direction_consistency,
            ])

        passed = 0
        for check in checks:
            if check():
                passed += 1

        return passed, len(checks)


def print_report(checker: DataQualityChecker, passed: int, total: int):
    """打印报告"""
    print("=" * 60)
    print("  TradingCoach 数据质量监控报告")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {checker.db_path}")
    print()

    # 统计
    print(f"检查项: {passed}/{total} 通过")
    print()

    # 问题列表
    if checker.issues:
        print("❌ 严重问题:")
        for issue in checker.issues:
            print(f"  [{issue['severity']}] {issue['check_id']}: {issue['message']} ({issue['count']} 条)")
            if issue['details']:
                print(f"      提示: {issue['details']}")
        print()

    # 警告列表
    if checker.warnings:
        print("⚠️  警告:")
        for warn in checker.warnings:
            print(f"  [{warn['severity']}] {warn['check_id']}: {warn['message']} ({warn['count']} 条)")
        print()

    # 结论
    if not checker.issues and not checker.warnings:
        print("✅ 数据质量健康，未发现问题")
    elif not checker.issues:
        print("⚠️  数据质量基本健康，但有警告需关注")
    else:
        print("❌ 数据存在严重问题，需要修复")

    print()
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="TradingCoach 数据质量监控")
    parser.add_argument("--db", default=DATABASE_PATH, help="数据库路径")
    parser.add_argument("--quick", action="store_true", help="快速检查（跳过耗时检查）")
    parser.add_argument("--fix", action="store_true", help="检查后提示修复命令")

    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"错误: 数据库不存在: {args.db}")
        sys.exit(1)

    checker = DataQualityChecker(args.db)
    passed, total = checker.run_all_checks(quick=args.quick)
    print_report(checker, passed, total)

    if args.fix and checker.issues:
        print("修复建议:")
        for issue in checker.issues:
            if issue['check_id'] == 'DI-POS-006':
                print("  python scripts/fix_option_classification.py --apply")
        print()

    checker.close()

    # 退出码
    if checker.issues:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
