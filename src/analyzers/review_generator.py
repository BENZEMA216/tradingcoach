"""
ReviewGenerator - 复盘报告生成器

基于规则引擎自动生成交易复盘报告
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.models.position import Position
from src.models.market_data import MarketData
from src.analyzers.strategy_classifier import StrategyClassifier
from config import (
    RSI_OVERSOLD, RSI_OVERBOUGHT,
    STOCH_OVERSOLD, STOCH_OVERBOUGHT,
    ADX_WEAK_TREND, ADX_MODERATE_TREND, ADX_STRONG_TREND
)

logger = logging.getLogger(__name__)


@dataclass
class ReviewReport:
    """复盘报告数据类"""
    entry_reason: str  # 入场理由
    exit_evaluation: str  # 离场评价
    positives: List[str]  # 做对的事情
    negatives: List[str]  # 做错的事情
    suggestions: List[str]  # 改进建议
    overall_comment: str  # 总体评价


class ReviewGenerator:
    """
    复盘报告生成器

    基于技术指标和交易结果自动生成复盘报告
    """

    def __init__(self):
        self.classifier = StrategyClassifier()
        logger.info("ReviewGenerator initialized")

    def generate_entry_reason(
        self,
        position: Position,
        market_data: Optional[MarketData]
    ) -> str:
        """
        生成入场理由描述

        Args:
            position: 持仓对象
            market_data: 入场时的市场数据

        Returns:
            入场理由文字描述
        """
        if not market_data:
            return "无法获取入场时的市场数据，无法分析入场理由。"

        is_long = position.direction in ['buy', 'buy_to_open', 'long']
        direction_text = "做多" if is_long else "做空"

        reasons = []

        # RSI分析
        if market_data.rsi_14:
            rsi = float(market_data.rsi_14)
            if rsi < RSI_OVERSOLD:
                reasons.append(f"RSI处于超卖区域({rsi:.1f})")
            elif rsi > RSI_OVERBOUGHT:
                reasons.append(f"RSI处于超买区域({rsi:.1f})")
            elif 40 <= rsi <= 60:
                reasons.append(f"RSI处于中性区域({rsi:.1f})")

        # MACD分析
        if market_data.macd and market_data.macd_signal:
            macd = float(market_data.macd)
            signal = float(market_data.macd_signal)
            if macd > signal:
                if macd > 0:
                    reasons.append("MACD金叉且位于零轴上方，多头动能强劲")
                else:
                    reasons.append("MACD金叉，多头动能开始恢复")
            else:
                if macd < 0:
                    reasons.append("MACD死叉且位于零轴下方，空头动能强劲")
                else:
                    reasons.append("MACD死叉，多头动能减弱")

        # ADX趋势分析
        if market_data.adx:
            adx = float(market_data.adx)
            if adx >= ADX_STRONG_TREND:
                reasons.append(f"ADX显示强趋势({adx:.1f})")
            elif adx >= ADX_MODERATE_TREND:
                reasons.append(f"ADX显示中等趋势({adx:.1f})")
            elif adx >= ADX_WEAK_TREND:
                reasons.append(f"ADX显示弱趋势({adx:.1f})")
            else:
                reasons.append(f"ADX显示无明显趋势({adx:.1f})")

        # 布林带分析
        if market_data.bb_upper and market_data.bb_lower and market_data.close:
            upper = float(market_data.bb_upper)
            lower = float(market_data.bb_lower)
            close = float(market_data.close)
            bb_pct = (close - lower) / (upper - lower) if upper != lower else 0.5

            if bb_pct < 0.1:
                reasons.append("价格跌破布林带下轨，可能存在均值回归机会")
            elif bb_pct < 0.2:
                reasons.append("价格接近布林带下轨")
            elif bb_pct > 0.9:
                reasons.append("价格突破布林带上轨，强势突破")
            elif bb_pct > 0.8:
                reasons.append("价格接近布林带上轨")

        # Stochastic分析
        if market_data.stoch_k:
            stoch = float(market_data.stoch_k)
            if stoch < STOCH_OVERSOLD:
                reasons.append(f"Stochastic处于超卖区域({stoch:.1f})")
            elif stoch > STOCH_OVERBOUGHT:
                reasons.append(f"Stochastic处于超买区域({stoch:.1f})")

        # 成交量分析
        if market_data.volume and market_data.volume_sma_20:
            vol_ratio = float(market_data.volume) / float(market_data.volume_sma_20)
            if vol_ratio >= 2.0:
                reasons.append(f"成交量显著放大({vol_ratio:.1f}倍于均量)")
            elif vol_ratio >= 1.5:
                reasons.append(f"成交量温和放大({vol_ratio:.1f}倍于均量)")

        # 均线排列
        if market_data.ma_5 and market_data.ma_20 and market_data.ma_50:
            ma5 = float(market_data.ma_5)
            ma20 = float(market_data.ma_20)
            ma50 = float(market_data.ma_50)

            if ma5 > ma20 > ma50:
                reasons.append("均线呈多头排列(MA5>MA20>MA50)")
            elif ma5 < ma20 < ma50:
                reasons.append("均线呈空头排列(MA5<MA20<MA50)")

        # 组合理由
        if reasons:
            strategy_type = position.strategy_type
            strategy_name = StrategyClassifier.STRATEGY_NAMES.get(strategy_type, "")

            intro = f"此笔{direction_text}交易"
            if strategy_name:
                intro += f"采用{strategy_name}策略"

            reason_text = "，".join(reasons)
            return f"{intro}。入场时：{reason_text}。"
        else:
            return f"此笔{direction_text}交易的技术指标信号不明显。"

    def generate_exit_evaluation(
        self,
        position: Position,
        exit_market_data: Optional[MarketData] = None
    ) -> str:
        """
        生成离场评价

        Args:
            position: 持仓对象
            exit_market_data: 离场时的市场数据

        Returns:
            离场评价文字描述
        """
        is_winner = position.net_pnl and float(position.net_pnl) >= 0
        net_pnl = float(position.net_pnl) if position.net_pnl else 0
        net_pnl_pct = float(position.net_pnl_pct) if position.net_pnl_pct else 0

        # 基本结果描述
        if is_winner:
            result = f"此笔交易盈利${abs(net_pnl):.2f}({net_pnl_pct:+.2f}%)"
        else:
            result = f"此笔交易亏损${abs(net_pnl):.2f}({net_pnl_pct:.2f}%)"

        evaluations = []

        # 分析MFE/MAE
        if position.mfe_pct and position.mae_pct:
            mfe = float(position.mfe_pct)
            mae = abs(float(position.mae_pct))

            if is_winner:
                # 盈利交易
                capture_ratio = (net_pnl_pct / mfe * 100) if mfe > 0 else 0
                if capture_ratio >= 80:
                    evaluations.append("成功捕获了大部分利润")
                elif capture_ratio >= 50:
                    evaluations.append("捕获了一半以上的最大利润")
                else:
                    evaluations.append(f"只捕获了{capture_ratio:.0f}%的最大利润，可能出场过早")
            else:
                # 亏损交易
                if mfe > abs(net_pnl_pct):
                    evaluations.append("曾经有盈利但没能保住，考虑设置移动止损")
                if mae > 20:
                    evaluations.append("承受了较大回撤，风险控制需要加强")

        # 分析持仓时间
        if position.holding_period_days:
            days = position.holding_period_days
            if days == 0:
                evaluations.append("日内交易")
            elif days <= 5:
                evaluations.append("短线持仓")
            elif days <= 20:
                evaluations.append("波段持仓")
            else:
                evaluations.append("中长线持仓")

        # 分析离场后走势
        if position.post_exit_20d_pct:
            post_pct = float(position.post_exit_20d_pct)
            is_long = position.direction in ['buy', 'buy_to_open', 'long']

            if is_long:
                if is_winner and post_pct > 10:
                    evaluations.append("离场后股价继续上涨，可能出场过早")
                elif is_winner and post_pct < -10:
                    evaluations.append("及时锁定利润，避免了后续下跌")
                elif not is_winner and post_pct > 20:
                    evaluations.append("止损后股价大幅反弹，止损位可能设置过紧")
                elif not is_winner and post_pct < -10:
                    evaluations.append("正确止损，避免了更大损失")
            else:
                # 做空逻辑相反
                if is_winner and post_pct < -10:
                    evaluations.append("离场后股价继续下跌，可能平仓过早")
                elif is_winner and post_pct > 10:
                    evaluations.append("及时平仓，避免了后续反弹")

        if evaluations:
            return f"{result}。" + "；".join(evaluations) + "。"
        else:
            return f"{result}。"

    def generate_review_report(
        self,
        position: Position,
        entry_market_data: Optional[MarketData] = None,
        exit_market_data: Optional[MarketData] = None
    ) -> ReviewReport:
        """
        生成完整复盘报告

        Args:
            position: 持仓对象
            entry_market_data: 入场时市场数据
            exit_market_data: 离场时市场数据

        Returns:
            ReviewReport对象
        """
        positives = []
        negatives = []
        suggestions = []

        is_winner = position.net_pnl and float(position.net_pnl) >= 0

        # 分析做对/做错的事情
        if is_winner:
            positives.append("实现了盈利")
        else:
            negatives.append("产生了亏损")

        # 基于评分分析
        if position.entry_quality_score:
            score = float(position.entry_quality_score)
            if score >= 70:
                positives.append("入场时机把握较好")
            elif score < 50:
                negatives.append("入场时机欠佳")
                suggestions.append("建议等待更明确的入场信号")

        if position.exit_quality_score:
            score = float(position.exit_quality_score)
            if score >= 70:
                positives.append("出场决策合理")
            elif score < 50:
                negatives.append("出场时机可以改进")

        if position.trend_quality_score:
            score = float(position.trend_quality_score)
            if score >= 70:
                positives.append("顺势交易，趋势把握准确")
            elif score < 50:
                negatives.append("逆势交易或趋势判断有误")
                suggestions.append("建议顺势而为，不要与趋势对抗")

        if position.risk_mgmt_score:
            score = float(position.risk_mgmt_score)
            if score >= 70:
                positives.append("风险控制得当")
            elif score < 50:
                negatives.append("风险管理需要加强")
                suggestions.append("建议设置合理的止损位，控制单笔亏损")

        # 基于MAE/MFE分析
        if position.mae_pct and position.mfe_pct:
            mae = abs(float(position.mae_pct))
            mfe = float(position.mfe_pct)

            if mfe > 0 and mae / mfe > 0.5:
                negatives.append("持仓期间承受了较大回撤")
                suggestions.append("可考虑设置移动止损保护利润")

            if is_winner and mfe > 0:
                capture = float(position.net_pnl_pct) / mfe if position.net_pnl_pct else 0
                if capture >= 0.7:
                    positives.append("成功捕获大部分利润")
                elif capture < 0.3:
                    suggestions.append("考虑延长持仓时间或优化出场点")

        # 生成总体评价
        overall_score = float(position.overall_score) if position.overall_score else 50
        grade = position.score_grade or "C"

        if overall_score >= 80:
            overall = f"这是一笔高质量的交易（{grade}级），各方面执行都比较到位。"
        elif overall_score >= 60:
            overall = f"这是一笔中等质量的交易（{grade}级），有一定改进空间。"
        else:
            overall = f"这笔交易质量偏低（{grade}级），需要认真总结改进。"

        return ReviewReport(
            entry_reason=self.generate_entry_reason(position, entry_market_data),
            exit_evaluation=self.generate_exit_evaluation(position, exit_market_data),
            positives=positives if positives else ["暂无明显亮点"],
            negatives=negatives if negatives else ["暂无明显问题"],
            suggestions=suggestions if suggestions else ["继续保持良好的交易习惯"],
            overall_comment=overall
        )

    @staticmethod
    def format_report_as_text(report: ReviewReport) -> str:
        """
        将报告格式化为纯文本

        Args:
            report: ReviewReport对象

        Returns:
            格式化的文本报告
        """
        lines = [
            "=" * 50,
            "交易复盘报告",
            "=" * 50,
            "",
            "【入场理由】",
            report.entry_reason,
            "",
            "【离场评价】",
            report.exit_evaluation,
            "",
            "【做对了什么】",
        ]

        for p in report.positives:
            lines.append(f"  ✅ {p}")

        lines.extend([
            "",
            "【可以改进】",
        ])

        for n in report.negatives:
            lines.append(f"  ❌ {n}")

        lines.extend([
            "",
            "【改进建议】",
        ])

        for s in report.suggestions:
            lines.append(f"  📝 {s}")

        lines.extend([
            "",
            "【总体评价】",
            report.overall_comment,
            "",
            "=" * 50,
        ])

        return "\n".join(lines)
