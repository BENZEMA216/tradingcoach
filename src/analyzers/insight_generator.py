"""
交易洞察生成器

input: 持仓数据、技术指标、历史持仓
output: 洞察列表（含案例关联、模式统计、改进建议）
pos: 分析层 - 生成基于规则的可操作洞察

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@dataclass
class SupportingCase:
    """支撑案例"""
    position_id: int
    symbol: str
    pnl: float
    date: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PatternStats:
    """模式统计"""
    total_occurrences: int
    win_rate: float  # 0-100
    avg_pnl: float
    total_pnl: float


@dataclass
class Insight:
    """洞察数据类 - 增强版，支持案例关联"""
    category: str  # entry, exit, risk, behavior, pattern, event
    type: str  # positive, negative, neutral, warning
    title: str
    description: str
    evidence: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    priority: int = 50  # 0-100, higher = more important
    # 新增：案例关联
    supporting_cases: List[SupportingCase] = field(default_factory=list)
    pattern_stats: Optional[PatternStats] = None
    # 新增：根因标签
    root_cause: Optional[str] = None  # timing, direction, position_size, external_event, execution


class InsightGenerator:
    """
    基于规则的洞察生成器（增强版）

    分析单笔交易或交易组合，生成可操作的洞察
    支持案例关联、模式统计、根因分析
    """

    def __init__(self, all_positions: Optional[List[Dict]] = None):
        """
        初始化洞察生成器

        Args:
            all_positions: 所有历史持仓列表，用于案例关联
        """
        self.insights: List[Insight] = []
        self.all_positions = all_positions or []
        # 预处理：按模式分类持仓
        self._pattern_cache: Dict[str, List[Dict]] = {}

    def _find_cases_by_pattern(
        self,
        pattern_key: str,
        filter_fn: callable,
        limit: int = 5,
        exclude_id: Optional[int] = None,
    ) -> tuple[List[SupportingCase], Optional[PatternStats]]:
        """
        查找符合特定模式的案例

        Args:
            pattern_key: 模式标识（用于缓存）
            filter_fn: 过滤函数，接收position返回bool
            limit: 返回案例数量限制
            exclude_id: 排除的position_id

        Returns:
            (支撑案例列表, 模式统计)
        """
        if pattern_key not in self._pattern_cache:
            matching = [p for p in self.all_positions if filter_fn(p)]
            self._pattern_cache[pattern_key] = matching

        matching = self._pattern_cache[pattern_key]

        # 排除当前持仓
        if exclude_id:
            matching = [p for p in matching if p.get('id') != exclude_id]

        if not matching:
            return [], None

        # 计算统计
        wins = [p for p in matching if p.get('net_pnl', 0) > 0]
        total_pnl = sum(p.get('net_pnl', 0) for p in matching)
        avg_pnl = total_pnl / len(matching) if matching else 0
        win_rate = len(wins) / len(matching) * 100 if matching else 0

        stats = PatternStats(
            total_occurrences=len(matching),
            win_rate=win_rate,
            avg_pnl=avg_pnl,
            total_pnl=total_pnl,
        )

        # 按盈亏绝对值排序，取最典型的案例
        sorted_cases = sorted(matching, key=lambda p: abs(p.get('net_pnl', 0)), reverse=True)
        cases = [
            SupportingCase(
                position_id=p.get('id', 0),
                symbol=p.get('symbol', ''),
                pnl=p.get('net_pnl', 0),
                date=p.get('close_time', p.get('open_time', ''))[:10] if p.get('close_time') or p.get('open_time') else None,
            )
            for p in sorted_cases[:limit]
        ]

        return cases, stats

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
        """分析入场质量 - 增强版，含案例关联"""
        entry_score = position.get('entry_quality_score')
        direction = position.get('direction', 'long')
        net_pnl = position.get('net_pnl', 0)
        position_id = position.get('id')

        # 基于评分的洞察
        if entry_score is not None:
            if entry_score >= 80:
                # 查找高入场评分的案例
                cases, stats = self._find_cases_by_pattern(
                    'high_entry_score',
                    lambda p: p.get('entry_quality_score', 0) >= 80,
                    exclude_id=position_id,
                )
                self.insights.append(Insight(
                    category='entry',
                    type='positive',
                    title='优秀的入场时机',
                    description=f'入场质量评分 {entry_score:.1f}/100，时机把握良好',
                    evidence={'entry_score': entry_score},
                    priority=60,
                    supporting_cases=cases,
                    pattern_stats=stats,
                ))
            elif entry_score < 50:
                # 查找低入场评分的案例
                cases, stats = self._find_cases_by_pattern(
                    'low_entry_score',
                    lambda p: p.get('entry_quality_score', 0) < 50 and p.get('entry_quality_score') is not None,
                    exclude_id=position_id,
                )
                suggestion = '建议等待更明确的技术信号再入场'
                if stats and stats.win_rate < 40:
                    suggestion = f'历史 {stats.total_occurrences} 次低评分入场，胜率仅 {stats.win_rate:.1f}%。建议等待更明确的技术信号再入场'
                self.insights.append(Insight(
                    category='entry',
                    type='negative',
                    title='入场时机有待改进',
                    description=f'入场质量评分仅 {entry_score:.1f}/100',
                    evidence={'entry_score': entry_score},
                    suggestion=suggestion,
                    priority=70,
                    supporting_cases=cases,
                    pattern_stats=stats,
                    root_cause='timing',
                ))

        # 基于技术指标的洞察
        if indicators:
            rsi = indicators.get('rsi_14')
            if rsi is not None:
                if direction == 'long' and rsi > 70:
                    # 查找在超买区域做多的案例
                    cases, stats = self._find_cases_by_pattern(
                        'overbought_long',
                        lambda p: (
                            p.get('direction') == 'long' and
                            p.get('entry_rsi_14', 0) > 70
                        ),
                        exclude_id=position_id,
                    )
                    suggestion = '避免在 RSI 超买时追涨'
                    if stats and stats.win_rate < 50:
                        suggestion = f'历史 {stats.total_occurrences} 次超买追涨，胜率仅 {stats.win_rate:.1f}%。避免在 RSI>70 时追涨'
                    self.insights.append(Insight(
                        category='entry',
                        type='warning',
                        title='在超买区域做多',
                        description=f'入场时 RSI = {rsi:.1f}，处于超买区域 (>70)',
                        evidence={'rsi': rsi},
                        suggestion=suggestion,
                        priority=80,
                        supporting_cases=cases,
                        pattern_stats=stats,
                        root_cause='timing',
                    ))
                elif direction == 'short' and rsi < 30:
                    # 查找在超卖区域做空的案例
                    cases, stats = self._find_cases_by_pattern(
                        'oversold_short',
                        lambda p: (
                            p.get('direction') == 'short' and
                            p.get('entry_rsi_14', 0) < 30
                        ),
                        exclude_id=position_id,
                    )
                    suggestion = '避免在 RSI 超卖时追空'
                    if stats and stats.win_rate < 50:
                        suggestion = f'历史 {stats.total_occurrences} 次超卖追空，胜率仅 {stats.win_rate:.1f}%。避免在 RSI<30 时追空'
                    self.insights.append(Insight(
                        category='entry',
                        type='warning',
                        title='在超卖区域做空',
                        description=f'入场时 RSI = {rsi:.1f}，处于超卖区域 (<30)',
                        evidence={'rsi': rsi},
                        suggestion=suggestion,
                        priority=80,
                        supporting_cases=cases,
                        pattern_stats=stats,
                        root_cause='timing',
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
                        priority=65,
                        root_cause='timing',
                    ))

    def _analyze_exit(self, position: Dict, indicators: Optional[Dict]):
        """分析出场质量 - 增强版，含案例关联"""
        exit_score = position.get('exit_quality_score')
        net_pnl = position.get('net_pnl', 0)
        mfe = position.get('mfe', 0)  # Maximum Favorable Excursion
        mae = position.get('mae', 0)  # Maximum Adverse Excursion
        position_id = position.get('id')

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
                # 查找低出场评分的案例
                cases, stats = self._find_cases_by_pattern(
                    'low_exit_score',
                    lambda p: p.get('exit_quality_score', 0) < 50 and p.get('exit_quality_score') is not None,
                    exclude_id=position_id,
                )
                suggestion = '考虑使用移动止盈或技术指标信号出场'
                if stats and stats.avg_pnl < 0:
                    suggestion = f'历史 {stats.total_occurrences} 次低评分出场，平均亏损 ${abs(stats.avg_pnl):.0f}。考虑使用移动止盈或技术指标信号出场'
                self.insights.append(Insight(
                    category='exit',
                    type='negative',
                    title='出场时机有待改进',
                    description=f'出场质量评分仅 {exit_score:.1f}/100',
                    evidence={'exit_score': exit_score},
                    suggestion=suggestion,
                    priority=70,
                    supporting_cases=cases,
                    pattern_stats=stats,
                    root_cause='timing',
                ))

        # MFE 分析 - 是否过早止盈
        if mfe and net_pnl and net_pnl > 0:
            capture_ratio = net_pnl / mfe if mfe > 0 else 0
            if capture_ratio < 0.3:
                # 查找过早止盈的案例
                cases, stats = self._find_cases_by_pattern(
                    'early_profit_take',
                    lambda p: (
                        p.get('mfe', 0) > 0 and
                        p.get('net_pnl', 0) > 0 and
                        p.get('net_pnl', 0) / p.get('mfe', 1) < 0.3
                    ),
                    exclude_id=position_id,
                )
                missed_profit = mfe - net_pnl
                suggestion = '考虑使用移动止盈，让利润奔跑'
                if stats:
                    total_missed = sum(
                        (p.get('mfe', 0) - p.get('net_pnl', 0))
                        for p in self._pattern_cache.get('early_profit_take', [])
                        if p.get('id') != position_id
                    )
                    if total_missed > 0:
                        suggestion = f'历史 {stats.total_occurrences} 次过早止盈，累计错失利润约 ${total_missed:.0f}。考虑使用移动止盈，让利润奔跑'
                self.insights.append(Insight(
                    category='exit',
                    type='warning',
                    title='过早止盈',
                    description=f'最大浮盈 ${mfe:.2f}，实际盈利 ${net_pnl:.2f}，只捕获了 {capture_ratio*100:.1f}% 的潜在利润',
                    evidence={'mfe': mfe, 'net_pnl': net_pnl, 'capture_ratio': capture_ratio, 'missed_profit': missed_profit},
                    suggestion=suggestion,
                    priority=75,
                    supporting_cases=cases,
                    pattern_stats=stats,
                    root_cause='execution',
                ))

    def _analyze_risk_management(self, position: Dict):
        """分析风险管理 - 增强版，含案例关联"""
        mae = position.get('mae', 0)
        net_pnl = position.get('net_pnl', 0)
        open_price = position.get('open_price', 0)
        quantity = position.get('quantity', 0)
        risk_score = position.get('risk_mgmt_score')
        position_id = position.get('id')

        cost_basis = open_price * quantity if open_price and quantity else 0

        # MAE 分析 - 持仓期间最大浮亏
        if mae and mae < 0 and cost_basis > 0:
            mae_pct = abs(mae) / cost_basis * 100
            if mae_pct > 10:
                # 查找经历大回撤的案例
                cases, stats = self._find_cases_by_pattern(
                    'large_drawdown',
                    lambda p: (
                        p.get('mae', 0) < 0 and
                        p.get('open_price', 0) > 0 and
                        p.get('quantity', 0) > 0 and
                        abs(p.get('mae', 0)) / (p.get('open_price', 0) * p.get('quantity', 1)) * 100 > 10
                    ),
                    exclude_id=position_id,
                )
                insight_type = 'warning' if net_pnl >= 0 else 'negative'
                suggestion = '考虑设置更严格的止损位'
                if stats and stats.win_rate < 40:
                    suggestion = f'历史 {stats.total_occurrences} 次大回撤，胜率仅 {stats.win_rate:.1f}%，累计亏损 ${abs(stats.total_pnl):.0f}。考虑设置更严格的止损位'
                self.insights.append(Insight(
                    category='risk',
                    type=insight_type,
                    title='持仓期间经历较大回撤',
                    description=f'最大浮亏 ${abs(mae):.2f} ({mae_pct:.1f}%)',
                    evidence={'mae': mae, 'mae_pct': mae_pct},
                    suggestion=suggestion,
                    priority=80 if net_pnl < 0 else 60,
                    supporting_cases=cases,
                    pattern_stats=stats,
                    root_cause='position_size' if mae_pct > 20 else 'timing',
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
                # 查找低风险评分的案例
                cases, stats = self._find_cases_by_pattern(
                    'low_risk_score',
                    lambda p: p.get('risk_mgmt_score', 0) < 50 and p.get('risk_mgmt_score') is not None,
                    exclude_id=position_id,
                )
                suggestion = '建议每笔交易设定明确的止损位'
                if stats and stats.avg_pnl < 0:
                    suggestion = f'历史 {stats.total_occurrences} 次低风控评分，平均亏损 ${abs(stats.avg_pnl):.0f}。建议每笔交易设定明确的止损位'
                self.insights.append(Insight(
                    category='risk',
                    type='negative',
                    title='风险控制不足',
                    description=f'风险管理评分仅 {risk_score:.1f}/100',
                    evidence={'risk_score': risk_score},
                    suggestion=suggestion,
                    priority=85,
                    supporting_cases=cases,
                    pattern_stats=stats,
                    root_cause='position_size',
                ))

    def _analyze_holding_period(self, position: Dict):
        """分析持仓时间 - 增强版，含案例关联"""
        holding_days = position.get('holding_period_days')
        net_pnl = position.get('net_pnl', 0)
        strategy_type = position.get('strategy_type')
        position_id = position.get('id')

        if holding_days is None:
            return

        # 持仓时间与盈亏的关系
        if holding_days < 1 and net_pnl and net_pnl < 0:
            # 查找日内交易亏损的案例
            cases, stats = self._find_cases_by_pattern(
                'intraday_loss',
                lambda p: (
                    p.get('holding_period_days', 999) < 1 and
                    p.get('net_pnl', 0) < 0
                ),
                exclude_id=position_id,
            )
            suggestion = '日内交易需要更严格的纪律和快速止损'
            if stats and stats.total_occurrences > 3:
                suggestion = f'历史 {stats.total_occurrences} 次日内亏损，累计亏损 ${abs(stats.total_pnl):.0f}。日内交易需要更严格的纪律和快速止损'
            self.insights.append(Insight(
                category='behavior',
                type='warning',
                title='日内交易亏损',
                description=f'持仓不足1天，亏损 ${abs(net_pnl):.2f}',
                evidence={'holding_days': holding_days, 'net_pnl': net_pnl},
                suggestion=suggestion,
                priority=65,
                supporting_cases=cases,
                pattern_stats=stats,
                root_cause='execution',
            ))
        elif holding_days > 30 and net_pnl and net_pnl < 0:
            # 查找长期持有亏损的案例
            cases, stats = self._find_cases_by_pattern(
                'long_hold_loss',
                lambda p: (
                    p.get('holding_period_days', 0) > 30 and
                    p.get('net_pnl', 0) < 0
                ),
                exclude_id=position_id,
            )
            suggestion = '避免死扛亏损仓位，及时止损释放资金'
            if stats and stats.total_occurrences > 2:
                avg_hold = sum(p.get('holding_period_days', 0) for p in self._pattern_cache.get('long_hold_loss', [])) / max(1, stats.total_occurrences)
                suggestion = f'历史 {stats.total_occurrences} 次长持亏损（平均 {avg_hold:.0f} 天），累计亏损 ${abs(stats.total_pnl):.0f}。避免死扛亏损仓位，及时止损释放资金'
            self.insights.append(Insight(
                category='behavior',
                type='warning',
                title='长期持有亏损仓位',
                description=f'持仓 {holding_days} 天，亏损 ${abs(net_pnl):.2f}',
                evidence={'holding_days': holding_days, 'net_pnl': net_pnl},
                suggestion=suggestion,
                priority=75,
                supporting_cases=cases,
                pattern_stats=stats,
                root_cause='execution',
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
    all_positions: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    为持仓生成洞察的便捷函数（增强版）

    Args:
        position_dict: 当前持仓数据
        entry_indicators: 入场时技术指标
        exit_indicators: 出场时技术指标
        similar_positions: 类似的历史持仓（用于对比）
        all_positions: 所有历史持仓（用于案例关联）

    Returns:
        List[Dict]: 洞察列表（字典格式），包含案例关联和模式统计
    """
    generator = InsightGenerator(all_positions=all_positions)
    insights = generator.generate_position_insights(
        position_dict,
        entry_indicators,
        exit_indicators,
        similar_positions
    )

    result = []
    for i in insights:
        insight_dict = {
            'category': i.category,
            'type': i.type,
            'title': i.title,
            'description': i.description,
            'evidence': i.evidence,
            'suggestion': i.suggestion,
            'priority': i.priority,
            'root_cause': i.root_cause,
        }

        # 添加支撑案例
        if i.supporting_cases:
            insight_dict['supporting_cases'] = [
                {
                    'position_id': case.position_id,
                    'symbol': case.symbol,
                    'pnl': case.pnl,
                    'date': case.date,
                    'description': case.description,
                }
                for case in i.supporting_cases
            ]

        # 添加模式统计
        if i.pattern_stats:
            insight_dict['pattern_stats'] = {
                'total_occurrences': i.pattern_stats.total_occurrences,
                'win_rate': i.pattern_stats.win_rate,
                'avg_pnl': i.pattern_stats.avg_pnl,
                'total_pnl': i.pattern_stats.total_pnl,
            }

        result.append(insight_dict)

    return result


def generate_portfolio_insights(
    positions: List[Dict[str, Any]],
    limit: int = 10,
) -> List[Dict]:
    """
    为整体投资组合生成洞察

    分析所有持仓的模式，生成组合级别的洞察和建议

    Args:
        positions: 所有持仓列表
        limit: 返回洞察数量限制

    Returns:
        List[Dict]: 组合级洞察列表
    """
    if not positions:
        return []

    insights = []

    # 1. 分析整体胜率趋势
    wins = [p for p in positions if p.get('net_pnl', 0) > 0]
    losses = [p for p in positions if p.get('net_pnl', 0) <= 0]
    win_rate = len(wins) / len(positions) * 100 if positions else 0

    # 2. 分析持亏vs持盈时间比
    avg_win_hold = sum(p.get('holding_period_days', 0) for p in wins) / len(wins) if wins else 0
    avg_loss_hold = sum(p.get('holding_period_days', 0) for p in losses) / len(losses) if losses else 0

    if avg_loss_hold > avg_win_hold * 2 and len(losses) > 3:
        insights.append({
            'category': 'behavior',
            'type': 'warning',
            'title': '持亏时间过长',
            'description': f'亏损持仓平均持有 {avg_loss_hold:.1f} 天，是盈利持仓 ({avg_win_hold:.1f} 天) 的 {avg_loss_hold/max(1,avg_win_hold):.1f} 倍',
            'suggestion': '及时止损，不要让亏损持仓占用过多时间和资金',
            'priority': 85,
            'pattern_stats': {
                'total_occurrences': len(losses),
                'win_rate': 0,
                'avg_pnl': sum(p.get('net_pnl', 0) for p in losses) / len(losses) if losses else 0,
                'total_pnl': sum(p.get('net_pnl', 0) for p in losses),
            },
            'root_cause': 'execution',
        })

    # 3. 分析频繁交易的标的
    symbol_counts = {}
    for p in positions:
        symbol = p.get('symbol', '')
        if symbol not in symbol_counts:
            symbol_counts[symbol] = {'count': 0, 'pnl': 0, 'wins': 0}
        symbol_counts[symbol]['count'] += 1
        symbol_counts[symbol]['pnl'] += p.get('net_pnl', 0)
        if p.get('net_pnl', 0) > 0:
            symbol_counts[symbol]['wins'] += 1

    for symbol, stats in symbol_counts.items():
        if stats['count'] >= 5 and stats['pnl'] < 0:
            symbol_win_rate = stats['wins'] / stats['count'] * 100
            if symbol_win_rate < 40:
                insights.append({
                    'category': 'pattern',
                    'type': 'warning',
                    'title': f'{symbol} 交易表现不佳',
                    'description': f'交易 {stats["count"]} 次，胜率 {symbol_win_rate:.1f}%，累计亏损 ${abs(stats["pnl"]):.0f}',
                    'suggestion': f'考虑减少或停止交易 {symbol}，或重新审视交易策略',
                    'priority': 80,
                    'pattern_stats': {
                        'total_occurrences': stats['count'],
                        'win_rate': symbol_win_rate,
                        'avg_pnl': stats['pnl'] / stats['count'],
                        'total_pnl': stats['pnl'],
                    },
                    'root_cause': 'direction',
                })

    # 4. 分析特定时段表现
    hour_stats = {}
    for p in positions:
        open_time = p.get('open_time', '')
        if open_time:
            try:
                hour = int(open_time.split(' ')[1].split(':')[0]) if ' ' in open_time else 0
                if hour not in hour_stats:
                    hour_stats[hour] = {'count': 0, 'pnl': 0, 'wins': 0}
                hour_stats[hour]['count'] += 1
                hour_stats[hour]['pnl'] += p.get('net_pnl', 0)
                if p.get('net_pnl', 0) > 0:
                    hour_stats[hour]['wins'] += 1
            except (IndexError, ValueError):
                pass

    for hour, stats in hour_stats.items():
        if stats['count'] >= 5 and stats['pnl'] < 0:
            hour_win_rate = stats['wins'] / stats['count'] * 100
            if hour_win_rate < 35:
                insights.append({
                    'category': 'behavior',
                    'type': 'warning',
                    'title': f'{hour}:00 时段表现不佳',
                    'description': f'该时段交易 {stats["count"]} 次，胜率 {hour_win_rate:.1f}%，累计亏损 ${abs(stats["pnl"]):.0f}',
                    'suggestion': f'考虑避免在 {hour}:00 左右开仓',
                    'priority': 70,
                    'pattern_stats': {
                        'total_occurrences': stats['count'],
                        'win_rate': hour_win_rate,
                        'avg_pnl': stats['pnl'] / stats['count'],
                        'total_pnl': stats['pnl'],
                    },
                    'root_cause': 'timing',
                })

    # 按优先级排序并限制数量
    insights.sort(key=lambda x: x.get('priority', 0), reverse=True)
    return insights[:limit]
