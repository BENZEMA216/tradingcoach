"""
OptionTradeReport - 期权交易复盘报告生成器

生成期权交易的综合复盘报告，包括：
1. 汇总统计（按 Call/Put、ITM/ATM/OTM、持有天数分组）
2. 最佳/最差交易分析
3. 单个持仓详情分析
4. 策略改进建议
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
from collections import defaultdict
import statistics

from sqlalchemy.orm import Session

from src.models.position import Position, PositionStatus
from src.utils.option_parser import OptionParser
from src.analyzers.option_analyzer import OptionTradeAnalyzer

logger = logging.getLogger(__name__)


class OptionTradeReport:
    """
    期权交易复盘报告生成器

    功能：
    1. 生成汇总统计报告
    2. 生成单个持仓详情报告
    3. 生成策略改进建议
    4. 导出报告（JSON/HTML格式）
    """

    def __init__(self, session: Session):
        """
        初始化报告生成器

        Args:
            session: Database session
        """
        self.session = session
        self.analyzer = OptionTradeAnalyzer()
        logger.info("OptionTradeReport initialized")

    def generate_summary(
        self,
        option_positions: List[Position] = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """
        生成期权交易汇总统计报告

        Args:
            option_positions: 期权持仓列表（可选，不提供则自动查询）
            start_date: 开始日期过滤
            end_date: 结束日期过滤

        Returns:
            dict: 汇总统计报告
        """
        # 获取期权持仓
        if option_positions is None:
            option_positions = self._get_option_positions(start_date, end_date)

        if not option_positions:
            return {
                'total_positions': 0,
                'message': 'No option positions found'
            }

        # 基础统计
        basic_stats = self._calculate_basic_stats(option_positions)

        # 按 Call/Put 分类统计
        call_put_stats = self._calculate_call_put_stats(option_positions)

        # 按 Moneyness 分类统计
        moneyness_stats = self._calculate_moneyness_stats(option_positions)

        # 按持有天数分组统计
        holding_stats = self._calculate_holding_period_stats(option_positions)

        # 按 DTE 分组统计
        dte_stats = self._calculate_dte_stats(option_positions)

        # 最佳/最差交易
        best_worst = self._find_best_worst_trades(option_positions)

        # 评分分布
        score_distribution = self._calculate_score_distribution(option_positions)

        return {
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'basic_stats': basic_stats,
            'call_put_stats': call_put_stats,
            'moneyness_stats': moneyness_stats,
            'holding_period_stats': holding_stats,
            'dte_stats': dte_stats,
            'best_worst_trades': best_worst,
            'score_distribution': score_distribution
        }

    def _get_option_positions(
        self,
        start_date: date = None,
        end_date: date = None
    ) -> List[Position]:
        """获取期权持仓"""
        query = self.session.query(Position).filter(
            Position.is_option == 1,
            Position.status == PositionStatus.CLOSED
        )

        if start_date:
            query = query.filter(Position.open_date >= start_date)
        if end_date:
            query = query.filter(Position.close_date <= end_date)

        return query.all()

    def _calculate_basic_stats(self, positions: List[Position]) -> Dict:
        """计算基础统计"""
        total = len(positions)
        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        losers = [p for p in positions if p.net_pnl and float(p.net_pnl) < 0]

        total_pnl = sum(float(p.net_pnl or 0) for p in positions)
        total_profit = sum(float(p.net_pnl) for p in winners)
        total_loss = sum(float(p.net_pnl) for p in losers)

        avg_pnl = total_pnl / total if total > 0 else 0
        avg_win = total_profit / len(winners) if winners else 0
        avg_loss = total_loss / len(losers) if losers else 0

        win_rate = len(winners) / total * 100 if total > 0 else 0

        # 盈亏比
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')

        # 期望值 = 胜率 * 平均盈利 - 败率 * 平均亏损
        expectancy = (win_rate / 100) * avg_win + ((100 - win_rate) / 100) * avg_loss

        return {
            'total_positions': total,
            'winners': len(winners),
            'losers': len(losers),
            'breakeven': total - len(winners) - len(losers),
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'avg_pnl': round(avg_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else None,
            'expectancy': round(expectancy, 2)
        }

    def _calculate_call_put_stats(self, positions: List[Position]) -> Dict:
        """按 Call/Put 分类统计"""
        calls = []
        puts = []

        for p in positions:
            option_info = OptionParser.parse(p.symbol)
            if option_info:
                if option_info.get('type', '').lower() == 'call':
                    calls.append(p)
                else:
                    puts.append(p)

        return {
            'call': self._calculate_group_stats(calls, 'Call'),
            'put': self._calculate_group_stats(puts, 'Put')
        }

    def _calculate_moneyness_stats(self, positions: List[Position]) -> Dict:
        """
        按入场时 Moneyness 分类统计

        分类：
        - ITM (In The Money): > 5%
        - ATM (At The Money): -5% ~ 5%
        - OTM (Out of The Money): < -5%
        - Deep OTM: < -15%
        """
        itm = []
        atm = []
        otm = []
        deep_otm = []

        for p in positions:
            moneyness = float(p.entry_moneyness) if p.entry_moneyness else None
            if moneyness is None:
                continue

            if moneyness > 5:
                itm.append(p)
            elif moneyness >= -5:
                atm.append(p)
            elif moneyness >= -15:
                otm.append(p)
            else:
                deep_otm.append(p)

        return {
            'itm': self._calculate_group_stats(itm, 'ITM (>5%)'),
            'atm': self._calculate_group_stats(atm, 'ATM (-5% ~ 5%)'),
            'otm': self._calculate_group_stats(otm, 'OTM (-15% ~ -5%)'),
            'deep_otm': self._calculate_group_stats(deep_otm, 'Deep OTM (<-15%)')
        }

    def _calculate_holding_period_stats(self, positions: List[Position]) -> Dict:
        """按持有天数分组统计"""
        intraday = []  # < 1天
        short_term = []  # 1-3天
        medium_term = []  # 4-7天
        long_term = []  # > 7天

        for p in positions:
            days = p.holding_period_days or 0
            if days < 1:
                intraday.append(p)
            elif days <= 3:
                short_term.append(p)
            elif days <= 7:
                medium_term.append(p)
            else:
                long_term.append(p)

        return {
            'intraday': self._calculate_group_stats(intraday, 'Intraday (<1d)'),
            'short_term': self._calculate_group_stats(short_term, 'Short (1-3d)'),
            'medium_term': self._calculate_group_stats(medium_term, 'Medium (4-7d)'),
            'long_term': self._calculate_group_stats(long_term, 'Long (>7d)')
        }

    def _calculate_dte_stats(self, positions: List[Position]) -> Dict:
        """按入场时 DTE 分组统计"""
        weekly = []  # < 7天
        short_dte = []  # 7-21天
        medium_dte = []  # 21-45天
        long_dte = []  # > 45天

        for p in positions:
            dte = p.entry_dte
            if dte is None:
                continue

            if dte < 7:
                weekly.append(p)
            elif dte <= 21:
                short_dte.append(p)
            elif dte <= 45:
                medium_dte.append(p)
            else:
                long_dte.append(p)

        return {
            'weekly': self._calculate_group_stats(weekly, 'Weekly (<7d)'),
            'short_dte': self._calculate_group_stats(short_dte, 'Short DTE (7-21d)'),
            'medium_dte': self._calculate_group_stats(medium_dte, 'Medium DTE (21-45d)'),
            'long_dte': self._calculate_group_stats(long_dte, 'Long DTE (>45d)')
        }

    def _calculate_group_stats(self, positions: List[Position], group_name: str) -> Dict:
        """计算分组统计"""
        if not positions:
            return {
                'name': group_name,
                'count': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'total_pnl': 0
            }

        total = len(positions)
        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        total_pnl = sum(float(p.net_pnl or 0) for p in positions)
        avg_pnl = total_pnl / total
        win_rate = len(winners) / total * 100

        # 计算平均盈亏百分比
        pnl_pcts = [float(p.net_pnl_pct) for p in positions if p.net_pnl_pct]
        avg_pnl_pct = statistics.mean(pnl_pcts) if pnl_pcts else 0

        return {
            'name': group_name,
            'count': total,
            'win_rate': round(win_rate, 2),
            'avg_pnl': round(avg_pnl, 2),
            'avg_pnl_pct': round(avg_pnl_pct, 2),
            'total_pnl': round(total_pnl, 2)
        }

    def _find_best_worst_trades(self, positions: List[Position], top_n: int = 5) -> Dict:
        """找出最佳和最差交易"""
        sorted_by_pnl = sorted(
            positions,
            key=lambda p: float(p.net_pnl or 0),
            reverse=True
        )

        best = sorted_by_pnl[:top_n]
        worst = sorted_by_pnl[-top_n:]

        return {
            'best': [self._position_to_summary(p) for p in best],
            'worst': [self._position_to_summary(p) for p in reversed(worst)]
        }

    def _position_to_summary(self, position: Position) -> Dict:
        """将持仓转换为摘要"""
        option_info = OptionParser.parse(position.symbol) or {}

        return {
            'id': position.id,
            'symbol': position.symbol,
            'underlying': option_info.get('underlying'),
            'option_type': option_info.get('type'),
            'strike': option_info.get('strike'),
            'expiry': option_info.get('expiry').isoformat() if option_info.get('expiry') else None,
            'direction': position.direction,
            'open_date': position.open_date.isoformat() if position.open_date else None,
            'close_date': position.close_date.isoformat() if position.close_date else None,
            'holding_days': position.holding_period_days,
            'net_pnl': float(position.net_pnl) if position.net_pnl else None,
            'net_pnl_pct': float(position.net_pnl_pct) if position.net_pnl_pct else None,
            'entry_moneyness': float(position.entry_moneyness) if position.entry_moneyness else None,
            'entry_dte': position.entry_dte,
            'exit_dte': position.exit_dte,
            'overall_score': float(position.overall_score) if position.overall_score else None,
            'score_grade': position.score_grade
        }

    def _calculate_score_distribution(self, positions: List[Position]) -> Dict:
        """计算评分分布"""
        grades = defaultdict(int)
        scores = []

        for p in positions:
            if p.score_grade:
                grades[p.score_grade] += 1
            if p.overall_score:
                scores.append(float(p.overall_score))

        avg_score = statistics.mean(scores) if scores else 0
        median_score = statistics.median(scores) if scores else 0

        return {
            'grade_distribution': dict(grades),
            'avg_score': round(avg_score, 2),
            'median_score': round(median_score, 2),
            'min_score': round(min(scores), 2) if scores else None,
            'max_score': round(max(scores), 2) if scores else None
        }

    def generate_position_detail(self, position: Position) -> Dict[str, Any]:
        """
        生成单个持仓的详细分析报告

        Args:
            position: Position对象

        Returns:
            dict: 详细分析报告
        """
        # 解析期权信息
        option_info = OptionParser.parse(position.symbol)
        if not option_info:
            return {'error': f'Failed to parse option symbol: {position.symbol}'}

        # 使用分析器进行分析
        analysis = self.analyzer.analyze_position(position)

        # 基本信息
        basic_info = {
            'position_id': position.id,
            'symbol': position.symbol,
            'underlying': option_info.get('underlying'),
            'option_type': option_info.get('type'),
            'strike': option_info.get('strike'),
            'expiry': option_info.get('expiry').isoformat() if option_info.get('expiry') else None,
            'direction': position.direction,
            'quantity': position.quantity,
            'open_time': position.open_time.isoformat() if position.open_time else None,
            'close_time': position.close_time.isoformat() if position.close_time else None,
            'open_price': float(position.open_price) if position.open_price else None,
            'close_price': float(position.close_price) if position.close_price else None
        }

        # 盈亏分析
        pnl_analysis = {
            'net_pnl': float(position.net_pnl) if position.net_pnl else None,
            'net_pnl_pct': float(position.net_pnl_pct) if position.net_pnl_pct else None,
            'mae': float(position.mae) if position.mae else None,
            'mae_pct': float(position.mae_pct) if position.mae_pct else None,
            'mfe': float(position.mfe) if position.mfe else None,
            'mfe_pct': float(position.mfe_pct) if position.mfe_pct else None
        }

        # 期权特有指标
        option_metrics = {
            'entry_moneyness': float(position.entry_moneyness) if position.entry_moneyness else None,
            'entry_dte': position.entry_dte,
            'exit_dte': position.exit_dte,
            'holding_days': position.holding_period_days
        }

        # 评分
        scores = {
            'overall_score': float(position.overall_score) if position.overall_score else None,
            'score_grade': position.score_grade,
            'entry_quality_score': float(position.entry_quality_score) if position.entry_quality_score else None,
            'exit_quality_score': float(position.exit_quality_score) if position.exit_quality_score else None,
            'trend_quality_score': float(position.trend_quality_score) if position.trend_quality_score else None,
            'risk_mgmt_score': float(position.risk_mgmt_score) if position.risk_mgmt_score else None,
            'option_entry_score': float(position.option_entry_score) if position.option_entry_score else None,
            'option_exit_score': float(position.option_exit_score) if position.option_exit_score else None,
            'option_strategy_score': float(position.option_strategy_score) if position.option_strategy_score else None
        }

        # 生成改进建议
        suggestions = self._generate_suggestions(position, analysis)

        return {
            'generated_at': datetime.now().isoformat(),
            'basic_info': basic_info,
            'pnl_analysis': pnl_analysis,
            'option_metrics': option_metrics,
            'scores': scores,
            'analysis': analysis,
            'suggestions': suggestions
        }

    def _generate_suggestions(
        self,
        position: Position,
        analysis: Dict
    ) -> List[str]:
        """
        根据分析结果生成改进建议

        Args:
            position: Position对象
            analysis: 分析结果

        Returns:
            list: 建议列表
        """
        suggestions = []

        # 基于盈亏的建议
        if position.net_pnl and float(position.net_pnl) < 0:
            pnl_pct = float(position.net_pnl_pct or 0)
            if pnl_pct < -50:
                suggestions.append(
                    "严重亏损：考虑设置更严格的止损点（如-30%），"
                    "避免期权归零风险"
                )
            elif pnl_pct < -30:
                suggestions.append(
                    "亏损较大：建议在-20%~-30%区间设置止损，"
                    "保护剩余本金"
                )

        # 基于入场 Moneyness 的建议
        entry_context = analysis.get('entry_context', {})
        moneyness_info = entry_context.get('moneyness', {})
        moneyness_pct = moneyness_info.get('percentage')

        if moneyness_pct is not None:
            if abs(moneyness_pct) > 20:
                suggestions.append(
                    f"行权价选择激进（Moneyness: {moneyness_pct:.1f}%）："
                    "考虑选择更接近ATM的行权价，平衡风险收益"
                )

        # 基于 DTE 的建议
        entry_dte = position.entry_dte
        exit_dte = position.exit_dte

        if entry_dte is not None:
            if entry_dte < 7:
                suggestions.append(
                    "DTE过短（<7天）：周期权时间价值损耗极快，"
                    "需要快速方向验证或考虑更长期期权"
                )
            elif exit_dte is not None and exit_dte < 3:
                suggestions.append(
                    "持有到临近到期：避免在DTE<3时仍持有期权，"
                    "时间价值在最后几天加速衰减"
                )

        # 基于持有时间的建议
        holding_days = position.holding_period_days
        if holding_days and entry_dte:
            hold_ratio = holding_days / entry_dte if entry_dte > 0 else 0
            if hold_ratio > 0.7:
                suggestions.append(
                    f"持有时间过长（占DTE的{hold_ratio:.0%}）："
                    "建议在持有时间达到DTE的一半前评估出场"
                )

        # 基于趋势一致性的建议
        trend_info = entry_context.get('trend_alignment', {})
        if not trend_info.get('aligned', True):
            option_type = analysis.get('option_info', {}).get('type', '')
            trend_dir = trend_info.get('trend_direction', '')
            suggestions.append(
                f"趋势不一致：买入{option_type}但正股趋势为{trend_dir}，"
                "考虑顺势交易或使用价差策略降低风险"
            )

        # 基于评分的建议
        if position.overall_score and float(position.overall_score) < 50:
            suggestions.append(
                "整体评分较低：建议复盘入场时机、行权价选择、"
                "和出场策略，找出主要失分点"
            )

        # 如果没有建议，给出正面反馈
        if not suggestions:
            if position.net_pnl and float(position.net_pnl) > 0:
                suggestions.append(
                    "交易执行良好！继续保持当前的交易纪律和策略"
                )
            else:
                suggestions.append(
                    "交易符合基本原则，继续积累经验"
                )

        return suggestions

    def generate_strategy_insights(
        self,
        option_positions: List[Position] = None
    ) -> Dict[str, Any]:
        """
        生成策略洞察和改进建议

        Args:
            option_positions: 期权持仓列表

        Returns:
            dict: 策略洞察报告
        """
        if option_positions is None:
            option_positions = self._get_option_positions()

        if not option_positions:
            return {'message': 'No option positions found'}

        # 分析胜率最高的策略组合
        best_strategies = self._analyze_winning_strategies(option_positions)

        # 分析亏损模式
        loss_patterns = self._analyze_loss_patterns(option_positions)

        # 时间分析
        time_analysis = self._analyze_optimal_timing(option_positions)

        # 最佳参数建议
        optimal_params = self._suggest_optimal_parameters(option_positions)

        return {
            'generated_at': datetime.now().isoformat(),
            'total_positions_analyzed': len(option_positions),
            'best_strategies': best_strategies,
            'loss_patterns': loss_patterns,
            'time_analysis': time_analysis,
            'optimal_parameters': optimal_params
        }

    def _analyze_winning_strategies(self, positions: List[Position]) -> Dict:
        """分析胜率最高的策略组合"""
        # 按 Call/Put + Moneyness 组合分析
        combos = defaultdict(list)

        for p in positions:
            option_info = OptionParser.parse(p.symbol)
            if not option_info:
                continue

            opt_type = option_info.get('type', '').lower()
            moneyness = float(p.entry_moneyness) if p.entry_moneyness else 0

            if moneyness > 5:
                money_cat = 'ITM'
            elif moneyness >= -5:
                money_cat = 'ATM'
            else:
                money_cat = 'OTM'

            combo_key = f"{opt_type.upper()}_{money_cat}"
            combos[combo_key].append(p)

        # 计算每个组合的统计
        combo_stats = {}
        for combo, combo_positions in combos.items():
            stats = self._calculate_group_stats(combo_positions, combo)
            combo_stats[combo] = stats

        # 按胜率排序
        sorted_combos = sorted(
            combo_stats.items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )

        return {
            'by_win_rate': [
                {'combo': k, **v}
                for k, v in sorted_combos
            ],
            'recommendation': sorted_combos[0][0] if sorted_combos else None
        }

    def _analyze_loss_patterns(self, positions: List[Position]) -> Dict:
        """分析亏损模式"""
        losers = [p for p in positions if p.net_pnl and float(p.net_pnl) < 0]

        if not losers:
            return {'message': 'No losing trades found'}

        patterns = {
            'wrong_direction': 0,
            'bad_timing': 0,
            'aggressive_strike': 0,
            'held_too_long': 0
        }

        for p in losers:
            # 分析亏损原因
            if p.entry_dte and p.exit_dte is not None:
                hold_ratio = (p.entry_dte - p.exit_dte) / p.entry_dte if p.entry_dte > 0 else 0
                if hold_ratio > 0.7:
                    patterns['held_too_long'] += 1

            if p.entry_moneyness and abs(float(p.entry_moneyness)) > 15:
                patterns['aggressive_strike'] += 1

        return {
            'total_losses': len(losers),
            'patterns': patterns,
            'avg_loss': round(
                sum(float(p.net_pnl) for p in losers) / len(losers),
                2
            )
        }

    def _analyze_optimal_timing(self, positions: List[Position]) -> Dict:
        """分析最佳交易时机"""
        # 按星期几分析
        weekday_stats = defaultdict(list)

        for p in positions:
            if p.open_date:
                weekday = p.open_date.strftime('%A')
                weekday_stats[weekday].append(p)

        weekday_performance = {}
        for day, day_positions in weekday_stats.items():
            stats = self._calculate_group_stats(day_positions, day)
            weekday_performance[day] = stats

        # 找出最佳交易日
        best_day = max(
            weekday_performance.items(),
            key=lambda x: x[1]['win_rate']
        ) if weekday_performance else (None, {})

        return {
            'by_weekday': weekday_performance,
            'best_day': best_day[0],
            'best_day_win_rate': best_day[1].get('win_rate', 0)
        }

    def _suggest_optimal_parameters(self, positions: List[Position]) -> Dict:
        """建议最优参数"""
        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]

        if not winners:
            return {'message': 'Not enough winning trades for analysis'}

        # 分析盈利交易的参数分布
        dte_values = [p.entry_dte for p in winners if p.entry_dte]
        moneyness_values = [
            float(p.entry_moneyness) for p in winners
            if p.entry_moneyness is not None
        ]
        holding_days_values = [
            p.holding_period_days for p in winners
            if p.holding_period_days
        ]

        return {
            'optimal_dte': {
                'avg': round(statistics.mean(dte_values), 0) if dte_values else None,
                'median': round(statistics.median(dte_values), 0) if dte_values else None,
                'range': f"{min(dte_values)}-{max(dte_values)}" if dte_values else None
            },
            'optimal_moneyness': {
                'avg': round(statistics.mean(moneyness_values), 2) if moneyness_values else None,
                'median': round(statistics.median(moneyness_values), 2) if moneyness_values else None
            },
            'optimal_holding_days': {
                'avg': round(statistics.mean(holding_days_values), 1) if holding_days_values else None,
                'median': round(statistics.median(holding_days_values), 0) if holding_days_values else None
            }
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"OptionTradeReport(session={self.session})"
