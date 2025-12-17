"""
交易洞察生成器

基于规则引擎生成交易洞察和改进建议
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """洞察数据类"""
    category: str  # entry, exit, risk, behavior, pattern
    type: str  # positive, negative, neutral, warning
    title: str
    description: str
    evidence: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    priority: int = 50  # 0-100, higher = more important


class InsightGenerator:
    """
    基于规则的洞察生成器

    分析单笔交易或交易组合，生成可操作的洞察
    """

    def __init__(self):
        self.insights: List[Insight] = []

    def generate_position_insights(
        self,
        position: Dict[str, Any],
        entry_indicators: Optional[Dict] = None,
        exit_indicators: Optional[Dict] = None,
        similar_positions: Optional[List[Dict]] = None,
    ) -> List[Insight]:
        """
        为单个持仓生成洞察

        Args:
            position: 持仓数据字典
            entry_indicators: 入场时技术指标
            exit_indicators: 出场时技术指标
            similar_positions: 类似的历史持仓（用于对比）

        Returns:
            List[Insight]: 洞察列表
        """
        self.insights = []

        # 1. 入场分析
        self._analyze_entry(position, entry_indicators)

        # 2. 出场分析
        self._analyze_exit(position, exit_indicators)

        # 3. 风险管理分析
        self._analyze_risk_management(position)

        # 4. 持仓时间分析
        self._analyze_holding_period(position)

        # 5. 费用分析
        self._analyze_fees(position)

        # 6. 与历史对比
        if similar_positions:
            self._compare_with_history(position, similar_positions)

        # 按优先级排序
        self.insights.sort(key=lambda x: x.priority, reverse=True)

        return self.insights

    def _analyze_entry(self, position: Dict, indicators: Optional[Dict]):
        """分析入场质量"""
        entry_score = position.get('entry_quality_score')
        direction = position.get('direction', 'long')
        net_pnl = position.get('net_pnl', 0)

        # 基于评分的洞察
        if entry_score is not None:
            if entry_score >= 80:
                self.insights.append(Insight(
                    category='entry',
                    type='positive',
                    title='优秀的入场时机',
                    description=f'入场质量评分 {entry_score:.1f}/100，时机把握良好',
                    evidence={'entry_score': entry_score},
                    priority=60
                ))
            elif entry_score < 50:
                self.insights.append(Insight(
                    category='entry',
                    type='negative',
                    title='入场时机有待改进',
                    description=f'入场质量评分仅 {entry_score:.1f}/100',
                    evidence={'entry_score': entry_score},
                    suggestion='建议等待更明确的技术信号再入场',
                    priority=70
                ))

        # 基于技术指标的洞察
        if indicators:
            rsi = indicators.get('rsi_14')
            if rsi is not None:
                if direction == 'long' and rsi > 70:
                    self.insights.append(Insight(
                        category='entry',
                        type='warning',
                        title='在超买区域做多',
                        description=f'入场时 RSI = {rsi:.1f}，处于超买区域 (>70)',
                        evidence={'rsi': rsi},
                        suggestion='避免在 RSI 超买时追涨',
                        priority=80
                    ))
                elif direction == 'short' and rsi < 30:
                    self.insights.append(Insight(
                        category='entry',
                        type='warning',
                        title='在超卖区域做空',
                        description=f'入场时 RSI = {rsi:.1f}，处于超卖区域 (<30)',
                        evidence={'rsi': rsi},
                        suggestion='避免在 RSI 超卖时追空',
                        priority=80
                    ))

            # 布林带分析
            bb_upper = indicators.get('bb_upper')
            bb_lower = indicators.get('bb_lower')
            close = indicators.get('close')

            if bb_upper and bb_lower and close:
                if close > bb_upper and direction == 'long':
                    self.insights.append(Insight(
                        category='entry',
                        type='warning',
                        title='在布林带上轨上方买入',
                        description='入场价格已突破布林带上轨，可能存在短期回调风险',
                        evidence={'close': close, 'bb_upper': bb_upper},
                        priority=65
                    ))

    def _analyze_exit(self, position: Dict, indicators: Optional[Dict]):
        """分析出场质量"""
        exit_score = position.get('exit_quality_score')
        net_pnl = position.get('net_pnl', 0)
        mfe = position.get('mfe', 0)  # Maximum Favorable Excursion
        mae = position.get('mae', 0)  # Maximum Adverse Excursion

        if exit_score is not None:
            if exit_score >= 80:
                self.insights.append(Insight(
                    category='exit',
                    type='positive',
                    title='出场时机把握良好',
                    description=f'出场质量评分 {exit_score:.1f}/100',
                    evidence={'exit_score': exit_score},
                    priority=60
                ))
            elif exit_score < 50:
                self.insights.append(Insight(
                    category='exit',
                    type='negative',
                    title='出场时机有待改进',
                    description=f'出场质量评分仅 {exit_score:.1f}/100',
                    evidence={'exit_score': exit_score},
                    suggestion='考虑使用移动止盈或技术指标信号出场',
                    priority=70
                ))

        # MFE 分析 - 是否过早止盈
        if mfe and net_pnl and net_pnl > 0:
            capture_ratio = net_pnl / mfe if mfe > 0 else 0
            if capture_ratio < 0.3:
                self.insights.append(Insight(
                    category='exit',
                    type='warning',
                    title='过早止盈',
                    description=f'最大浮盈 ${mfe:.2f}，实际盈利 ${net_pnl:.2f}，只捕获了 {capture_ratio*100:.1f}% 的潜在利润',
                    evidence={'mfe': mfe, 'net_pnl': net_pnl, 'capture_ratio': capture_ratio},
                    suggestion='考虑使用移动止盈，让利润奔跑',
                    priority=75
                ))

    def _analyze_risk_management(self, position: Dict):
        """分析风险管理"""
        mae = position.get('mae', 0)
        net_pnl = position.get('net_pnl', 0)
        open_price = position.get('open_price', 0)
        quantity = position.get('quantity', 0)
        risk_score = position.get('risk_mgmt_score')

        cost_basis = open_price * quantity if open_price and quantity else 0

        # MAE 分析 - 持仓期间最大浮亏
        if mae and mae < 0 and cost_basis > 0:
            mae_pct = abs(mae) / cost_basis * 100
            if mae_pct > 10:
                insight_type = 'warning' if net_pnl >= 0 else 'negative'
                self.insights.append(Insight(
                    category='risk',
                    type=insight_type,
                    title='持仓期间经历较大回撤',
                    description=f'最大浮亏 ${abs(mae):.2f} ({mae_pct:.1f}%)',
                    evidence={'mae': mae, 'mae_pct': mae_pct},
                    suggestion='考虑设置更严格的止损位',
                    priority=80 if net_pnl < 0 else 60
                ))

        # 风险评分
        if risk_score is not None:
            if risk_score >= 80:
                self.insights.append(Insight(
                    category='risk',
                    type='positive',
                    title='风险控制良好',
                    description=f'风险管理评分 {risk_score:.1f}/100',
                    evidence={'risk_score': risk_score},
                    priority=55
                ))
            elif risk_score < 50:
                self.insights.append(Insight(
                    category='risk',
                    type='negative',
                    title='风险控制不足',
                    description=f'风险管理评分仅 {risk_score:.1f}/100',
                    evidence={'risk_score': risk_score},
                    suggestion='建议每笔交易设定明确的止损位',
                    priority=85
                ))

    def _analyze_holding_period(self, position: Dict):
        """分析持仓时间"""
        holding_days = position.get('holding_period_days')
        net_pnl = position.get('net_pnl', 0)
        strategy_type = position.get('strategy_type')

        if holding_days is None:
            return

        # 持仓时间与盈亏的关系
        if holding_days < 1 and net_pnl and net_pnl < 0:
            self.insights.append(Insight(
                category='behavior',
                type='warning',
                title='日内交易亏损',
                description=f'持仓不足1天，亏损 ${abs(net_pnl):.2f}',
                evidence={'holding_days': holding_days, 'net_pnl': net_pnl},
                suggestion='日内交易需要更严格的纪律和快速止损',
                priority=65
            ))
        elif holding_days > 30 and net_pnl and net_pnl < 0:
            self.insights.append(Insight(
                category='behavior',
                type='warning',
                title='长期持有亏损仓位',
                description=f'持仓 {holding_days} 天，亏损 ${abs(net_pnl):.2f}',
                evidence={'holding_days': holding_days, 'net_pnl': net_pnl},
                suggestion='避免死扛亏损仓位，及时止损释放资金',
                priority=75
            ))

    def _analyze_fees(self, position: Dict):
        """分析费用"""
        total_fees = position.get('total_fees', 0)
        realized_pnl = position.get('realized_pnl', 0)
        net_pnl = position.get('net_pnl', 0)

        if total_fees and realized_pnl:
            fee_ratio = abs(total_fees / realized_pnl) * 100 if realized_pnl != 0 else 0

            if fee_ratio > 20:
                self.insights.append(Insight(
                    category='behavior',
                    type='warning',
                    title='费用占比过高',
                    description=f'费用 ${total_fees:.2f} 占毛利润的 {fee_ratio:.1f}%',
                    evidence={'total_fees': total_fees, 'realized_pnl': realized_pnl, 'fee_ratio': fee_ratio},
                    suggestion='考虑增大单笔交易金额或减少交易频率',
                    priority=60
                ))

            # 费用导致盈利变亏损
            if realized_pnl > 0 and net_pnl < 0:
                self.insights.append(Insight(
                    category='behavior',
                    type='negative',
                    title='费用吞噬利润',
                    description=f'毛利润 ${realized_pnl:.2f}，扣除费用后亏损 ${abs(net_pnl):.2f}',
                    evidence={'realized_pnl': realized_pnl, 'net_pnl': net_pnl, 'total_fees': total_fees},
                    suggestion='小幅盈利的交易需要注意费用成本',
                    priority=70
                ))

    def _compare_with_history(self, position: Dict, similar_positions: List[Dict]):
        """与历史类似交易对比"""
        if not similar_positions:
            return

        symbol = position.get('symbol')
        current_pnl = position.get('net_pnl', 0)

        # 计算历史胜率和平均盈亏
        wins = [p for p in similar_positions if p.get('net_pnl', 0) > 0]
        losses = [p for p in similar_positions if p.get('net_pnl', 0) <= 0]

        win_rate = len(wins) / len(similar_positions) * 100 if similar_positions else 0
        avg_pnl = sum(p.get('net_pnl', 0) for p in similar_positions) / len(similar_positions)

        self.insights.append(Insight(
            category='pattern',
            type='neutral',
            title=f'{symbol} 历史交易分析',
            description=f'历史 {len(similar_positions)} 笔交易，胜率 {win_rate:.1f}%，平均盈亏 ${avg_pnl:.2f}',
            evidence={
                'total_trades': len(similar_positions),
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
            },
            priority=50
        ))

        # 当前表现与历史对比
        if current_pnl > avg_pnl * 1.5:
            self.insights.append(Insight(
                category='pattern',
                type='positive',
                title='表现优于历史平均',
                description=f'本次盈利 ${current_pnl:.2f}，优于历史平均 ${avg_pnl:.2f}',
                priority=55
            ))
        elif current_pnl < avg_pnl * 0.5 and avg_pnl > 0:
            self.insights.append(Insight(
                category='pattern',
                type='neutral',
                title='表现低于历史平均',
                description=f'本次盈亏 ${current_pnl:.2f}，低于历史平均 ${avg_pnl:.2f}',
                priority=55
            ))


def generate_insights_for_position(
    position_dict: Dict[str, Any],
    entry_indicators: Optional[Dict] = None,
    exit_indicators: Optional[Dict] = None,
    similar_positions: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    为持仓生成洞察的便捷函数

    Returns:
        List[Dict]: 洞察列表（字典格式）
    """
    generator = InsightGenerator()
    insights = generator.generate_position_insights(
        position_dict,
        entry_indicators,
        exit_indicators,
        similar_positions
    )

    return [
        {
            'category': i.category,
            'type': i.type,
            'title': i.title,
            'description': i.description,
            'evidence': i.evidence,
            'suggestion': i.suggestion,
            'priority': i.priority,
        }
        for i in insights
    ]
