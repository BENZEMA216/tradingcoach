"""
Data Quality Monitor - 数据质量监控仪表板

input: SQLite database, trades, positions, market_data tables
output: Data quality metrics, anomaly detection, health dashboard
pos: 数据质量保障 - 提供全面的数据质量监控和报告

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import statistics
import json
import sqlite3


class QualityLevel(Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"  # 95%+
    GOOD = "good"            # 85-95%
    FAIR = "fair"            # 70-85%
    POOR = "poor"            # 50-70%
    CRITICAL = "critical"    # <50%


class AnomalyType(Enum):
    """异常类型"""
    OUTLIER_VALUE = "outlier_value"
    MISSING_DATA = "missing_data"
    DUPLICATE_DATA = "duplicate_data"
    INCONSISTENT_DATA = "inconsistent_data"
    STALE_DATA = "stale_data"
    INVALID_RANGE = "invalid_range"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    ORPHAN_RECORD = "orphan_record"


@dataclass
class Anomaly:
    """异常记录"""
    anomaly_type: AnomalyType
    table: str
    record_id: Optional[int]
    field: Optional[str]
    current_value: Any
    expected_value: Optional[Any]
    severity: str  # critical, high, medium, low
    description: str
    detected_at: datetime = field(default_factory=datetime.now)
    auto_fixable: bool = False
    suggested_fix: Optional[str] = None


@dataclass
class QualityMetrics:
    """数据质量指标"""
    table_name: str
    total_records: int
    valid_records: int
    null_count: Dict[str, int]
    duplicate_count: int
    orphan_count: int
    outlier_count: int
    freshness_hours: float
    completeness_pct: float
    accuracy_pct: float
    consistency_pct: float
    overall_score: float
    quality_level: QualityLevel
    anomalies: List[Anomaly] = field(default_factory=list)


class DataQualityMonitor:
    """数据质量监控器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.anomalies: List[Anomaly] = []
        self.metrics: Dict[str, QualityMetrics] = {}

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # 核心检查方法
    # =========================================================================

    def check_trades_quality(self) -> QualityMetrics:
        """检查交易数据质量"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM trades")
        total = cursor.fetchone()[0]

        if total == 0:
            return QualityMetrics(
                table_name="trades",
                total_records=0,
                valid_records=0,
                null_count={},
                duplicate_count=0,
                orphan_count=0,
                outlier_count=0,
                freshness_hours=0,
                completeness_pct=0,
                accuracy_pct=0,
                consistency_pct=0,
                overall_score=0,
                quality_level=QualityLevel.CRITICAL,
            )

        anomalies = []

        # 1. 空值检查
        required_fields = ['symbol', 'direction', 'filled_quantity', 'filled_price', 'filled_time']
        null_count = {}
        for field in required_fields:
            cursor.execute(f"SELECT COUNT(*) FROM trades WHERE {field} IS NULL")
            count = cursor.fetchone()[0]
            null_count[field] = count
            if count > 0:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.MISSING_DATA,
                    table="trades",
                    record_id=None,
                    field=field,
                    current_value=f"{count} null values",
                    expected_value="0 null values",
                    severity="high",
                    description=f"发现 {count} 条交易记录 {field} 字段为空",
                ))

        # 2. 重复检查 (trade_fingerprint)
        cursor.execute("""
            SELECT trade_fingerprint, COUNT(*) as cnt
            FROM trades
            WHERE trade_fingerprint IS NOT NULL
            GROUP BY trade_fingerprint
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        duplicate_count = sum(row['cnt'] - 1 for row in duplicates)
        if duplicate_count > 0:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.DUPLICATE_DATA,
                table="trades",
                record_id=None,
                field="trade_fingerprint",
                current_value=f"{duplicate_count} duplicates",
                expected_value="0 duplicates",
                severity="high",
                description=f"发现 {duplicate_count} 条重复交易记录",
                auto_fixable=True,
                suggested_fix="DELETE duplicates keeping earliest id",
            ))

        # 3. 孤儿记录检查 (无关联持仓)
        cursor.execute("""
            SELECT COUNT(*) FROM trades
            WHERE position_id IS NULL
            AND status = 'FILLED'
            AND filled_time < datetime('now', '-7 days')
        """)
        orphan_count = cursor.fetchone()[0]
        if orphan_count > 0:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.ORPHAN_RECORD,
                table="trades",
                record_id=None,
                field="position_id",
                current_value=f"{orphan_count} orphans",
                expected_value="0 orphans",
                severity="medium",
                description=f"发现 {orphan_count} 条未关联持仓的交易记录",
            ))

        # 4. 异常值检查
        outlier_count = 0
        # 检查极端价格
        cursor.execute("""
            SELECT id, symbol, filled_price
            FROM trades
            WHERE filled_price <= 0 OR filled_price > 100000
        """)
        extreme_prices = cursor.fetchall()
        for row in extreme_prices:
            outlier_count += 1
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.OUTLIER_VALUE,
                table="trades",
                record_id=row['id'],
                field="filled_price",
                current_value=row['filled_price'],
                expected_value="0 < price <= 100000",
                severity="high",
                description=f"交易 {row['id']} ({row['symbol']}) 价格异常: {row['filled_price']}",
            ))

        # 检查极端数量
        cursor.execute("""
            SELECT id, symbol, filled_quantity
            FROM trades
            WHERE filled_quantity <= 0 OR filled_quantity > 1000000
        """)
        extreme_qty = cursor.fetchall()
        for row in extreme_qty:
            outlier_count += 1
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.OUTLIER_VALUE,
                table="trades",
                record_id=row['id'],
                field="filled_quantity",
                current_value=row['filled_quantity'],
                expected_value="0 < quantity <= 1000000",
                severity="high",
                description=f"交易 {row['id']} ({row['symbol']}) 数量异常: {row['filled_quantity']}",
            ))

        # 5. 数据新鲜度
        cursor.execute("SELECT MAX(filled_time) FROM trades")
        latest = cursor.fetchone()[0]
        if latest:
            latest_dt = datetime.fromisoformat(latest.replace('Z', '+00:00').replace(' ', 'T'))
            freshness_hours = (datetime.now(latest_dt.tzinfo) - latest_dt).total_seconds() / 3600
        else:
            freshness_hours = float('inf')

        # 6. 计算质量指标
        valid_records = total - sum(null_count.values()) - duplicate_count
        completeness_pct = (1 - sum(null_count.values()) / (total * len(required_fields))) * 100
        accuracy_pct = (1 - outlier_count / total) * 100 if total > 0 else 0
        consistency_pct = (1 - duplicate_count / total) * 100 if total > 0 else 0

        overall_score = (completeness_pct * 0.4 + accuracy_pct * 0.35 + consistency_pct * 0.25)

        if overall_score >= 95:
            quality_level = QualityLevel.EXCELLENT
        elif overall_score >= 85:
            quality_level = QualityLevel.GOOD
        elif overall_score >= 70:
            quality_level = QualityLevel.FAIR
        elif overall_score >= 50:
            quality_level = QualityLevel.POOR
        else:
            quality_level = QualityLevel.CRITICAL

        conn.close()

        metrics = QualityMetrics(
            table_name="trades",
            total_records=total,
            valid_records=valid_records,
            null_count=null_count,
            duplicate_count=duplicate_count,
            orphan_count=orphan_count,
            outlier_count=outlier_count,
            freshness_hours=freshness_hours,
            completeness_pct=completeness_pct,
            accuracy_pct=accuracy_pct,
            consistency_pct=consistency_pct,
            overall_score=overall_score,
            quality_level=quality_level,
            anomalies=anomalies,
        )

        self.metrics["trades"] = metrics
        self.anomalies.extend(anomalies)
        return metrics

    def check_positions_quality(self) -> QualityMetrics:
        """检查持仓数据质量"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM positions")
        total = cursor.fetchone()[0]

        if total == 0:
            return QualityMetrics(
                table_name="positions",
                total_records=0,
                valid_records=0,
                null_count={},
                duplicate_count=0,
                orphan_count=0,
                outlier_count=0,
                freshness_hours=0,
                completeness_pct=0,
                accuracy_pct=0,
                consistency_pct=0,
                overall_score=0,
                quality_level=QualityLevel.CRITICAL,
            )

        anomalies = []

        # 1. 空值检查
        required_fields = ['symbol', 'direction', 'status', 'open_price', 'open_time', 'quantity']
        null_count = {}
        for field in required_fields:
            cursor.execute(f"SELECT COUNT(*) FROM positions WHERE {field} IS NULL")
            count = cursor.fetchone()[0]
            null_count[field] = count

        # 2. 已平仓但缺少关键字段
        cursor.execute("""
            SELECT COUNT(*) FROM positions
            WHERE status = 'CLOSED'
            AND (close_price IS NULL OR close_time IS NULL OR net_pnl IS NULL)
        """)
        incomplete_closed = cursor.fetchone()[0]
        if incomplete_closed > 0:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.MISSING_DATA,
                table="positions",
                record_id=None,
                field="close_price/close_time/net_pnl",
                current_value=f"{incomplete_closed} incomplete",
                expected_value="0 incomplete",
                severity="high",
                description=f"发现 {incomplete_closed} 条已平仓持仓缺少平仓数据",
            ))

        # 3. 盈亏计算一致性检查
        cursor.execute("""
            SELECT id, symbol, direction, open_price, close_price, quantity,
                   realized_pnl, net_pnl, total_fees, is_option
            FROM positions
            WHERE status = 'CLOSED' AND realized_pnl IS NOT NULL
        """)
        positions = cursor.fetchall()

        outlier_count = 0
        for pos in positions:
            multiplier = 100 if pos['is_option'] else 1
            if pos['direction'] == 'long':
                expected_pnl = (pos['close_price'] - pos['open_price']) * pos['quantity'] * multiplier
            else:
                expected_pnl = (pos['open_price'] - pos['close_price']) * pos['quantity'] * multiplier

            actual_pnl = pos['realized_pnl']
            if actual_pnl and abs(actual_pnl - expected_pnl) > abs(expected_pnl) * 0.1:  # 10% 容差
                outlier_count += 1
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.INCONSISTENT_DATA,
                    table="positions",
                    record_id=pos['id'],
                    field="realized_pnl",
                    current_value=actual_pnl,
                    expected_value=round(expected_pnl, 2),
                    severity="medium",
                    description=f"持仓 {pos['id']} ({pos['symbol']}) 盈亏计算不一致",
                ))

        # 4. 评分范围检查
        cursor.execute("""
            SELECT id, symbol, overall_score
            FROM positions
            WHERE overall_score IS NOT NULL AND (overall_score < 0 OR overall_score > 100)
        """)
        invalid_scores = cursor.fetchall()
        for row in invalid_scores:
            outlier_count += 1
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.INVALID_RANGE,
                table="positions",
                record_id=row['id'],
                field="overall_score",
                current_value=row['overall_score'],
                expected_value="0-100",
                severity="medium",
                description=f"持仓 {row['id']} ({row['symbol']}) 评分超出范围: {row['overall_score']}",
                auto_fixable=True,
                suggested_fix="CLAMP to 0-100 range",
            ))

        # 5. 时间逻辑检查
        cursor.execute("""
            SELECT id, symbol, open_time, close_time
            FROM positions
            WHERE status = 'CLOSED' AND close_time < open_time
        """)
        time_errors = cursor.fetchall()
        for row in time_errors:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.BUSINESS_RULE_VIOLATION,
                table="positions",
                record_id=row['id'],
                field="close_time",
                current_value=row['close_time'],
                expected_value=f"> {row['open_time']}",
                severity="critical",
                description=f"持仓 {row['id']} ({row['symbol']}) 平仓时间早于开仓时间",
            ))

        # 6. 数据新鲜度
        cursor.execute("SELECT MAX(updated_at) FROM positions")
        latest = cursor.fetchone()[0]
        if latest:
            latest_dt = datetime.fromisoformat(latest.replace('Z', '+00:00').replace(' ', 'T'))
            freshness_hours = (datetime.now(latest_dt.tzinfo) - latest_dt).total_seconds() / 3600
        else:
            freshness_hours = float('inf')

        # 计算指标
        valid_records = total - sum(null_count.values()) - incomplete_closed
        completeness_pct = (1 - (sum(null_count.values()) + incomplete_closed) / (total * len(required_fields))) * 100
        accuracy_pct = (1 - outlier_count / total) * 100 if total > 0 else 0
        consistency_pct = (1 - len(time_errors) / total) * 100 if total > 0 else 0

        overall_score = (completeness_pct * 0.4 + accuracy_pct * 0.35 + consistency_pct * 0.25)

        if overall_score >= 95:
            quality_level = QualityLevel.EXCELLENT
        elif overall_score >= 85:
            quality_level = QualityLevel.GOOD
        elif overall_score >= 70:
            quality_level = QualityLevel.FAIR
        elif overall_score >= 50:
            quality_level = QualityLevel.POOR
        else:
            quality_level = QualityLevel.CRITICAL

        conn.close()

        metrics = QualityMetrics(
            table_name="positions",
            total_records=total,
            valid_records=valid_records,
            null_count=null_count,
            duplicate_count=0,
            orphan_count=0,
            outlier_count=outlier_count,
            freshness_hours=freshness_hours,
            completeness_pct=completeness_pct,
            accuracy_pct=accuracy_pct,
            consistency_pct=consistency_pct,
            overall_score=overall_score,
            quality_level=quality_level,
            anomalies=anomalies,
        )

        self.metrics["positions"] = metrics
        self.anomalies.extend(anomalies)
        return metrics

    def check_cross_table_consistency(self) -> List[Anomaly]:
        """检查跨表一致性"""
        conn = self._get_connection()
        cursor = conn.cursor()
        anomalies = []

        # 1. 检查 trades.position_id 外键有效性
        cursor.execute("""
            SELECT t.id, t.symbol, t.position_id
            FROM trades t
            LEFT JOIN positions p ON t.position_id = p.id
            WHERE t.position_id IS NOT NULL AND p.id IS NULL
        """)
        invalid_fk = cursor.fetchall()
        for row in invalid_fk:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.ORPHAN_RECORD,
                table="trades",
                record_id=row['id'],
                field="position_id",
                current_value=row['position_id'],
                expected_value="valid position id",
                severity="high",
                description=f"交易 {row['id']} ({row['symbol']}) 关联的持仓 {row['position_id']} 不存在",
                auto_fixable=True,
                suggested_fix="SET position_id = NULL",
            ))

        # 2. 检查持仓的交易关联
        cursor.execute("""
            SELECT p.id, p.symbol, p.status,
                   (SELECT COUNT(*) FROM trades t WHERE t.position_id = p.id) as trade_count
            FROM positions p
            WHERE p.status = 'CLOSED'
        """)
        positions = cursor.fetchall()
        for pos in positions:
            if pos['trade_count'] < 2:  # 已平仓应至少有开仓和平仓两笔交易
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.INCONSISTENT_DATA,
                    table="positions",
                    record_id=pos['id'],
                    field="trade_count",
                    current_value=pos['trade_count'],
                    expected_value=">= 2 for closed positions",
                    severity="medium",
                    description=f"已平仓持仓 {pos['id']} ({pos['symbol']}) 关联交易数不足: {pos['trade_count']}",
                ))

        # 3. 检查持仓数量与交易数量一致性
        cursor.execute("""
            SELECT p.id, p.symbol, p.quantity as pos_qty,
                   SUM(CASE WHEN t.direction IN ('BUY', 'BUY_TO_COVER') THEN t.filled_quantity ELSE 0 END) as buy_qty,
                   SUM(CASE WHEN t.direction IN ('SELL', 'SELL_SHORT') THEN t.filled_quantity ELSE 0 END) as sell_qty
            FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE p.status = 'CLOSED'
            GROUP BY p.id
        """)
        qty_checks = cursor.fetchall()
        for row in qty_checks:
            if row['buy_qty'] != row['sell_qty']:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.INCONSISTENT_DATA,
                    table="positions",
                    record_id=row['id'],
                    field="quantity",
                    current_value=f"buy={row['buy_qty']}, sell={row['sell_qty']}",
                    expected_value="buy_qty == sell_qty for closed",
                    severity="medium",
                    description=f"持仓 {row['id']} ({row['symbol']}) 买卖数量不匹配",
                ))

        conn.close()
        self.anomalies.extend(anomalies)
        return anomalies

    def detect_statistical_anomalies(self) -> List[Anomaly]:
        """检测统计异常值 (使用 IQR 方法)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        anomalies = []

        # 1. 盈亏异常值检测
        cursor.execute("""
            SELECT id, symbol, net_pnl
            FROM positions
            WHERE status = 'CLOSED' AND net_pnl IS NOT NULL
            ORDER BY net_pnl
        """)
        pnl_data = cursor.fetchall()

        if len(pnl_data) >= 10:
            pnl_values = [row['net_pnl'] for row in pnl_data]
            q1 = statistics.quantiles(pnl_values, n=4)[0]
            q3 = statistics.quantiles(pnl_values, n=4)[2]
            iqr = q3 - q1
            lower_bound = q1 - 3 * iqr
            upper_bound = q3 + 3 * iqr

            for row in pnl_data:
                if row['net_pnl'] < lower_bound or row['net_pnl'] > upper_bound:
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.OUTLIER_VALUE,
                        table="positions",
                        record_id=row['id'],
                        field="net_pnl",
                        current_value=row['net_pnl'],
                        expected_value=f"[{lower_bound:.2f}, {upper_bound:.2f}]",
                        severity="low",
                        description=f"持仓 {row['id']} ({row['symbol']}) 盈亏为统计异常值: ${row['net_pnl']:.2f}",
                    ))

        # 2. 持仓时间异常值检测
        cursor.execute("""
            SELECT id, symbol, holding_period_days
            FROM positions
            WHERE status = 'CLOSED' AND holding_period_days IS NOT NULL
            ORDER BY holding_period_days
        """)
        holding_data = cursor.fetchall()

        if len(holding_data) >= 10:
            holding_values = [row['holding_period_days'] for row in holding_data]
            q1 = statistics.quantiles(holding_values, n=4)[0]
            q3 = statistics.quantiles(holding_values, n=4)[2]
            iqr = q3 - q1
            upper_bound = q3 + 3 * iqr

            for row in holding_data:
                if row['holding_period_days'] > upper_bound:
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.OUTLIER_VALUE,
                        table="positions",
                        record_id=row['id'],
                        field="holding_period_days",
                        current_value=row['holding_period_days'],
                        expected_value=f"<= {upper_bound:.0f} days",
                        severity="low",
                        description=f"持仓 {row['id']} ({row['symbol']}) 持有时间异常长: {row['holding_period_days']} 天",
                    ))

        conn.close()
        self.anomalies.extend(anomalies)
        return anomalies

    # =========================================================================
    # 报告生成
    # =========================================================================

    def generate_dashboard(self) -> Dict[str, Any]:
        """生成数据质量仪表板"""
        # 运行所有检查
        trades_metrics = self.check_trades_quality()
        positions_metrics = self.check_positions_quality()
        cross_anomalies = self.check_cross_table_consistency()
        stat_anomalies = self.detect_statistical_anomalies()

        # 汇总
        total_records = trades_metrics.total_records + positions_metrics.total_records
        total_anomalies = len(self.anomalies)
        critical_count = len([a for a in self.anomalies if a.severity == 'critical'])
        high_count = len([a for a in self.anomalies if a.severity == 'high'])

        # 整体健康评分
        overall_score = (
            trades_metrics.overall_score * 0.4 +
            positions_metrics.overall_score * 0.6
        )

        if overall_score >= 95:
            health_status = "HEALTHY"
            health_color = "green"
        elif overall_score >= 85:
            health_status = "GOOD"
            health_color = "blue"
        elif overall_score >= 70:
            health_status = "WARNING"
            health_color = "yellow"
        else:
            health_status = "CRITICAL"
            health_color = "red"

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "health_status": health_status,
                "health_color": health_color,
                "overall_score": round(overall_score, 1),
                "total_records": total_records,
                "total_anomalies": total_anomalies,
                "critical_issues": critical_count,
                "high_issues": high_count,
            },
            "tables": {
                "trades": {
                    "total_records": trades_metrics.total_records,
                    "quality_level": trades_metrics.quality_level.value,
                    "overall_score": round(trades_metrics.overall_score, 1),
                    "completeness": round(trades_metrics.completeness_pct, 1),
                    "accuracy": round(trades_metrics.accuracy_pct, 1),
                    "consistency": round(trades_metrics.consistency_pct, 1),
                    "freshness_hours": round(trades_metrics.freshness_hours, 1),
                    "null_counts": trades_metrics.null_count,
                    "duplicates": trades_metrics.duplicate_count,
                    "outliers": trades_metrics.outlier_count,
                },
                "positions": {
                    "total_records": positions_metrics.total_records,
                    "quality_level": positions_metrics.quality_level.value,
                    "overall_score": round(positions_metrics.overall_score, 1),
                    "completeness": round(positions_metrics.completeness_pct, 1),
                    "accuracy": round(positions_metrics.accuracy_pct, 1),
                    "consistency": round(positions_metrics.consistency_pct, 1),
                    "freshness_hours": round(positions_metrics.freshness_hours, 1),
                    "null_counts": positions_metrics.null_count,
                    "outliers": positions_metrics.outlier_count,
                },
            },
            "anomalies": {
                "total": len(self.anomalies),
                "by_severity": {
                    "critical": critical_count,
                    "high": high_count,
                    "medium": len([a for a in self.anomalies if a.severity == 'medium']),
                    "low": len([a for a in self.anomalies if a.severity == 'low']),
                },
                "by_type": {
                    t.value: len([a for a in self.anomalies if a.anomaly_type == t])
                    for t in AnomalyType
                },
                "auto_fixable": len([a for a in self.anomalies if a.auto_fixable]),
                "details": [
                    {
                        "type": a.anomaly_type.value,
                        "table": a.table,
                        "record_id": a.record_id,
                        "field": a.field,
                        "severity": a.severity,
                        "description": a.description,
                        "auto_fixable": a.auto_fixable,
                    }
                    for a in self.anomalies[:50]  # 最多显示 50 条
                ],
            },
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """生成修复建议"""
        recommendations = []

        critical_anomalies = [a for a in self.anomalies if a.severity == 'critical']
        if critical_anomalies:
            recommendations.append(f"⚠️ 有 {len(critical_anomalies)} 个严重问题需要立即处理")

        auto_fixable = [a for a in self.anomalies if a.auto_fixable]
        if auto_fixable:
            recommendations.append(f"🔧 有 {len(auto_fixable)} 个问题可以自动修复")

        if self.metrics.get("trades"):
            if self.metrics["trades"].duplicate_count > 0:
                recommendations.append("📋 建议运行去重脚本清理重复交易记录")
            if self.metrics["trades"].orphan_count > 10:
                recommendations.append("🔗 建议检查未关联持仓的交易记录，重新运行配对")

        if self.metrics.get("positions"):
            if self.metrics["positions"].overall_score < 85:
                recommendations.append("📊 持仓数据质量较低，建议检查数据导入流程")

        return recommendations


def run_quality_check(db_path: str) -> Dict[str, Any]:
    """运行完整的数据质量检查"""
    monitor = DataQualityMonitor(db_path)
    return monitor.generate_dashboard()


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/tradingcoach.db"
    dashboard = run_quality_check(db_path)
    print(json.dumps(dashboard, indent=2, ensure_ascii=False))
