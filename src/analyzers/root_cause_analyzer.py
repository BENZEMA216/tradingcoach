"""
根因分析器

input: 持仓数据、市场数据、事件数据
output: 亏损/盈利归因分析、行为模式检测、改进建议
pos: 分析层 - 深度分析交易结果的根本原因

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RootCause(Enum):
    """根因类型"""
    TIMING = "timing"  # 时机问题：入场/出场时机不佳
    DIRECTION = "direction"  # 方向问题：做多/做空方向错误
    POSITION_SIZE = "position_size"  # 仓位问题：仓位过大/过小
    EXTERNAL_EVENT = "external_event"  # 外部事件：财报、宏观、地缘等
    EXECUTION = "execution"  # 执行问题：过早止盈、死扛亏损、追涨杀跌


class OutcomeType(Enum):
    """结果类型"""
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"


@dataclass
class Attribution:
    """归因结果"""
    root_cause: RootCause
    confidence: float  # 0-1
    contribution: float  # 该因素对结果的贡献度 0-100%
    evidence: Dict[str, Any]
    description: str


@dataclass
class BehaviorPattern:
    """行为模式"""
    pattern_name: str
    description: str
    severity: str  # low, medium, high, critical
    occurrences: int
    total_impact: float  # 累计影响（盈亏金额）
    suggestion: str
    examples: List[Dict]  # 典型案例


class RootCauseAnalyzer:
    """
    根因分析器

    分析交易结果的根本原因，提供归因分析和行为模式检测
    """

    def __init__(self):
        self.behavior_patterns: List[BehaviorPattern] = []

    def analyze_position(
        self,
        position: Dict[str, Any],
        entry_indicators: Optional[Dict] = None,
        exit_indicators: Optional[Dict] = None,
        events: Optional[List[Dict]] = None,
        market_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        分析单个持仓的根因

        Args:
            position: 持仓数据
            entry_indicators: 入场时技术指标
            exit_indicators: 出场时技术指标
            events: 持仓期间的事件列表
            market_context: 市场环境数据（大盘走势等）

        Returns:
            Dict containing:
            - outcome: win/loss/breakeven
            - attributions: List[Attribution] 归因列表
            - primary_cause: 主要根因
            - summary: 文字总结
        """
        net_pnl = position.get('net_pnl', 0)
        outcome = self._determine_outcome(net_pnl)

        attributions = []

        # 1. 分析时机因素
        timing_attr = self._analyze_timing(position, entry_indicators, exit_indicators)
        if timing_attr:
            attributions.append(timing_attr)

        # 2. 分析方向因素
        direction_attr = self._analyze_direction(position, entry_indicators, market_context)
        if direction_attr:
            attributions.append(direction_attr)

        # 3. 分析仓位因素
        position_size_attr = self._analyze_position_size(position)
        if position_size_attr:
            attributions.append(position_size_attr)

        # 4. 分析外部事件因素
        event_attr = self._analyze_external_events(position, events)
        if event_attr:
            attributions.append(event_attr)

        # 5. 分析执行因素
        execution_attr = self._analyze_execution(position)
        if execution_attr:
            attributions.append(execution_attr)

        # 归一化贡献度
        total_contribution = sum(a.contribution for a in attributions)
        if total_contribution > 0:
            for a in attributions:
                a.contribution = a.contribution / total_contribution * 100

        # 按贡献度排序
        attributions.sort(key=lambda x: x.contribution, reverse=True)

        # 确定主要根因
        primary_cause = attributions[0].root_cause if attributions else None

        # 生成总结
        summary = self._generate_summary(outcome, attributions, position)

        return {
            'outcome': outcome.value,
            'net_pnl': net_pnl,
            'attributions': [
                {
                    'root_cause': a.root_cause.value,
                    'confidence': a.confidence,
                    'contribution': a.contribution,
                    'evidence': a.evidence,
                    'description': a.description,
                }
                for a in attributions
            ],
            'primary_cause': primary_cause.value if primary_cause else None,
            'summary': summary,
        }

    def analyze_portfolio(
        self,
        positions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        分析整体投资组合的行为模式

        Args:
            positions: 所有持仓列表

        Returns:
            Dict containing:
            - patterns: List[BehaviorPattern] 检测到的行为模式
            - root_cause_distribution: 根因分布统计
            - recommendations: 改进建议列表
        """
        if not positions:
            return {
                'patterns': [],
                'root_cause_distribution': {},
                'recommendations': [],
            }

        patterns = []

        # 1. 检测持亏时间过长模式
        hold_loss_pattern = self._detect_hold_loss_pattern(positions)
        if hold_loss_pattern:
            patterns.append(hold_loss_pattern)

        # 2. 检测追涨杀跌模式
        chase_pattern = self._detect_chase_pattern(positions)
        if chase_pattern:
            patterns.append(chase_pattern)

        # 3. 检测过早止盈模式
        early_exit_pattern = self._detect_early_exit_pattern(positions)
        if early_exit_pattern:
            patterns.append(early_exit_pattern)

        # 4. 检测频繁交易模式
        overtrading_pattern = self._detect_overtrading_pattern(positions)
        if overtrading_pattern:
            patterns.append(overtrading_pattern)

        # 5. 检测逆势交易模式
        counter_trend_pattern = self._detect_counter_trend_pattern(positions)
        if counter_trend_pattern:
            patterns.append(counter_trend_pattern)

        # 6. 检测集中持仓模式
        concentration_pattern = self._detect_concentration_pattern(positions)
        if concentration_pattern:
            patterns.append(concentration_pattern)

        # 计算根因分布
        root_cause_distribution = self._calculate_root_cause_distribution(positions)

        # 生成改进建议
        recommendations = self._generate_recommendations(patterns, root_cause_distribution)

        return {
            'patterns': [
                {
                    'pattern_name': p.pattern_name,
                    'description': p.description,
                    'severity': p.severity,
                    'occurrences': p.occurrences,
                    'total_impact': p.total_impact,
                    'suggestion': p.suggestion,
                    'examples': p.examples[:3],  # 最多3个案例
                }
                for p in patterns
            ],
            'root_cause_distribution': root_cause_distribution,
            'recommendations': recommendations,
        }

    def _determine_outcome(self, net_pnl: float) -> OutcomeType:
        """判断交易结果"""
        if net_pnl > 0:
            return OutcomeType.WIN
        elif net_pnl < 0:
            return OutcomeType.LOSS
        return OutcomeType.BREAKEVEN

    def _analyze_timing(
        self,
        position: Dict,
        entry_indicators: Optional[Dict],
        exit_indicators: Optional[Dict],
    ) -> Optional[Attribution]:
        """分析时机因素"""
        entry_score = position.get('entry_quality_score', 50)
        exit_score = position.get('exit_quality_score', 50)
        net_pnl = position.get('net_pnl', 0)

        evidence = {
            'entry_score': entry_score,
            'exit_score': exit_score,
        }

        # 入场时机问题
        if entry_indicators:
            rsi = entry_indicators.get('rsi_14')
            if rsi:
                evidence['entry_rsi'] = rsi
                if position.get('direction') == 'long' and rsi > 70:
                    evidence['overbought_entry'] = True
                elif position.get('direction') == 'short' and rsi < 30:
                    evidence['oversold_entry'] = True

        # 计算时机因素的贡献度
        contribution = 0
        confidence = 0.5

        if entry_score < 50:
            contribution += (50 - entry_score) / 50 * 50  # 最多贡献50%
            confidence += 0.2

        if exit_score < 50:
            contribution += (50 - exit_score) / 50 * 30  # 最多贡献30%
            confidence += 0.15

        if 'overbought_entry' in evidence or 'oversold_entry' in evidence:
            contribution += 20
            confidence += 0.15

        if contribution == 0:
            return None

        description = self._generate_timing_description(evidence, net_pnl)

        return Attribution(
            root_cause=RootCause.TIMING,
            confidence=min(confidence, 1.0),
            contribution=contribution,
            evidence=evidence,
            description=description,
        )

    def _analyze_direction(
        self,
        position: Dict,
        entry_indicators: Optional[Dict],
        market_context: Optional[Dict],
    ) -> Optional[Attribution]:
        """分析方向因素"""
        direction = position.get('direction', 'long')
        net_pnl = position.get('net_pnl', 0)
        trend_score = position.get('trend_alignment_score', 50)

        evidence = {
            'direction': direction,
            'trend_score': trend_score,
        }

        # 检查趋势一致性
        if entry_indicators:
            sma_20 = entry_indicators.get('sma_20')
            sma_50 = entry_indicators.get('sma_50')
            close = entry_indicators.get('close')

            if sma_20 and sma_50 and close:
                if sma_20 > sma_50:
                    evidence['trend'] = 'up'
                else:
                    evidence['trend'] = 'down'

                # 逆势交易
                if evidence['trend'] == 'down' and direction == 'long':
                    evidence['counter_trend'] = True
                elif evidence['trend'] == 'up' and direction == 'short':
                    evidence['counter_trend'] = True

        contribution = 0
        confidence = 0.5

        # 趋势评分低说明方向可能有问题
        if trend_score < 50 and net_pnl < 0:
            contribution += (50 - trend_score) / 50 * 60
            confidence += 0.25

        if evidence.get('counter_trend'):
            contribution += 30
            confidence += 0.2

        if contribution == 0:
            return None

        description = self._generate_direction_description(evidence, net_pnl)

        return Attribution(
            root_cause=RootCause.DIRECTION,
            confidence=min(confidence, 1.0),
            contribution=contribution,
            evidence=evidence,
            description=description,
        )

    def _analyze_position_size(self, position: Dict) -> Optional[Attribution]:
        """分析仓位因素"""
        mae = position.get('mae', 0)
        net_pnl = position.get('net_pnl', 0)
        open_price = position.get('open_price', 0)
        quantity = position.get('quantity', 0)

        cost_basis = open_price * quantity if open_price and quantity else 0

        evidence = {
            'mae': mae,
            'cost_basis': cost_basis,
        }

        contribution = 0
        confidence = 0.4

        # MAE 过大说明仓位可能有问题
        if mae and mae < 0 and cost_basis > 0:
            mae_pct = abs(mae) / cost_basis * 100
            evidence['mae_pct'] = mae_pct

            if mae_pct > 20:
                contribution += 40
                confidence += 0.3
            elif mae_pct > 10:
                contribution += 20
                confidence += 0.15

        if contribution == 0:
            return None

        description = f'持仓期间最大浮亏 {evidence.get("mae_pct", 0):.1f}%，仓位风险较大'

        return Attribution(
            root_cause=RootCause.POSITION_SIZE,
            confidence=min(confidence, 1.0),
            contribution=contribution,
            evidence=evidence,
            description=description,
        )

    def _analyze_external_events(
        self,
        position: Dict,
        events: Optional[List[Dict]],
    ) -> Optional[Attribution]:
        """分析外部事件因素"""
        if not events:
            return None

        net_pnl = position.get('net_pnl', 0)

        # 查找高影响事件
        high_impact_events = [
            e for e in events
            if e.get('event_importance', 0) >= 7 or e.get('is_key_event')
        ]

        if not high_impact_events:
            return None

        evidence = {
            'events_count': len(high_impact_events),
            'events': [
                {
                    'type': e.get('event_type'),
                    'title': e.get('event_title', '')[:50],
                    'price_change': e.get('price_change_pct'),
                    'date': e.get('event_date'),
                }
                for e in high_impact_events[:3]
            ],
        }

        # 计算事件影响
        contribution = 0
        confidence = 0.5

        for event in high_impact_events:
            price_change = abs(event.get('price_change_pct', 0))
            if price_change > 5:
                contribution += 30
                confidence += 0.2
            elif price_change > 2:
                contribution += 15
                confidence += 0.1

        contribution = min(contribution, 70)  # 外部事件最多贡献70%

        if contribution == 0:
            return None

        event_types = [e.get('event_type', 'unknown') for e in high_impact_events]
        description = f'持仓期间经历 {len(high_impact_events)} 个重大事件（{", ".join(set(event_types))}），影响了交易结果'

        return Attribution(
            root_cause=RootCause.EXTERNAL_EVENT,
            confidence=min(confidence, 1.0),
            contribution=contribution,
            evidence=evidence,
            description=description,
        )

    def _analyze_execution(self, position: Dict) -> Optional[Attribution]:
        """分析执行因素"""
        mfe = position.get('mfe', 0)
        mae = position.get('mae', 0)
        net_pnl = position.get('net_pnl', 0)
        holding_days = position.get('holding_period_days', 0)

        evidence = {
            'mfe': mfe,
            'mae': mae,
            'holding_days': holding_days,
        }

        contribution = 0
        confidence = 0.5
        issues = []

        # 过早止盈
        if mfe and net_pnl > 0 and mfe > 0:
            capture_ratio = net_pnl / mfe
            evidence['capture_ratio'] = capture_ratio
            if capture_ratio < 0.3:
                contribution += 35
                confidence += 0.2
                issues.append('过早止盈')

        # 止损过晚
        if mae and net_pnl < 0 and mae < 0:
            loss_ratio = abs(net_pnl) / abs(mae) if mae != 0 else 0
            evidence['loss_ratio'] = loss_ratio
            if loss_ratio > 0.8:  # 亏损接近最大回撤
                contribution += 30
                confidence += 0.15
                issues.append('止损过晚')

        # 持仓时间异常
        if holding_days > 30 and net_pnl < 0:
            contribution += 20
            confidence += 0.1
            issues.append('长期持亏')
        elif holding_days < 1 and abs(net_pnl) > 100:
            contribution += 15
            confidence += 0.1
            issues.append('日内大额交易')

        if contribution == 0:
            return None

        description = '执行问题：' + '、'.join(issues) if issues else '执行纪律有待改进'

        return Attribution(
            root_cause=RootCause.EXECUTION,
            confidence=min(confidence, 1.0),
            contribution=contribution,
            evidence=evidence,
            description=description,
        )

    def _generate_timing_description(self, evidence: Dict, net_pnl: float) -> str:
        """生成时机因素描述"""
        parts = []

        if evidence.get('entry_score', 50) < 50:
            parts.append(f'入场质量评分 {evidence["entry_score"]:.0f}')

        if evidence.get('exit_score', 50) < 50:
            parts.append(f'出场质量评分 {evidence["exit_score"]:.0f}')

        if evidence.get('overbought_entry'):
            parts.append('在超买区域做多')

        if evidence.get('oversold_entry'):
            parts.append('在超卖区域做空')

        return '时机问题：' + '、'.join(parts) if parts else '入场/出场时机有待改进'

    def _generate_direction_description(self, evidence: Dict, net_pnl: float) -> str:
        """生成方向因素描述"""
        if evidence.get('counter_trend'):
            trend = '上涨' if evidence.get('trend') == 'up' else '下跌'
            direction = '做多' if evidence.get('direction') == 'long' else '做空'
            return f'逆势交易：市场趋势{trend}，但选择{direction}'

        if evidence.get('trend_score', 50) < 50:
            return f'交易方向与市场趋势不一致（趋势评分 {evidence["trend_score"]:.0f}）'

        return '方向选择有待改进'

    def _generate_summary(
        self,
        outcome: OutcomeType,
        attributions: List[Attribution],
        position: Dict,
    ) -> str:
        """生成归因总结"""
        symbol = position.get('symbol', '')
        net_pnl = position.get('net_pnl', 0)

        if not attributions:
            if outcome == OutcomeType.WIN:
                return f'{symbol} 交易盈利 ${net_pnl:.0f}，整体执行良好'
            elif outcome == OutcomeType.LOSS:
                return f'{symbol} 交易亏损 ${abs(net_pnl):.0f}，暂无法确定主要原因'
            return f'{symbol} 交易持平'

        primary = attributions[0]

        cause_names = {
            RootCause.TIMING: '时机',
            RootCause.DIRECTION: '方向',
            RootCause.POSITION_SIZE: '仓位',
            RootCause.EXTERNAL_EVENT: '外部事件',
            RootCause.EXECUTION: '执行',
        }

        if outcome == OutcomeType.WIN:
            return f'{symbol} 盈利 ${net_pnl:.0f}。主要归因：{cause_names.get(primary.root_cause, "其他")}（{primary.contribution:.0f}%）'
        elif outcome == OutcomeType.LOSS:
            summary = f'{symbol} 亏损 ${abs(net_pnl):.0f}。主要原因：{cause_names.get(primary.root_cause, "其他")}（{primary.contribution:.0f}%）。'
            summary += f'{primary.description}'
            return summary

        return f'{symbol} 交易持平'

    def _detect_hold_loss_pattern(self, positions: List[Dict]) -> Optional[BehaviorPattern]:
        """检测持亏时间过长模式"""
        wins = [p for p in positions if p.get('net_pnl', 0) > 0]
        losses = [p for p in positions if p.get('net_pnl', 0) < 0]

        if len(wins) < 3 or len(losses) < 3:
            return None

        avg_win_hold = sum(p.get('holding_period_days', 0) for p in wins) / len(wins)
        avg_loss_hold = sum(p.get('holding_period_days', 0) for p in losses) / len(losses)

        if avg_loss_hold <= avg_win_hold * 1.5:
            return None

        ratio = avg_loss_hold / max(avg_win_hold, 1)
        total_loss = sum(p.get('net_pnl', 0) for p in losses)

        # 按持仓时间排序，取最典型的案例
        loss_examples = sorted(losses, key=lambda p: p.get('holding_period_days', 0), reverse=True)[:5]

        severity = 'critical' if ratio > 3 else 'high' if ratio > 2 else 'medium'

        return BehaviorPattern(
            pattern_name='持亏时间过长',
            description=f'亏损持仓平均持有 {avg_loss_hold:.1f} 天，是盈利持仓 ({avg_win_hold:.1f} 天) 的 {ratio:.1f} 倍',
            severity=severity,
            occurrences=len(losses),
            total_impact=total_loss,
            suggestion='及时止损，设置明确的止损位，避免让亏损持仓占用过多时间和资金',
            examples=[
                {
                    'position_id': p.get('id'),
                    'symbol': p.get('symbol'),
                    'pnl': p.get('net_pnl'),
                    'holding_days': p.get('holding_period_days'),
                }
                for p in loss_examples
            ],
        )

    def _detect_chase_pattern(self, positions: List[Dict]) -> Optional[BehaviorPattern]:
        """检测追涨杀跌模式"""
        chase_positions = []

        for p in positions:
            entry_rsi = p.get('entry_rsi_14')
            direction = p.get('direction')
            net_pnl = p.get('net_pnl', 0)

            if entry_rsi is None:
                continue

            # 追涨：RSI > 70 做多
            # 杀跌：RSI < 30 做空
            if (direction == 'long' and entry_rsi > 70) or (direction == 'short' and entry_rsi < 30):
                chase_positions.append(p)

        if len(chase_positions) < 3:
            return None

        total_pnl = sum(p.get('net_pnl', 0) for p in chase_positions)
        win_rate = len([p for p in chase_positions if p.get('net_pnl', 0) > 0]) / len(chase_positions) * 100

        if win_rate >= 50:  # 如果胜率还行，不算严重问题
            return None

        severity = 'high' if total_pnl < -500 else 'medium'

        return BehaviorPattern(
            pattern_name='追涨杀跌',
            description=f'在 RSI 极端区域追涨杀跌 {len(chase_positions)} 次，胜率仅 {win_rate:.1f}%',
            severity=severity,
            occurrences=len(chase_positions),
            total_impact=total_pnl,
            suggestion='避免在 RSI > 70 时做多或 RSI < 30 时做空，等待回调/反弹再入场',
            examples=[
                {
                    'position_id': p.get('id'),
                    'symbol': p.get('symbol'),
                    'pnl': p.get('net_pnl'),
                    'entry_rsi': p.get('entry_rsi_14'),
                    'direction': p.get('direction'),
                }
                for p in chase_positions[:5]
            ],
        )

    def _detect_early_exit_pattern(self, positions: List[Dict]) -> Optional[BehaviorPattern]:
        """检测过早止盈模式"""
        early_exits = []
        total_missed = 0

        for p in positions:
            mfe = p.get('mfe', 0)
            net_pnl = p.get('net_pnl', 0)

            if mfe and mfe > 0 and net_pnl > 0:
                capture_ratio = net_pnl / mfe
                if capture_ratio < 0.3:
                    missed = mfe - net_pnl
                    total_missed += missed
                    early_exits.append({
                        'position': p,
                        'capture_ratio': capture_ratio,
                        'missed_profit': missed,
                    })

        if len(early_exits) < 3:
            return None

        avg_capture = sum(e['capture_ratio'] for e in early_exits) / len(early_exits)

        severity = 'high' if total_missed > 1000 else 'medium'

        return BehaviorPattern(
            pattern_name='过早止盈',
            description=f'{len(early_exits)} 次盈利交易过早出场，平均只捕获 {avg_capture*100:.1f}% 的潜在利润',
            severity=severity,
            occurrences=len(early_exits),
            total_impact=-total_missed,  # 错失的利润为负影响
            suggestion='使用移动止盈或分批出场策略，让利润奔跑',
            examples=[
                {
                    'position_id': e['position'].get('id'),
                    'symbol': e['position'].get('symbol'),
                    'pnl': e['position'].get('net_pnl'),
                    'mfe': e['position'].get('mfe'),
                    'capture_ratio': f'{e["capture_ratio"]*100:.1f}%',
                    'missed_profit': e['missed_profit'],
                }
                for e in sorted(early_exits, key=lambda x: x['missed_profit'], reverse=True)[:5]
            ],
        )

    def _detect_overtrading_pattern(self, positions: List[Dict]) -> Optional[BehaviorPattern]:
        """检测频繁交易模式"""
        if len(positions) < 10:
            return None

        # 按日期分组
        daily_trades = {}
        for p in positions:
            date = p.get('open_time', '')[:10]
            if date:
                if date not in daily_trades:
                    daily_trades[date] = []
                daily_trades[date].append(p)

        # 找出交易过多的日子
        heavy_days = [(date, trades) for date, trades in daily_trades.items() if len(trades) >= 5]

        if len(heavy_days) < 2:
            return None

        # 分析这些日子的盈亏
        heavy_day_positions = []
        for date, trades in heavy_days:
            heavy_day_positions.extend(trades)

        total_pnl = sum(p.get('net_pnl', 0) for p in heavy_day_positions)
        win_rate = len([p for p in heavy_day_positions if p.get('net_pnl', 0) > 0]) / len(heavy_day_positions) * 100

        if total_pnl >= 0 and win_rate >= 50:  # 如果盈利且胜率还行，不算问题
            return None

        severity = 'high' if total_pnl < -500 else 'medium'

        return BehaviorPattern(
            pattern_name='频繁交易',
            description=f'{len(heavy_days)} 天日内交易超过5次，这些日子累计盈亏 ${total_pnl:.0f}',
            severity=severity,
            occurrences=len(heavy_day_positions),
            total_impact=total_pnl,
            suggestion='减少交易频率，专注高质量交易机会',
            examples=[
                {
                    'date': date,
                    'trade_count': len(trades),
                    'day_pnl': sum(p.get('net_pnl', 0) for p in trades),
                }
                for date, trades in sorted(heavy_days, key=lambda x: sum(p.get('net_pnl', 0) for p in x[1]))[:5]
            ],
        )

    def _detect_counter_trend_pattern(self, positions: List[Dict]) -> Optional[BehaviorPattern]:
        """检测逆势交易模式"""
        counter_trend_positions = []

        for p in positions:
            trend_score = p.get('trend_alignment_score', 50)
            net_pnl = p.get('net_pnl', 0)

            if trend_score is not None and trend_score < 40:
                counter_trend_positions.append(p)

        if len(counter_trend_positions) < 3:
            return None

        total_pnl = sum(p.get('net_pnl', 0) for p in counter_trend_positions)
        win_rate = len([p for p in counter_trend_positions if p.get('net_pnl', 0) > 0]) / len(counter_trend_positions) * 100

        if win_rate >= 45:  # 逆势交易也可能盈利
            return None

        severity = 'high' if total_pnl < -500 else 'medium'

        return BehaviorPattern(
            pattern_name='逆势交易',
            description=f'{len(counter_trend_positions)} 次逆势交易，胜率 {win_rate:.1f}%',
            severity=severity,
            occurrences=len(counter_trend_positions),
            total_impact=total_pnl,
            suggestion='顺势交易，等待趋势确认再入场',
            examples=[
                {
                    'position_id': p.get('id'),
                    'symbol': p.get('symbol'),
                    'pnl': p.get('net_pnl'),
                    'trend_score': p.get('trend_alignment_score'),
                    'direction': p.get('direction'),
                }
                for p in sorted(counter_trend_positions, key=lambda x: x.get('net_pnl', 0))[:5]
            ],
        )

    def _detect_concentration_pattern(self, positions: List[Dict]) -> Optional[BehaviorPattern]:
        """检测集中持仓模式"""
        symbol_stats = {}

        for p in positions:
            symbol = p.get('symbol', '')
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {'count': 0, 'pnl': 0}
            symbol_stats[symbol]['count'] += 1
            symbol_stats[symbol]['pnl'] += p.get('net_pnl', 0)

        # 找出交易次数过多且亏损的标的
        problem_symbols = [
            (symbol, stats) for symbol, stats in symbol_stats.items()
            if stats['count'] >= 5 and stats['pnl'] < 0
        ]

        if not problem_symbols:
            return None

        total_loss = sum(stats['pnl'] for _, stats in problem_symbols)

        severity = 'high' if total_loss < -1000 else 'medium'

        return BehaviorPattern(
            pattern_name='集中持仓亏损',
            description=f'{len(problem_symbols)} 个标的频繁交易且亏损',
            severity=severity,
            occurrences=sum(stats['count'] for _, stats in problem_symbols),
            total_impact=total_loss,
            suggestion='减少对亏损标的的交易，或重新审视交易策略',
            examples=[
                {
                    'symbol': symbol,
                    'trade_count': stats['count'],
                    'total_pnl': stats['pnl'],
                }
                for symbol, stats in sorted(problem_symbols, key=lambda x: x[1]['pnl'])[:5]
            ],
        )

    def _calculate_root_cause_distribution(self, positions: List[Dict]) -> Dict[str, Any]:
        """计算根因分布"""
        # 简化版：基于已有字段统计
        distribution = {
            'timing': 0,
            'direction': 0,
            'position_size': 0,
            'execution': 0,
        }

        losses = [p for p in positions if p.get('net_pnl', 0) < 0]

        for p in losses:
            entry_score = p.get('entry_quality_score', 50)
            exit_score = p.get('exit_quality_score', 50)
            trend_score = p.get('trend_alignment_score', 50)
            mae = p.get('mae', 0)
            mfe = p.get('mfe', 0)
            net_pnl = p.get('net_pnl', 0)
            open_price = p.get('open_price', 0)
            quantity = p.get('quantity', 0)

            # 时机问题
            if entry_score < 50 or exit_score < 50:
                distribution['timing'] += 1

            # 方向问题
            if trend_score < 50:
                distribution['direction'] += 1

            # 仓位问题
            cost_basis = open_price * quantity if open_price and quantity else 0
            if mae and mae < 0 and cost_basis > 0:
                mae_pct = abs(mae) / cost_basis * 100
                if mae_pct > 15:
                    distribution['position_size'] += 1

            # 执行问题
            holding_days = p.get('holding_period_days', 0)
            if holding_days > 20:
                distribution['execution'] += 1

        return distribution

    def _generate_recommendations(
        self,
        patterns: List[BehaviorPattern],
        distribution: Dict[str, int],
    ) -> List[Dict[str, str]]:
        """生成改进建议"""
        recommendations = []

        # 基于检测到的模式
        for pattern in patterns:
            if pattern.severity in ['high', 'critical']:
                recommendations.append({
                    'title': f'解决{pattern.pattern_name}问题',
                    'description': pattern.suggestion,
                    'priority': 'high' if pattern.severity == 'critical' else 'medium',
                    'expected_impact': f'可能减少 ${abs(pattern.total_impact):.0f} 损失' if pattern.total_impact < 0 else f'可能增加 ${pattern.total_impact:.0f} 盈利',
                })

        # 基于根因分布
        if distribution.get('timing', 0) > 5:
            recommendations.append({
                'title': '改进入场/出场时机',
                'description': '使用技术指标确认入场信号，设置明确的止盈止损位',
                'priority': 'high',
                'expected_impact': '提高交易胜率',
            })

        if distribution.get('direction', 0) > 5:
            recommendations.append({
                'title': '顺势交易',
                'description': '在做交易决策前先确认大趋势方向，避免逆势操作',
                'priority': 'medium',
                'expected_impact': '减少逆势亏损',
            })

        if distribution.get('position_size', 0) > 3:
            recommendations.append({
                'title': '控制仓位规模',
                'description': '单笔交易不超过账户的5-10%，设置最大亏损限额',
                'priority': 'high',
                'expected_impact': '降低单笔交易风险',
            })

        if distribution.get('execution', 0) > 5:
            recommendations.append({
                'title': '改进执行纪律',
                'description': '严格执行交易计划，避免情绪化交易',
                'priority': 'medium',
                'expected_impact': '提高交易质量',
            })

        return recommendations


# 便捷函数
def analyze_position_root_cause(
    position: Dict[str, Any],
    entry_indicators: Optional[Dict] = None,
    exit_indicators: Optional[Dict] = None,
    events: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """分析单个持仓的根因"""
    analyzer = RootCauseAnalyzer()
    return analyzer.analyze_position(
        position,
        entry_indicators,
        exit_indicators,
        events,
    )


def analyze_portfolio_patterns(
    positions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """分析投资组合的行为模式"""
    analyzer = RootCauseAnalyzer()
    return analyzer.analyze_portfolio(positions)
