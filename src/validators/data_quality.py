"""
DataQualityChecker - 数据质量检查器

检查 Position 和 MarketData 数据的完整性和一致性
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """问题严重程度"""
    CRITICAL = "critical"    # 严重问题，数据不可用
    HIGH = "high"            # 高风险，可能影响分析准确性
    MEDIUM = "medium"        # 中等，部分功能受影响
    LOW = "low"              # 低风险，可以忽略
    INFO = "info"            # 信息性提示


@dataclass
class DataIssue:
    """数据问题"""
    issue_type: str                      # 问题类型代码
    severity: IssueSeverity              # 严重程度
    message: str                         # 问题描述
    field_name: Optional[str] = None     # 相关字段
    record_id: Optional[int] = None      # 相关记录ID
    record_type: Optional[str] = None    # 记录类型（Position/Trade等）
    suggested_fix: Optional[str] = None  # 建议修复方法
    context: Dict[str, Any] = field(default_factory=dict)  # 额外上下文

    def to_dict(self) -> Dict[str, Any]:
        return {
            'issue_type': self.issue_type,
            'severity': self.severity.value,
            'message': self.message,
            'field': self.field_name,
            'record_id': self.record_id,
            'record_type': self.record_type,
            'suggested_fix': self.suggested_fix,
            'context': self.context,
        }


@dataclass
class DataQualityReport:
    """数据质量报告"""
    total_records: int = 0
    checked_records: int = 0
    issues: List[DataIssue] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    check_time: datetime = field(default_factory=datetime.now)

    @property
    def critical_count(self) -> int:
        return len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL])

    @property
    def high_count(self) -> int:
        return len([i for i in self.issues if i.severity == IssueSeverity.HIGH])

    @property
    def is_healthy(self) -> bool:
        """数据是否健康（无 critical 问题）"""
        return self.critical_count == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_records': self.total_records,
            'checked_records': self.checked_records,
            'is_healthy': self.is_healthy,
            'critical_count': self.critical_count,
            'high_count': self.high_count,
            'total_issues': len(self.issues),
            'summary': self.summary,
            'check_time': self.check_time.isoformat(),
            'issues': [i.to_dict() for i in self.issues],
        }


class DataQualityChecker:
    """
    数据质量检查器

    检查各类数据的完整性、一致性和合理性
    """

    def __init__(self, db: Session):
        """
        初始化

        Args:
            db: SQLAlchemy Session
        """
        self.db = db

    def check_position(self, position) -> List[DataIssue]:
        """
        检查单个持仓的数据质量

        Args:
            position: Position 对象

        Returns:
            DataIssue 列表
        """
        issues = []
        pos_id = position.id
        record_type = "Position"

        # 1. 必填字段检查
        required_fields = ['symbol', 'direction', 'quantity', 'open_date']
        for field_name in required_fields:
            value = getattr(position, field_name, None)
            if value is None:
                issues.append(DataIssue(
                    issue_type="missing_required_field",
                    severity=IssueSeverity.CRITICAL,
                    message=f"缺少必填字段: {field_name}",
                    field=field_name,
                    record_id=pos_id,
                    record_type=record_type,
                    suggested_fix=f"请补充 {field_name} 字段"
                ))

        # 2. 已平仓持仓的必填字段
        if position.status and position.status.value == 'CLOSED':
            closed_required = ['close_date', 'close_price']
            for field_name in closed_required:
                value = getattr(position, field_name, None)
                if value is None:
                    issues.append(DataIssue(
                        issue_type="missing_closed_field",
                        severity=IssueSeverity.HIGH,
                        message=f"已平仓持仓缺少字段: {field_name}",
                        field=field_name,
                        record_id=pos_id,
                        record_type=record_type,
                    ))

        # 3. 时间顺序检查
        if position.open_date and position.close_date:
            open_time = position.open_date
            close_time = position.close_date

            if close_time < open_time:
                issues.append(DataIssue(
                    issue_type="time_order_error",
                    severity=IssueSeverity.CRITICAL,
                    message="平仓时间早于开仓时间",
                    field="close_date",
                    record_id=pos_id,
                    record_type=record_type,
                    context={
                        'open_date': str(open_time),
                        'close_date': str(close_time),
                    }
                ))

        # 4. 数值合理性检查
        if position.quantity is not None:
            qty = float(position.quantity)
            if qty <= 0:
                issues.append(DataIssue(
                    issue_type="invalid_quantity",
                    severity=IssueSeverity.CRITICAL,
                    message=f"数量无效: {qty}",
                    field="quantity",
                    record_id=pos_id,
                    record_type=record_type,
                ))
            elif qty > 1000000:  # 异常大的数量
                issues.append(DataIssue(
                    issue_type="suspicious_quantity",
                    severity=IssueSeverity.MEDIUM,
                    message=f"数量异常大: {qty}",
                    field="quantity",
                    record_id=pos_id,
                    record_type=record_type,
                ))

        # 5. 价格合理性检查
        for price_field in ['open_price', 'close_price']:
            price = getattr(position, price_field, None)
            if price is not None:
                price_val = float(price)
                if price_val < 0:
                    issues.append(DataIssue(
                        issue_type="negative_price",
                        severity=IssueSeverity.CRITICAL,
                        message=f"价格为负: {price_field}={price_val}",
                        field=price_field,
                        record_id=pos_id,
                        record_type=record_type,
                    ))
                elif price_val == 0:
                    issues.append(DataIssue(
                        issue_type="zero_price",
                        severity=IssueSeverity.HIGH,
                        message=f"价格为零: {price_field}",
                        field=price_field,
                        record_id=pos_id,
                        record_type=record_type,
                    ))

        # 6. 盈亏一致性检查
        if all([position.open_price, position.close_price, position.net_pnl, position.quantity]):
            open_p = float(position.open_price)
            close_p = float(position.close_price)
            qty = float(position.quantity)
            pnl = float(position.net_pnl)
            direction = position.direction

            # 计算预期盈亏（忽略费用）
            if direction and direction.value == 'BUY':
                expected_gross = (close_p - open_p) * qty
            else:
                expected_gross = (open_p - close_p) * qty

            # 允许 20% 的偏差（因为费用）
            if abs(pnl) > 0:
                deviation = abs(pnl - expected_gross) / abs(pnl)
                if deviation > 0.5:  # 偏差超过 50%
                    issues.append(DataIssue(
                        issue_type="pnl_inconsistency",
                        severity=IssueSeverity.MEDIUM,
                        message=f"盈亏数据可能不一致，偏差 {deviation*100:.0f}%",
                        field="net_pnl",
                        record_id=pos_id,
                        record_type=record_type,
                        context={
                            'expected_gross_pnl': round(expected_gross, 2),
                            'actual_net_pnl': round(pnl, 2),
                        }
                    ))

        # 7. 评分合理性检查
        score_fields = ['overall_score', 'entry_quality_score', 'exit_quality_score',
                       'trend_quality_score', 'risk_mgmt_score']
        for score_field in score_fields:
            score = getattr(position, score_field, None)
            if score is not None:
                score_val = float(score)
                if score_val < 0 or score_val > 100:
                    issues.append(DataIssue(
                        issue_type="invalid_score",
                        severity=IssueSeverity.MEDIUM,
                        message=f"评分超出范围[0,100]: {score_field}={score_val}",
                        field=score_field,
                        record_id=pos_id,
                        record_type=record_type,
                    ))

        # 8. 市场环境关联检查
        if position.status and position.status.value == 'CLOSED':
            if not position.entry_market_env_id:
                issues.append(DataIssue(
                    issue_type="missing_market_env",
                    severity=IssueSeverity.LOW,
                    message="缺少入场市场环境关联",
                    field="entry_market_env_id",
                    record_id=pos_id,
                    record_type=record_type,
                    suggested_fix="运行 market_env_fetcher 填充市场环境数据"
                ))

        return issues

    def check_all_positions(self) -> DataQualityReport:
        """
        检查所有持仓的数据质量

        Returns:
            DataQualityReport
        """
        from src.models.position import Position

        report = DataQualityReport()

        positions = self.db.query(Position).all()
        report.total_records = len(positions)

        issue_type_count = {}

        for pos in positions:
            issues = self.check_position(pos)
            report.issues.extend(issues)
            report.checked_records += 1

            for issue in issues:
                issue_type_count[issue.issue_type] = issue_type_count.get(issue.issue_type, 0) + 1

        report.summary = issue_type_count

        logger.info(
            f"Position quality check completed: "
            f"{report.checked_records} checked, "
            f"{len(report.issues)} issues found, "
            f"{report.critical_count} critical"
        )

        return report

    def check_market_data_coverage(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> float:
        """
        检查市场数据覆盖率

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            覆盖率百分比 (0-100)
        """
        from src.models.market_data import MarketData

        # 计算预期交易日数量（排除周末）
        expected_days = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # 周一到周五
                expected_days += 1
            current += timedelta(days=1)

        if expected_days == 0:
            return 100.0

        # 查询实际数据数量
        actual_count = self.db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.date >= start_date,
            MarketData.date <= end_date
        ).count()

        coverage = (actual_count / expected_days) * 100
        return min(coverage, 100.0)  # 不超过 100%

    def check_market_environment_coverage(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        检查市场环境数据覆盖率

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            覆盖率统计
        """
        from src.models.market_environment import MarketEnvironment

        # 计算预期交易日数量
        expected_days = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:
                expected_days += 1
            current += timedelta(days=1)

        # 查询实际数据
        records = self.db.query(MarketEnvironment).filter(
            MarketEnvironment.date >= start_date,
            MarketEnvironment.date <= end_date
        ).all()

        actual_count = len(records)

        # 检查数据完整度
        high_completeness = len([r for r in records if r.data_completeness and float(r.data_completeness) >= 80])
        vix_count = len([r for r in records if r.vix is not None])
        spy_count = len([r for r in records if r.spy_close is not None])

        return {
            'expected_days': expected_days,
            'actual_records': actual_count,
            'coverage_pct': round((actual_count / expected_days * 100) if expected_days > 0 else 0, 2),
            'high_completeness_count': high_completeness,
            'vix_coverage_pct': round((vix_count / expected_days * 100) if expected_days > 0 else 0, 2),
            'spy_coverage_pct': round((spy_count / expected_days * 100) if expected_days > 0 else 0, 2),
        }

    def generate_full_report(self) -> Dict[str, Any]:
        """
        生成完整的数据质量报告

        Returns:
            完整报告字典
        """
        from src.models.position import Position
        from datetime import date

        # 获取日期范围
        positions = self.db.query(Position).filter(
            Position.close_date.isnot(None)
        ).order_by(Position.close_date).all()

        if not positions:
            return {'error': 'No closed positions found'}

        first_date = positions[0].close_date
        last_date = positions[-1].close_date

        if hasattr(first_date, 'date'):
            first_date = first_date.date()
        if hasattr(last_date, 'date'):
            last_date = last_date.date()

        # 各项检查
        position_report = self.check_all_positions()
        market_env_coverage = self.check_market_environment_coverage(first_date, last_date)

        return {
            'generated_at': datetime.now().isoformat(),
            'date_range': {
                'start': str(first_date),
                'end': str(last_date),
            },
            'position_quality': position_report.to_dict(),
            'market_environment_coverage': market_env_coverage,
            'overall_health': position_report.is_healthy and market_env_coverage['coverage_pct'] >= 80,
        }
