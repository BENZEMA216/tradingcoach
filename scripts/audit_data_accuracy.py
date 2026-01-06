#!/usr/bin/env python3
"""
input: config.DATABASE_PATH, tests/data_integrity/
output: 数据准确性审计报告、问题记录、可选修复
pos: 一键运行所有数据完整性检查，生成报告并提供修复选项

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

用法:
    python scripts/audit_data_accuracy.py                    # 仅审计
    python scripts/audit_data_accuracy.py --fix              # 审计并修复
    python scripts/audit_data_accuracy.py --report report.md # 生成 Markdown 报告
"""
import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import DATABASE_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Check Definitions
# ============================================================================

CHECKS = {
    # Trade Integrity
    "DI-TRADE-001": {
        "name": "交易指纹唯一性",
        "priority": "P0",
        "category": "trade",
        "sql": """
            SELECT trade_fingerprint, COUNT(*) as cnt
            FROM trades
            GROUP BY trade_fingerprint
            HAVING cnt > 1
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-TRADE-002": {
        "name": "交易必填字段非空",
        "priority": "P0",
        "category": "trade",
        "sql": """
            SELECT id, symbol, direction, filled_quantity, filled_price, filled_time
            FROM trades
            WHERE symbol IS NULL
               OR direction IS NULL
               OR filled_quantity IS NULL
               OR filled_price IS NULL
               OR filled_time IS NULL
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-TRADE-003": {
        "name": "交易方向枚举有效",
        "priority": "P0",
        "category": "trade",
        "sql": """
            SELECT id, direction FROM trades
            WHERE direction NOT IN ('BUY', 'SELL', 'SELL_SHORT', 'BUY_TO_COVER')
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-TRADE-004": {
        "name": "交易数量价格为正数",
        "priority": "P0",
        "category": "trade",
        "sql": """
            SELECT id, symbol, filled_quantity, filled_price FROM trades
            WHERE filled_quantity <= 0 OR filled_price <= 0
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-TRADE-005": {
        "name": "交易费用非负",
        "priority": "P1",
        "category": "trade",
        "sql": """
            SELECT id, symbol, commission, platform_fee, total_fee FROM trades
            WHERE commission < 0
               OR platform_fee < 0
               OR total_fee < 0
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-TRADE-006": {
        "name": "交易费用字段累加一致",
        "priority": "P2",
        "category": "trade",
        "sql": """
            SELECT id, symbol, total_fee,
                   COALESCE(commission, 0) +
                   COALESCE(platform_fee, 0) +
                   COALESCE(clearing_fee, 0) +
                   COALESCE(transaction_fee, 0) +
                   COALESCE(stamp_duty, 0) +
                   COALESCE(sec_fee, 0) +
                   COALESCE(option_regulatory_fee, 0) +
                   COALESCE(option_clearing_fee, 0) as calculated_fee
            FROM trades
            WHERE ABS(total_fee - (
                COALESCE(commission, 0) +
                COALESCE(platform_fee, 0) +
                COALESCE(clearing_fee, 0) +
                COALESCE(transaction_fee, 0) +
                COALESCE(stamp_duty, 0) +
                COALESCE(sec_fee, 0) +
                COALESCE(option_regulatory_fee, 0) +
                COALESCE(option_clearing_fee, 0)
            )) > 0.01
        """,
        "check_type": "query_empty",
        "fixable": False,
        "warning_only": True,  # P2 级别仅警告
    },
    "DI-TRADE-007": {
        "name": "期权交易字段完整",
        "priority": "P0",
        "category": "trade",
        "sql": """
            SELECT id, symbol, underlying_symbol, option_type, strike_price, expiration_date
            FROM trades
            WHERE is_option = 1
              AND (underlying_symbol IS NULL
                   OR option_type IS NULL
                   OR strike_price IS NULL
                   OR expiration_date IS NULL)
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": None,  # 使用脚本修复
        "fix_script": "scripts/fix_option_fields.py",
    },

    # Position Integrity
    "DI-POS-001": {
        "name": "持仓基础字段非空",
        "priority": "P0",
        "category": "position",
        "sql": """
            SELECT id, symbol, direction, status, open_price, open_time, quantity
            FROM positions
            WHERE symbol IS NULL
               OR direction IS NULL
               OR status IS NULL
               OR open_price IS NULL
               OR open_time IS NULL
               OR quantity IS NULL
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-POS-002": {
        "name": "持仓方向枚举有效",
        "priority": "P0",
        "category": "position",
        "sql": """
            SELECT id, direction FROM positions
            WHERE direction NOT IN ('long', 'short')
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-POS-003": {
        "name": "持仓状态枚举有效",
        "priority": "P0",
        "category": "position",
        "sql": """
            SELECT id, status FROM positions
            WHERE status NOT IN ('OPEN', 'CLOSED', 'PARTIALLY_CLOSED')
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-POS-004": {
        "name": "已平仓持仓字段完整",
        "priority": "P0",
        "category": "position",
        "sql": """
            SELECT id, symbol, close_price, close_time, net_pnl
            FROM positions
            WHERE status = 'CLOSED'
              AND (close_price IS NULL
                   OR close_time IS NULL
                   OR net_pnl IS NULL)
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-POS-005": {
        "name": "开放持仓无平仓信息",
        "priority": "P1",
        "category": "position",
        "sql": """
            SELECT id, symbol, close_price, close_time
            FROM positions
            WHERE status = 'OPEN'
              AND (close_price IS NOT NULL
                   OR close_time IS NOT NULL)
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE positions
            SET close_price = NULL, close_time = NULL
            WHERE status = 'OPEN'
              AND (close_price IS NOT NULL OR close_time IS NOT NULL)
        """,
    },
    "DI-POS-006": {
        "name": "多头盈亏计算正确",
        "priority": "P0",
        "category": "position",
        "sql": """
            SELECT id, symbol, direction, open_price, close_price, quantity, is_option,
                   realized_pnl,
                   (close_price - open_price) * quantity *
                       CASE WHEN is_option = 1 THEN 100 ELSE 1 END as expected_pnl
            FROM positions
            WHERE direction = 'long'
              AND status = 'CLOSED'
              AND ABS(realized_pnl - (close_price - open_price) * quantity *
                  CASE WHEN is_option = 1 THEN 100 ELSE 1 END) > 0.01
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE positions
            SET realized_pnl = (close_price - open_price) * quantity *
                CASE WHEN is_option = 1 THEN 100 ELSE 1 END
            WHERE direction = 'long'
              AND status = 'CLOSED'
              AND ABS(realized_pnl - (close_price - open_price) * quantity *
                  CASE WHEN is_option = 1 THEN 100 ELSE 1 END) > 0.01
        """,
    },
    "DI-POS-007": {
        "name": "空头盈亏计算正确",
        "priority": "P0",
        "category": "position",
        "sql": """
            SELECT id, symbol, direction, open_price, close_price, quantity, is_option,
                   realized_pnl,
                   (open_price - close_price) * quantity *
                       CASE WHEN is_option = 1 THEN 100 ELSE 1 END as expected_pnl
            FROM positions
            WHERE direction = 'short'
              AND status = 'CLOSED'
              AND ABS(realized_pnl - (open_price - close_price) * quantity *
                  CASE WHEN is_option = 1 THEN 100 ELSE 1 END) > 0.01
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE positions
            SET realized_pnl = (open_price - close_price) * quantity *
                CASE WHEN is_option = 1 THEN 100 ELSE 1 END
            WHERE direction = 'short'
              AND status = 'CLOSED'
              AND ABS(realized_pnl - (open_price - close_price) * quantity *
                  CASE WHEN is_option = 1 THEN 100 ELSE 1 END) > 0.01
        """,
    },
    "DI-POS-008": {
        "name": "净盈亏计算正确",
        "priority": "P0",
        "category": "position",
        "sql": """
            SELECT id, symbol, realized_pnl, total_fees, net_pnl,
                   realized_pnl - total_fees as expected_net_pnl
            FROM positions
            WHERE status = 'CLOSED'
              AND ABS(net_pnl - (realized_pnl - total_fees)) > 0.01
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE positions
            SET net_pnl = realized_pnl - total_fees
            WHERE status = 'CLOSED'
              AND ABS(net_pnl - (realized_pnl - total_fees)) > 0.01
        """,
    },
    "DI-POS-010": {
        "name": "评分范围有效(0-100)",
        "priority": "P1",
        "category": "position",
        "sql": """
            SELECT id, symbol, overall_score FROM positions
            WHERE overall_score IS NOT NULL
              AND (overall_score < 0 OR overall_score > 100)
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE positions
            SET overall_score = CASE
                WHEN overall_score < 0 THEN 0
                WHEN overall_score > 100 THEN 100
                ELSE overall_score END
            WHERE overall_score IS NOT NULL
              AND (overall_score < 0 OR overall_score > 100)
        """,
    },
    "DI-POS-011": {
        "name": "评分等级与分数匹配",
        "priority": "P1",
        "category": "position",
        "sql": """
            SELECT id, symbol, overall_score, score_grade FROM positions
            WHERE overall_score IS NOT NULL
              AND score_grade IS NOT NULL
              AND NOT (
                (overall_score >= 95 AND score_grade = 'A+') OR
                (overall_score >= 90 AND overall_score < 95 AND score_grade = 'A') OR
                (overall_score >= 85 AND overall_score < 90 AND score_grade = 'A-') OR
                (overall_score >= 80 AND overall_score < 85 AND score_grade = 'B+') OR
                (overall_score >= 75 AND overall_score < 80 AND score_grade = 'B') OR
                (overall_score >= 70 AND overall_score < 75 AND score_grade = 'B-') OR
                (overall_score >= 65 AND overall_score < 70 AND score_grade = 'C+') OR
                (overall_score >= 60 AND overall_score < 65 AND score_grade = 'C') OR
                (overall_score >= 55 AND overall_score < 60 AND score_grade = 'C-') OR
                (overall_score >= 50 AND overall_score < 55 AND score_grade = 'D') OR
                (overall_score < 50 AND score_grade = 'F')
              )
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE positions
            SET score_grade = CASE
                WHEN overall_score >= 95 THEN 'A+'
                WHEN overall_score >= 90 THEN 'A'
                WHEN overall_score >= 85 THEN 'A-'
                WHEN overall_score >= 80 THEN 'B+'
                WHEN overall_score >= 75 THEN 'B'
                WHEN overall_score >= 70 THEN 'B-'
                WHEN overall_score >= 65 THEN 'C+'
                WHEN overall_score >= 60 THEN 'C'
                WHEN overall_score >= 55 THEN 'C-'
                WHEN overall_score >= 50 THEN 'D'
                ELSE 'F' END
            WHERE overall_score IS NOT NULL
              AND score_grade IS NOT NULL
              AND NOT (
                (overall_score >= 95 AND score_grade = 'A+') OR
                (overall_score >= 90 AND overall_score < 95 AND score_grade = 'A') OR
                (overall_score >= 85 AND overall_score < 90 AND score_grade = 'A-') OR
                (overall_score >= 80 AND overall_score < 85 AND score_grade = 'B+') OR
                (overall_score >= 75 AND overall_score < 80 AND score_grade = 'B') OR
                (overall_score >= 70 AND overall_score < 75 AND score_grade = 'B-') OR
                (overall_score >= 65 AND overall_score < 70 AND score_grade = 'C+') OR
                (overall_score >= 60 AND overall_score < 65 AND score_grade = 'C') OR
                (overall_score >= 55 AND overall_score < 60 AND score_grade = 'C-') OR
                (overall_score >= 50 AND overall_score < 55 AND score_grade = 'D') OR
                (overall_score < 50 AND score_grade = 'F')
              )
        """,
    },
    "DI-POS-012": {
        "name": "期权持仓字段完整",
        "priority": "P0",
        "category": "position",
        "sql": """
            SELECT id, symbol, option_type, strike_price, expiry_date
            FROM positions
            WHERE is_option = 1
              AND (option_type IS NULL
                   OR strike_price IS NULL
                   OR expiry_date IS NULL)
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_script": "scripts/fix_option_fields.py",
    },

    # Matching Integrity
    "DI-MATCH-001": {
        "name": "已平仓持仓开平仓价格完整",
        "priority": "P0",
        "category": "matching",
        "sql": """
            SELECT id, symbol, open_price, close_price
            FROM positions
            WHERE status = 'CLOSED'
              AND (open_price IS NULL OR close_price IS NULL)
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-MATCH-001b": {
        "name": "已平仓持仓有关联交易",
        "priority": "P0",
        "category": "matching",
        "sql": """
            SELECT p.id, p.symbol, COUNT(t.id) as trade_count
            FROM positions p
            LEFT JOIN trades t ON t.position_id = p.id
            WHERE p.status = 'CLOSED'
            GROUP BY p.id
            HAVING trade_count = 0
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-MATCH-002": {
        "name": "开放持仓交易数正确",
        "priority": "P1",
        "category": "matching",
        "sql": """
            SELECT p.id, p.symbol, COUNT(t.id) as trade_count
            FROM positions p
            LEFT JOIN trades t ON t.position_id = p.id
            WHERE p.status = 'OPEN'
            GROUP BY p.id
            HAVING trade_count != 1
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-MATCH-003a": {
        "name": "非期权多头交易方向一致",
        "priority": "P0",
        "category": "matching",
        "sql": """
            SELECT p.id, p.symbol, p.direction, t.direction as trade_dir
            FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE p.direction = 'long'
              AND p.is_option = 0
              AND t.direction NOT IN ('BUY', 'SELL')
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-MATCH-003b": {
        "name": "非期权空头交易方向一致",
        "priority": "P0",
        "category": "matching",
        "sql": """
            SELECT p.id, p.symbol, p.direction, t.direction as trade_dir
            FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE p.direction = 'short'
              AND p.is_option = 0
              AND t.direction NOT IN ('SELL_SHORT', 'BUY_TO_COVER')
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-FK-001": {
        "name": "Trade.position_id 外键有效",
        "priority": "P0",
        "category": "matching",
        "sql": """
            SELECT t.id, t.symbol, t.position_id
            FROM trades t
            LEFT JOIN positions p ON t.position_id = p.id
            WHERE t.position_id IS NOT NULL
              AND p.id IS NULL
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE trades SET position_id = NULL
            WHERE position_id IS NOT NULL
              AND position_id NOT IN (SELECT id FROM positions)
        """,
    },
    "DI-FK-002": {
        "name": "Trade.market_data_id 外键有效",
        "priority": "P1",
        "category": "matching",
        "sql": """
            SELECT t.id, t.symbol, t.market_data_id
            FROM trades t
            LEFT JOIN market_data m ON t.market_data_id = m.id
            WHERE t.market_data_id IS NOT NULL
              AND m.id IS NULL
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE trades SET market_data_id = NULL
            WHERE market_data_id IS NOT NULL
              AND market_data_id NOT IN (SELECT id FROM market_data)
        """,
    },

    # Business Rules
    "DI-BIZ-001": {
        "name": "开仓时间早于平仓时间",
        "priority": "P0",
        "category": "business",
        "sql": """
            SELECT id, symbol, open_time, close_time
            FROM positions
            WHERE status = 'CLOSED'
              AND open_time >= close_time
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-BIZ-002": {
        "name": "交易时间在合理范围",
        "priority": "P1",
        "category": "business",
        "sql": """
            SELECT id, symbol, filled_time
            FROM trades
            WHERE filled_time < '2020-01-01'
               OR filled_time > datetime('now', '+1 day')
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-BIZ-005": {
        "name": "持仓数量不超过交易数量",
        "priority": "P1",
        "category": "business",
        "sql": """
            SELECT p.id, p.symbol, p.quantity as pos_qty, t.filled_quantity as trade_qty
            FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE t.direction IN ('BUY', 'SELL_SHORT')
              AND p.quantity > t.filled_quantity
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-BIZ-006": {
        "name": "非期权持仓价格与交易一致",
        "priority": "P1",
        "category": "business",
        "sql": """
            SELECT p.id, p.symbol, p.open_price, t.filled_price
            FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE t.direction IN ('BUY', 'SELL_SHORT')
              AND p.is_option = 0
              AND ABS(p.open_price - t.filled_price) > 0.01
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE positions
            SET open_price = (
                SELECT t.filled_price FROM trades t
                WHERE t.position_id = positions.id
                  AND t.direction IN ('BUY', 'SELL_SHORT')
                LIMIT 1
            )
            WHERE is_option = 0
              AND id IN (
                SELECT p.id FROM positions p
                JOIN trades t ON t.position_id = p.id
                WHERE t.direction IN ('BUY', 'SELL_SHORT')
                  AND p.is_option = 0
                  AND ABS(p.open_price - t.filled_price) > 0.01
              )
        """,
    },

    # Market Data Integrity
    "DI-MD-001": {
        "name": "市场数据唯一约束",
        "priority": "P0",
        "category": "market_data",
        "sql": """
            SELECT symbol, timestamp, interval, COUNT(*) as cnt
            FROM market_data
            GROUP BY symbol, timestamp, interval
            HAVING cnt > 1
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-MD-002": {
        "name": "OHLC 逻辑正确",
        "priority": "P0",
        "category": "market_data",
        "sql": """
            SELECT id, symbol, timestamp, open, high, low, close
            FROM market_data
            WHERE low > open OR low > close
               OR high < open OR high < close
        """,
        "check_type": "query_empty",
        "fixable": False,
    },
    "DI-MD-003": {
        "name": "RSI 范围有效(0-100)",
        "priority": "P1",
        "category": "market_data",
        "sql": """
            SELECT id, symbol, timestamp, rsi_14
            FROM market_data
            WHERE rsi_14 IS NOT NULL
              AND (rsi_14 < 0 OR rsi_14 > 100)
        """,
        "check_type": "query_empty",
        "fixable": True,
        "fix_sql": """
            UPDATE market_data
            SET rsi_14 = NULL
            WHERE rsi_14 IS NOT NULL
              AND (rsi_14 < 0 OR rsi_14 > 100)
        """,
    },
}


# ============================================================================
# Audit Engine
# ============================================================================

class DataAuditor:
    """数据准确性审计器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.results: dict[str, dict[str, Any]] = {}
        self.issues: list[dict[str, Any]] = []

    def run_check(self, check_id: str, check_def: dict) -> dict:
        """运行单个检查"""
        session = self.Session()
        try:
            result = session.execute(text(check_def["sql"])).fetchall()

            if check_def["check_type"] == "query_empty":
                passed = len(result) == 0
                count = len(result)
            else:
                passed = True
                count = 0

            # 获取列名
            columns = []
            if result:
                columns = list(result[0]._mapping.keys()) if hasattr(result[0], '_mapping') else []

            return {
                "check_id": check_id,
                "name": check_def["name"],
                "priority": check_def["priority"],
                "category": check_def["category"],
                "passed": passed,
                "warning_only": check_def.get("warning_only", False),
                "count": count,
                "fixable": check_def.get("fixable", False),
                "columns": columns,
                "sample_rows": [dict(row._mapping) if hasattr(row, '_mapping') else list(row) for row in result[:10]],
            }
        except Exception as e:
            return {
                "check_id": check_id,
                "name": check_def["name"],
                "priority": check_def["priority"],
                "category": check_def["category"],
                "passed": False,
                "warning_only": False,
                "count": -1,
                "error": str(e),
                "fixable": False,
                "columns": [],
                "sample_rows": [],
            }
        finally:
            session.close()

    def run_all_checks(self) -> dict:
        """运行所有检查"""
        logger.info("=" * 60)
        logger.info("开始数据准确性审计")
        logger.info(f"数据库: {self.db_path}")
        logger.info("=" * 60)

        categories = {}
        total_passed = 0
        total_failed = 0
        total_warnings = 0

        for check_id, check_def in CHECKS.items():
            result = self.run_check(check_id, check_def)
            self.results[check_id] = result

            category = check_def["category"]
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0, "warnings": 0, "checks": []}

            if result["passed"]:
                total_passed += 1
                categories[category]["passed"] += 1
                status = "✓"
            elif result.get("warning_only"):
                total_warnings += 1
                categories[category]["warnings"] += 1
                status = "⚠"
            else:
                total_failed += 1
                categories[category]["failed"] += 1
                status = "✗"
                self.issues.append(result)

            categories[category]["checks"].append(result)

            logger.info(f"[{status}] {check_id}: {check_def['name']} "
                       f"({result['count']} 条{'问题' if result['count'] > 0 else ''})")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "database": self.db_path,
            "total_checks": len(CHECKS),
            "passed": total_passed,
            "failed": total_failed,
            "warnings": total_warnings,
            "categories": categories,
            "issues": self.issues,
        }

        logger.info("=" * 60)
        logger.info(f"审计完成: {total_passed} 通过 / {total_failed} 失败 / {total_warnings} 警告")
        logger.info("=" * 60)

        return summary

    def backup_database(self) -> str:
        """备份数据库"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"数据库已备份到: {backup_path}")
        return backup_path

    def fix_issue(self, check_id: str) -> bool:
        """修复单个问题"""
        if check_id not in CHECKS:
            logger.error(f"未知检查项: {check_id}")
            return False

        check_def = CHECKS[check_id]
        if not check_def.get("fixable"):
            logger.warning(f"{check_id} 不支持自动修复")
            return False

        session = self.Session()
        try:
            if "fix_sql" in check_def and check_def["fix_sql"]:
                session.execute(text(check_def["fix_sql"]))
                session.commit()
                logger.info(f"[修复] {check_id}: 执行 SQL 修复成功")
                return True
            elif "fix_script" in check_def:
                import subprocess
                script_path = Path(__file__).parent.parent / check_def["fix_script"]
                result = subprocess.run(
                    ["python3", str(script_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"[修复] {check_id}: 执行脚本修复成功")
                    return True
                else:
                    logger.error(f"[修复] {check_id}: 脚本执行失败 - {result.stderr}")
                    return False
            else:
                logger.warning(f"{check_id} 无可用修复方法")
                return False
        except Exception as e:
            session.rollback()
            logger.error(f"[修复] {check_id}: 失败 - {e}")
            return False
        finally:
            session.close()

    def fix_all_issues(self) -> dict:
        """修复所有可修复的问题"""
        logger.info("开始修复问题...")

        # 先备份
        backup_path = self.backup_database()

        fixed = 0
        failed = 0

        for issue in self.issues:
            check_id = issue["check_id"]
            if CHECKS[check_id].get("fixable"):
                if self.fix_issue(check_id):
                    fixed += 1
                else:
                    failed += 1

        logger.info(f"修复完成: {fixed} 成功 / {failed} 失败")
        logger.info(f"备份位置: {backup_path}")

        return {
            "backup_path": backup_path,
            "fixed": fixed,
            "failed": failed,
        }

    def generate_report(self, output_path: str = None) -> str:
        """生成 Markdown 报告"""
        if not self.results:
            self.run_all_checks()

        lines = [
            "# 数据准确性审计报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**数据库**: `{self.db_path}`",
            "",
            "## 概要",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总检查项 | {len(CHECKS)} |",
            f"| 通过 | {sum(1 for r in self.results.values() if r['passed'])} |",
            f"| 失败 | {sum(1 for r in self.results.values() if not r['passed'] and not r.get('warning_only'))} |",
            f"| 警告 | {sum(1 for r in self.results.values() if r.get('warning_only') and not r['passed'])} |",
            "",
        ]

        # 按类别分组
        categories = {}
        for check_id, result in self.results.items():
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((check_id, result))

        category_names = {
            "trade": "交易记录",
            "position": "持仓记录",
            "matching": "FIFO 配对",
            "business": "业务规则",
            "market_data": "市场数据",
        }

        for cat, checks in categories.items():
            lines.append(f"## {category_names.get(cat, cat)}")
            lines.append("")
            lines.append("| 检查项 | 名称 | 优先级 | 状态 | 问题数 | 可修复 |")
            lines.append("|--------|------|--------|------|--------|--------|")

            for check_id, result in checks:
                if result["passed"]:
                    status = "✅ 通过"
                elif result.get("warning_only"):
                    status = "⚠️ 警告"
                else:
                    status = "❌ 失败"

                fixable = "是" if result.get("fixable") else "-"
                count = result["count"] if result["count"] >= 0 else "错误"

                lines.append(f"| {check_id} | {result['name']} | {result['priority']} | {status} | {count} | {fixable} |")

            lines.append("")

        # 问题详情
        if self.issues:
            lines.append("## 问题详情")
            lines.append("")

            for issue in self.issues:
                lines.append(f"### {issue['check_id']}: {issue['name']}")
                lines.append("")
                lines.append(f"- **优先级**: {issue['priority']}")
                lines.append(f"- **问题数量**: {issue['count']}")
                lines.append(f"- **可修复**: {'是' if issue.get('fixable') else '否'}")
                lines.append("")

                if issue.get("sample_rows"):
                    lines.append("**示例数据**:")
                    lines.append("")
                    lines.append("```json")
                    lines.append(json.dumps(issue["sample_rows"][:5], indent=2, ensure_ascii=False, default=str))
                    lines.append("```")
                    lines.append("")

        report = "\n".join(lines)

        if output_path:
            Path(output_path).write_text(report, encoding="utf-8")
            logger.info(f"报告已保存到: {output_path}")

        return report


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="TradingCoach 数据准确性审计工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/audit_data_accuracy.py                    # 仅审计
    python scripts/audit_data_accuracy.py --fix              # 审计并修复
    python scripts/audit_data_accuracy.py --report audit.md  # 生成报告
    python scripts/audit_data_accuracy.py --json             # JSON 输出
        """
    )
    parser.add_argument("--fix", action="store_true", help="修复所有可修复的问题")
    parser.add_argument("--report", type=str, help="生成 Markdown 报告到指定文件")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    parser.add_argument("--check", type=str, help="只运行指定的检查项")
    parser.add_argument("--db", type=str, default=DATABASE_PATH, help="数据库路径")

    args = parser.parse_args()

    auditor = DataAuditor(args.db)

    if args.check:
        # 运行单个检查
        if args.check not in CHECKS:
            logger.error(f"未知检查项: {args.check}")
            logger.info(f"可用检查项: {', '.join(CHECKS.keys())}")
            sys.exit(1)

        result = auditor.run_check(args.check, CHECKS[args.check])
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            status = "通过" if result["passed"] else "失败"
            print(f"{args.check}: {result['name']} - {status} ({result['count']} 条问题)")
            if result.get("sample_rows"):
                print("示例数据:")
                for row in result["sample_rows"][:5]:
                    print(f"  {row}")
        sys.exit(0 if result["passed"] else 1)

    # 运行所有检查
    summary = auditor.run_all_checks()

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    elif args.report:
        auditor.generate_report(args.report)

    if args.fix and summary["failed"] > 0:
        fix_result = auditor.fix_all_issues()
        logger.info(f"修复结果: {fix_result['fixed']} 成功 / {fix_result['failed']} 失败")

        # 重新审计验证
        logger.info("重新验证...")
        auditor.results = {}
        auditor.issues = []
        new_summary = auditor.run_all_checks()

        if new_summary["failed"] < summary["failed"]:
            logger.info(f"✓ 问题减少: {summary['failed']} -> {new_summary['failed']}")
        elif new_summary["failed"] == 0:
            logger.info("✓ 所有问题已修复!")

    # 返回状态码
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
