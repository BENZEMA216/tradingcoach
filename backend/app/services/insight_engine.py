"""
Trading Insight Engine - Rule-based insight generation

This engine analyzes trading positions and generates actionable insights
based on a comprehensive set of rules across 10 dimensions.
"""

from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session

from ..database import Position, PositionStatus
from ..schemas.insights import TradingInsight, InsightType, InsightCategory


class InsightEngine:
    """
    Rule-based trading insight generation engine.

    Analyzes positions across 10 dimensions:
    1. Time (weekday effect, month patterns)
    2. Holding Period (optimal holding, bag-holding tendency)
    3. Symbol (best/worst performers, concentration)
    4. Direction (long vs short effectiveness)
    5. Risk Management (stop-loss execution, risk-reward)
    6. Behavior Patterns (revenge trading, overconfidence)
    7. Fees (fee impact analysis)
    8. Options (DTE, moneyness analysis)
    9. Benchmark (performance comparison)
    10. Trends (improvement/deterioration patterns)
    """

    def __init__(self, db: Session):
        self.db = db
        self.positions: List[Position] = []
        self.insights: List[TradingInsight] = []

        # Cached computations
        self._winners: List[Position] = []
        self._losers: List[Position] = []
        self._win_rate: float = 0.0
        self._avg_pnl: float = 0.0
        self._total_pnl: float = 0.0

    def generate_insights(
        self,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        limit: int = 5
    ) -> List[TradingInsight]:
        """
        Generate insights for the given date range.
        Returns top N insights sorted by priority.
        """
        # Fetch positions
        query = self.db.query(Position).filter(Position.status == PositionStatus.CLOSED)

        if date_start:
            query = query.filter(Position.close_date >= date_start)
        if date_end:
            query = query.filter(Position.close_date <= date_end)

        self.positions = query.order_by(Position.close_date).all()

        if len(self.positions) < 3:
            return []

        # Compute basic stats
        self._compute_basic_stats()

        # Clear previous insights
        self.insights = []

        # Run all analyzers
        self._analyze_weekday_effect()
        self._analyze_holding_period()
        self._analyze_symbols()
        self._analyze_direction()
        self._analyze_risk_management()
        self._analyze_behavior_patterns()
        self._analyze_fees()
        self._analyze_options()
        self._analyze_trends()

        # Sort by priority (descending) and return top N
        self.insights.sort(key=lambda x: x.priority, reverse=True)
        return self.insights[:limit]

    def _compute_basic_stats(self):
        """Compute commonly used statistics"""
        self._winners = [p for p in self.positions if p.net_pnl and float(p.net_pnl) > 0]
        self._losers = [p for p in self.positions if p.net_pnl and float(p.net_pnl) <= 0]

        total = len(self.positions)
        self._win_rate = len(self._winners) / total * 100 if total > 0 else 0
        self._total_pnl = sum(float(p.net_pnl or 0) for p in self.positions)
        self._avg_pnl = self._total_pnl / total if total > 0 else 0

    def _add_insight(self, insight: TradingInsight):
        """Add an insight to the list"""
        self.insights.append(insight)

    # ========== 1. TIME DIMENSION ANALYSIS ==========

    def _analyze_weekday_effect(self):
        """
        T01: Weekday problem - Win rate significantly below average
        T02: Weekday strength - Win rate significantly above average
        """
        weekday_stats = defaultdict(lambda: {"count": 0, "winners": 0, "pnl": 0.0})
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        weekday_names_zh = ["周一", "周二", "周三", "周四", "周五"]

        for p in self.positions:
            if p.close_date:
                wd = p.close_date.weekday()
                if wd < 5:  # Only weekdays
                    weekday_stats[wd]["count"] += 1
                    weekday_stats[wd]["pnl"] += float(p.net_pnl or 0)
                    if p.net_pnl and float(p.net_pnl) > 0:
                        weekday_stats[wd]["winners"] += 1

        for wd, stats in weekday_stats.items():
            if stats["count"] >= 5:  # Minimum sample size
                wd_win_rate = stats["winners"] / stats["count"] * 100

                # T01: Problem weekday
                if wd_win_rate < self._win_rate - 20:
                    self._add_insight(TradingInsight(
                        id=f"T01-{weekday_names[wd]}",
                        type=InsightType.PROBLEM,
                        category=InsightCategory.TIME,
                        priority=85,
                        title=f"{weekday_names_zh[wd]}胜率偏低",
                        description=f"{weekday_names_zh[wd]}胜率仅{wd_win_rate:.0f}%，远低于平均{self._win_rate:.0f}%",
                        suggestion=f"建议减少{weekday_names_zh[wd]}的交易，或在这一天采取更保守的策略",
                        data_points={
                            "weekday": weekday_names[wd],
                            "weekday_zh": weekday_names_zh[wd],
                            "weekday_trades": stats["count"],
                            "weekday_win_rate": round(wd_win_rate, 1),
                            "average_win_rate": round(self._win_rate, 1),
                            "weekday_pnl": round(stats["pnl"], 2),
                        }
                    ))

                # T02: Strong weekday
                elif wd_win_rate > self._win_rate + 15:
                    self._add_insight(TradingInsight(
                        id=f"T02-{weekday_names[wd]}",
                        type=InsightType.STRENGTH,
                        category=InsightCategory.TIME,
                        priority=60,
                        title=f"{weekday_names_zh[wd]}表现优异",
                        description=f"{weekday_names_zh[wd]}胜率高达{wd_win_rate:.0f}%，明显高于平均{self._win_rate:.0f}%",
                        suggestion=f"可以考虑在{weekday_names_zh[wd]}增加交易机会",
                        data_points={
                            "weekday": weekday_names[wd],
                            "weekday_zh": weekday_names_zh[wd],
                            "weekday_trades": stats["count"],
                            "weekday_win_rate": round(wd_win_rate, 1),
                            "average_win_rate": round(self._win_rate, 1),
                            "weekday_pnl": round(stats["pnl"], 2),
                        }
                    ))

    # ========== 2. HOLDING PERIOD ANALYSIS ==========

    def _analyze_holding_period(self):
        """
        H01: Best holding period
        H02: Long holding risk
        H03: Intraday vs swing comparison
        H04: Bag-holding tendency
        H05: Early profit-taking
        """
        # Calculate average holding days for winners vs losers
        winners_with_holding = [p for p in self._winners if p.holding_period_days is not None]
        losers_with_holding = [p for p in self._losers if p.holding_period_days is not None]

        avg_winner_holding = (
            sum(p.holding_period_days for p in winners_with_holding) / len(winners_with_holding)
            if winners_with_holding else 0
        )
        avg_loser_holding = (
            sum(p.holding_period_days for p in losers_with_holding) / len(losers_with_holding)
            if losers_with_holding else 0
        )

        # H04: Bag-holding tendency - losers held much longer than winners
        if avg_loser_holding > avg_winner_holding * 1.5 and len(losers_with_holding) >= 5:
            self._add_insight(TradingInsight(
                id="H04",
                type=InsightType.PROBLEM,
                category=InsightCategory.HOLDING,
                priority=90,
                title="存在扛单倾向",
                description=f"亏损交易平均持仓{avg_loser_holding:.1f}天，而盈利交易仅{avg_winner_holding:.1f}天",
                suggestion="建议设置严格的止损规则，亏损交易不应持仓过久",
                data_points={
                    "avg_winner_holding_days": round(avg_winner_holding, 1),
                    "avg_loser_holding_days": round(avg_loser_holding, 1),
                    "ratio": round(avg_loser_holding / avg_winner_holding, 2) if avg_winner_holding > 0 else None,
                    "loser_count": len(losers_with_holding),
                    "winner_count": len(winners_with_holding),
                }
            ))

        # H02: Long holding risk - positions held > 7 days have high loss rate
        long_positions = [p for p in self.positions if p.holding_period_days and p.holding_period_days > 7]
        if len(long_positions) >= 5:
            long_losers = [p for p in long_positions if p.net_pnl and float(p.net_pnl) <= 0]
            long_loss_rate = len(long_losers) / len(long_positions) * 100

            if long_loss_rate > 60:
                self._add_insight(TradingInsight(
                    id="H02",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.HOLDING,
                    priority=80,
                    title="长持仓风险较高",
                    description=f"持仓超过7天的交易中，{long_loss_rate:.0f}%是亏损的",
                    suggestion="考虑缩短平均持仓时间，或对长期持仓设置更严格的风控",
                    data_points={
                        "long_position_count": len(long_positions),
                        "long_loser_count": len(long_losers),
                        "long_loss_rate": round(long_loss_rate, 1),
                    }
                ))

        # H03: Intraday vs Swing comparison
        intraday = [p for p in self.positions if p.holding_period_days == 0]
        swing = [p for p in self.positions if p.holding_period_days and p.holding_period_days > 0]

        if len(intraday) >= 5 and len(swing) >= 5:
            intraday_winners = [p for p in intraday if p.net_pnl and float(p.net_pnl) > 0]
            swing_winners = [p for p in swing if p.net_pnl and float(p.net_pnl) > 0]

            intraday_wr = len(intraday_winners) / len(intraday) * 100
            swing_wr = len(swing_winners) / len(swing) * 100

            if abs(intraday_wr - swing_wr) > 15:
                better = "日内" if intraday_wr > swing_wr else "波段"
                worse = "波段" if intraday_wr > swing_wr else "日内"
                better_wr = max(intraday_wr, swing_wr)
                worse_wr = min(intraday_wr, swing_wr)

                self._add_insight(TradingInsight(
                    id="H03",
                    type=InsightType.REMINDER,
                    category=InsightCategory.HOLDING,
                    priority=65,
                    title=f"{better}交易更擅长",
                    description=f"{better}交易胜率{better_wr:.0f}%，而{worse}交易仅{worse_wr:.0f}%",
                    suggestion=f"可以考虑增加{better}交易的比重，减少{worse}交易",
                    data_points={
                        "intraday_count": len(intraday),
                        "intraday_win_rate": round(intraday_wr, 1),
                        "swing_count": len(swing),
                        "swing_win_rate": round(swing_wr, 1),
                    }
                ))

        # H01: Best holding period bucket
        buckets = [
            ("当天", 0, 0),
            ("1-3天", 1, 3),
            ("4-7天", 4, 7),
            ("1-2周", 8, 14),
        ]

        best_bucket = None
        best_wr = 0
        best_count = 0

        for label, min_d, max_d in buckets:
            bucket_positions = [
                p for p in self.positions
                if p.holding_period_days is not None and min_d <= p.holding_period_days <= max_d
            ]
            if len(bucket_positions) >= 10:
                bucket_winners = [p for p in bucket_positions if p.net_pnl and float(p.net_pnl) > 0]
                bucket_wr = len(bucket_winners) / len(bucket_positions) * 100

                if bucket_wr > 65 and bucket_wr > best_wr:
                    best_bucket = label
                    best_wr = bucket_wr
                    best_count = len(bucket_positions)

        if best_bucket:
            self._add_insight(TradingInsight(
                id="H01",
                type=InsightType.STRENGTH,
                category=InsightCategory.HOLDING,
                priority=55,
                title=f"最佳持仓周期: {best_bucket}",
                description=f"持仓{best_bucket}的交易胜率高达{best_wr:.0f}%（{best_count}笔）",
                suggestion=f"可以优化交易计划，使持仓时间更集中在{best_bucket}这个区间",
                data_points={
                    "best_period": best_bucket,
                    "win_rate": round(best_wr, 1),
                    "trade_count": best_count,
                }
            ))

        # H05: Early profit-taking detection
        winners_with_post_exit = [
            p for p in self._winners
            if p.post_exit_5d_pct is not None
        ]
        if len(winners_with_post_exit) >= 10:
            continued_up = [p for p in winners_with_post_exit if float(p.post_exit_5d_pct) > 5]
            continued_up_pct = len(continued_up) / len(winners_with_post_exit) * 100
            if continued_up_pct > 50:
                avg_missed = sum(float(p.post_exit_5d_pct) for p in continued_up) / len(continued_up)
                self._add_insight(TradingInsight(
                    id="H05",
                    type=InsightType.REMINDER,
                    category=InsightCategory.HOLDING,
                    priority=63,
                    title="可能存在过早止盈",
                    description=f"{continued_up_pct:.0f}%的盈利交易在离场后5天内又涨了超过5%，平均再涨{avg_missed:.1f}%",
                    suggestion="考虑使用追踪止盈或分批止盈策略，让利润充分运行",
                    data_points={
                        "continued_up_count": len(continued_up),
                        "total_winners": len(winners_with_post_exit),
                        "continued_up_pct": round(continued_up_pct, 1),
                        "avg_missed_pct": round(avg_missed, 1),
                    }
                ))

        # H06: Holding period and quality score relationship
        positions_with_score = [
            p for p in self.positions
            if p.overall_score is not None and p.holding_period_days is not None
        ]
        if len(positions_with_score) >= 20:
            short_holding = [p for p in positions_with_score if p.holding_period_days <= 1]
            long_holding = [p for p in positions_with_score if p.holding_period_days > 3]

            if len(short_holding) >= 10 and len(long_holding) >= 10:
                short_avg_score = sum(float(p.overall_score) for p in short_holding) / len(short_holding)
                long_avg_score = sum(float(p.overall_score) for p in long_holding) / len(long_holding)

                if short_avg_score > long_avg_score + 10:
                    self._add_insight(TradingInsight(
                        id="H06",
                        type=InsightType.REMINDER,
                        category=InsightCategory.HOLDING,
                        priority=58,
                        title="短线交易质量更高",
                        description=f"短线持仓平均评分{short_avg_score:.0f}分，长线仅{long_avg_score:.0f}分",
                        suggestion="你可能更适合短线交易，长线持仓需要改进入场和出场策略",
                        data_points={
                            "short_avg_score": round(short_avg_score, 1),
                            "short_count": len(short_holding),
                            "long_avg_score": round(long_avg_score, 1),
                            "long_count": len(long_holding),
                        }
                    ))

    # ========== 3. SYMBOL ANALYSIS ==========

    def _analyze_symbols(self):
        """
        S01: Strong symbol - high win rate
        S02: Problem symbol - low win rate
        S03: Over-concentration
        S04: Repeated losses on same symbol
        """
        symbol_stats = defaultdict(lambda: {
            "count": 0, "winners": 0, "pnl": 0.0, "consecutive_losses": 0, "max_consec_losses": 0
        })

        # Group by symbol
        for p in self.positions:
            symbol = p.symbol
            stats = symbol_stats[symbol]
            stats["count"] += 1
            stats["pnl"] += float(p.net_pnl or 0)

            if p.net_pnl and float(p.net_pnl) > 0:
                stats["winners"] += 1
                stats["consecutive_losses"] = 0
            else:
                stats["consecutive_losses"] += 1
                stats["max_consec_losses"] = max(stats["max_consec_losses"], stats["consecutive_losses"])

        total_trades = len(self.positions)

        for symbol, stats in symbol_stats.items():
            if stats["count"] >= 5:
                symbol_wr = stats["winners"] / stats["count"] * 100
                concentration = stats["count"] / total_trades * 100

                # S01: Strong symbol
                if symbol_wr > 70:
                    self._add_insight(TradingInsight(
                        id=f"S01-{symbol}",
                        type=InsightType.STRENGTH,
                        category=InsightCategory.SYMBOL,
                        priority=70,
                        title=f"{symbol}是优势标的",
                        description=f"{symbol}胜率{symbol_wr:.0f}%（{stats['count']}笔），总盈利${stats['pnl']:,.0f}",
                        suggestion=f"继续关注{symbol}的交易机会，这是你最擅长的标的之一",
                        data_points={
                            "symbol": symbol,
                            "trade_count": stats["count"],
                            "win_rate": round(symbol_wr, 1),
                            "total_pnl": round(stats["pnl"], 2),
                            "winners": stats["winners"],
                            "losers": stats["count"] - stats["winners"],
                        }
                    ))

                # S02: Problem symbol
                elif symbol_wr < 35:
                    self._add_insight(TradingInsight(
                        id=f"S02-{symbol}",
                        type=InsightType.PROBLEM,
                        category=InsightCategory.SYMBOL,
                        priority=75,
                        title=f"{symbol}表现不佳",
                        description=f"{symbol}胜率仅{symbol_wr:.0f}%（{stats['count']}笔），总亏损${abs(stats['pnl']):,.0f}",
                        suggestion=f"建议暂停交易{symbol}，或深入分析为何在此标的上表现不佳",
                        data_points={
                            "symbol": symbol,
                            "trade_count": stats["count"],
                            "win_rate": round(symbol_wr, 1),
                            "total_pnl": round(stats["pnl"], 2),
                        }
                    ))

                # S03: Over-concentration
                if concentration > 30:
                    self._add_insight(TradingInsight(
                        id=f"S03-{symbol}",
                        type=InsightType.REMINDER,
                        category=InsightCategory.SYMBOL,
                        priority=60,
                        title=f"{symbol}交易过度集中",
                        description=f"{symbol}占总交易的{concentration:.0f}%，存在过度集中风险",
                        suggestion="建议分散交易标的，降低单一标的依赖",
                        data_points={
                            "symbol": symbol,
                            "concentration_pct": round(concentration, 1),
                            "trade_count": stats["count"],
                            "total_trades": total_trades,
                        }
                    ))

                # S04: Repeated losses
                if stats["max_consec_losses"] >= 3:
                    self._add_insight(TradingInsight(
                        id=f"S04-{symbol}",
                        type=InsightType.PROBLEM,
                        category=InsightCategory.SYMBOL,
                        priority=80,
                        title=f"{symbol}连续亏损",
                        description=f"{symbol}曾出现连续{stats['max_consec_losses']}笔亏损",
                        suggestion=f"在{symbol}连亏后应暂停交易，冷静分析后再考虑入场",
                        data_points={
                            "symbol": symbol,
                            "max_consecutive_losses": stats["max_consec_losses"],
                            "trade_count": stats["count"],
                        }
                    ))

        # S05: First trade on new symbol performance
        symbol_first_trade = {}
        for p in self.positions:
            if p.symbol not in symbol_first_trade:
                symbol_first_trade[p.symbol] = p.net_pnl and float(p.net_pnl) > 0

        first_trade_results = list(symbol_first_trade.values())
        if len(first_trade_results) >= 10:
            first_trade_wr = sum(first_trade_results) / len(first_trade_results) * 100
            if first_trade_wr < self._win_rate - 15:
                self._add_insight(TradingInsight(
                    id="S05",
                    type=InsightType.REMINDER,
                    category=InsightCategory.SYMBOL,
                    priority=65,
                    title="新标的首次交易风险",
                    description=f"首次交易新标的的胜率仅{first_trade_wr:.0f}%，低于平均{self._win_rate:.0f}%",
                    suggestion="建议对新标的采取更保守的仓位，或先观察再入场",
                    data_points={
                        "first_trade_win_rate": round(first_trade_wr, 1),
                        "average_win_rate": round(self._win_rate, 1),
                        "unique_symbols": len(first_trade_results),
                    }
                ))

        # S06: Options vs Stocks comparison
        options = [p for p in self.positions if p.is_option]
        stocks = [p for p in self.positions if not p.is_option]

        if len(options) >= 5 and len(stocks) >= 5:
            option_winners = [p for p in options if p.net_pnl and float(p.net_pnl) > 0]
            stock_winners = [p for p in stocks if p.net_pnl and float(p.net_pnl) > 0]

            option_wr = len(option_winners) / len(options) * 100
            stock_wr = len(stock_winners) / len(stocks) * 100

            option_pnl = sum(float(p.net_pnl or 0) for p in options)
            stock_pnl = sum(float(p.net_pnl or 0) for p in stocks)

            if abs(option_wr - stock_wr) > 15:
                better = "期权" if option_wr > stock_wr else "股票"
                worse = "股票" if option_wr > stock_wr else "期权"
                better_wr = max(option_wr, stock_wr)
                worse_wr = min(option_wr, stock_wr)

                self._add_insight(TradingInsight(
                    id="S06",
                    type=InsightType.REMINDER,
                    category=InsightCategory.SYMBOL,
                    priority=62,
                    title=f"{better}交易更擅长",
                    description=f"{better}胜率{better_wr:.0f}%，{worse}仅{worse_wr:.0f}%",
                    suggestion=f"可以适当增加{better}交易的比重",
                    data_points={
                        "option_count": len(options),
                        "option_win_rate": round(option_wr, 1),
                        "option_pnl": round(option_pnl, 2),
                        "stock_count": len(stocks),
                        "stock_win_rate": round(stock_wr, 1),
                        "stock_pnl": round(stock_pnl, 2),
                    }
                ))

    # ========== 4. DIRECTION ANALYSIS ==========

    def _analyze_direction(self):
        """
        D01: Long vs Short preference
        D02: Strategy effectiveness
        """
        direction_stats = defaultdict(lambda: {"count": 0, "winners": 0, "pnl": 0.0})

        for p in self.positions:
            direction = p.direction or "unknown"
            direction_stats[direction]["count"] += 1
            direction_stats[direction]["pnl"] += float(p.net_pnl or 0)
            if p.net_pnl and float(p.net_pnl) > 0:
                direction_stats[direction]["winners"] += 1

        # D01: Long vs Short preference
        long_stats = direction_stats.get("long", {"count": 0, "winners": 0})
        short_stats = direction_stats.get("short", {"count": 0, "winners": 0})

        if long_stats["count"] >= 5 and short_stats["count"] >= 5:
            long_wr = long_stats["winners"] / long_stats["count"] * 100
            short_wr = short_stats["winners"] / short_stats["count"] * 100

            if abs(long_wr - short_wr) > 15:
                better = "做多" if long_wr > short_wr else "做空"
                worse = "做空" if long_wr > short_wr else "做多"
                better_wr = max(long_wr, short_wr)
                worse_wr = min(long_wr, short_wr)

                self._add_insight(TradingInsight(
                    id="D01",
                    type=InsightType.REMINDER,
                    category=InsightCategory.DIRECTION,
                    priority=65,
                    title=f"{better}更擅长",
                    description=f"{better}胜率{better_wr:.0f}%，{worse}胜率仅{worse_wr:.0f}%",
                    suggestion=f"可以考虑增加{better}交易的比重",
                    data_points={
                        "long_count": long_stats["count"],
                        "long_win_rate": round(long_wr, 1),
                        "short_count": short_stats["count"],
                        "short_win_rate": round(short_wr, 1),
                    }
                ))

        # D02: Strategy effectiveness
        strategy_stats = defaultdict(lambda: {"count": 0, "winners": 0, "pnl": 0.0})

        for p in self.positions:
            strategy = p.strategy_type or "unknown"
            strategy_stats[strategy]["count"] += 1
            strategy_stats[strategy]["pnl"] += float(p.net_pnl or 0)
            if p.net_pnl and float(p.net_pnl) > 0:
                strategy_stats[strategy]["winners"] += 1

        for strategy, stats in strategy_stats.items():
            if strategy != "unknown" and stats["count"] >= 10:
                strategy_wr = stats["winners"] / stats["count"] * 100

                if strategy_wr > 65:
                    strategy_name_map = {
                        "trend": "趋势跟踪",
                        "mean_reversion": "均值回归",
                        "breakout": "突破交易",
                        "momentum": "动量交易",
                        "range": "区间交易",
                    }
                    strategy_name = strategy_name_map.get(strategy, strategy)

                    self._add_insight(TradingInsight(
                        id="D02",
                        type=InsightType.STRENGTH,
                        category=InsightCategory.DIRECTION,
                        priority=60,
                        title=f"{strategy_name}策略有效",
                        description=f"{strategy_name}策略胜率{strategy_wr:.0f}%（{stats['count']}笔）",
                        suggestion=f"继续使用{strategy_name}策略，并优化相关参数",
                        data_points={
                            "strategy": strategy,
                            "strategy_name": strategy_name,
                            "trade_count": stats["count"],
                            "win_rate": round(strategy_wr, 1),
                            "total_pnl": round(stats["pnl"], 2),
                        }
                    ))

    # ========== 5. RISK MANAGEMENT ANALYSIS ==========

    def _analyze_risk_management(self):
        """
        R01: Win/Loss ratio imbalance
        R02: Stop-loss execution issues
        R03: Single trade risk too high
        R05: Consecutive losses
        """
        # R01: Win/Loss ratio imbalance
        if self._winners and self._losers:
            avg_win = sum(float(p.net_pnl) for p in self._winners) / len(self._winners)
            avg_loss = abs(sum(float(p.net_pnl) for p in self._losers) / len(self._losers))

            if avg_loss > avg_win * 1.5:
                self._add_insight(TradingInsight(
                    id="R01",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.RISK,
                    priority=85,
                    title="盈亏比失衡",
                    description=f"平均亏损${avg_loss:.0f}是平均盈利${avg_win:.0f}的{avg_loss/avg_win:.1f}倍",
                    suggestion="需要改进止损策略，减小平均亏损额，或提高盈利目标",
                    data_points={
                        "avg_win": round(avg_win, 2),
                        "avg_loss": round(avg_loss, 2),
                        "ratio": round(avg_loss / avg_win, 2),
                        "winner_count": len(self._winners),
                        "loser_count": len(self._losers),
                    }
                ))

        # R02: Stop-loss execution - check MAE
        high_mae_losers = []
        for p in self._losers:
            if p.mae_pct and float(p.mae_pct) < -10:
                high_mae_losers.append(p)

        if len(self._losers) >= 5:
            high_mae_pct = len(high_mae_losers) / len(self._losers) * 100

            if high_mae_pct > 60:
                self._add_insight(TradingInsight(
                    id="R02",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.RISK,
                    priority=88,
                    title="止损执行不严格",
                    description=f"{high_mae_pct:.0f}%的亏损交易MAE超过-10%，说明止损设置或执行有问题",
                    suggestion="建议设置更严格的止损点，并严格执行",
                    data_points={
                        "high_mae_loser_count": len(high_mae_losers),
                        "total_loser_count": len(self._losers),
                        "high_mae_pct": round(high_mae_pct, 1),
                    }
                ))

        # R03: Single trade risk too high
        if self._total_pnl > 0:
            max_loss = min(float(p.net_pnl or 0) for p in self.positions)
            if abs(max_loss) > self._total_pnl * 0.2:  # Single loss > 20% of total profit
                self._add_insight(TradingInsight(
                    id="R03",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.RISK,
                    priority=82,
                    title="单笔风险过大",
                    description=f"最大单笔亏损${abs(max_loss):.0f}，占总盈利的{abs(max_loss)/self._total_pnl*100:.0f}%",
                    suggestion="建议控制单笔交易的风险敞口，设置止损以限制最大亏损",
                    data_points={
                        "max_single_loss": round(max_loss, 2),
                        "total_pnl": round(self._total_pnl, 2),
                        "pct_of_total": round(abs(max_loss) / self._total_pnl * 100, 1),
                    }
                ))

        # R05: Consecutive losses
        max_consecutive_losses = 0
        current_losses = 0

        for p in self.positions:
            if p.net_pnl and float(p.net_pnl) <= 0:
                current_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
            else:
                current_losses = 0

        if max_consecutive_losses >= 5:
            self._add_insight(TradingInsight(
                id="R05",
                type=InsightType.REMINDER,
                category=InsightCategory.RISK,
                priority=70,
                title="出现过连续亏损",
                description=f"最长连续亏损{max_consecutive_losses}笔",
                suggestion="连亏时应暂停交易，分析原因后再继续",
                data_points={
                    "max_consecutive_losses": max_consecutive_losses,
                }
            ))

        # R06: MAE/MFE efficiency analysis
        positions_with_mfe = [p for p in self._winners if p.mfe and p.net_pnl and float(p.mfe) > 0]
        if len(positions_with_mfe) >= 5:
            capture_ratios = []
            for p in positions_with_mfe:
                mfe = float(p.mfe)
                pnl = float(p.net_pnl)
                if mfe > 0:
                    capture_ratios.append(pnl / mfe)

            if capture_ratios:
                avg_capture = sum(capture_ratios) / len(capture_ratios) * 100
                if avg_capture < 50:
                    self._add_insight(TradingInsight(
                        id="R06",
                        type=InsightType.PROBLEM,
                        category=InsightCategory.RISK,
                        priority=75,
                        title="盈利捕获率偏低",
                        description=f"盈利交易平均只捕获了最大浮盈的{avg_capture:.0f}%",
                        suggestion="考虑使用追踪止盈或分批止盈，以获取更多利润",
                        data_points={
                            "avg_capture_ratio": round(avg_capture, 1),
                            "sample_count": len(capture_ratios),
                        }
                    ))

        # R07: Stop-loss discipline - check if losers hit MAE and continued holding
        losers_with_mae = [p for p in self._losers if p.mae_pct and float(p.mae_pct) < -5]
        deep_losers = [p for p in losers_with_mae if float(p.mae_pct) < -15]
        if len(losers_with_mae) >= 5:
            deep_loss_pct = len(deep_losers) / len(losers_with_mae) * 100
            if deep_loss_pct > 30:
                self._add_insight(TradingInsight(
                    id="R07",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.RISK,
                    priority=83,
                    title="止损纪律需改进",
                    description=f"{deep_loss_pct:.0f}%的亏损交易最大浮亏超过-15%，说明止损执行不及时",
                    suggestion="建议在入场时就设定止损点，并严格执行",
                    data_points={
                        "deep_loser_count": len(deep_losers),
                        "total_losers": len(losers_with_mae),
                        "deep_loss_pct": round(deep_loss_pct, 1),
                    }
                ))

        # R08: Overnight holding risk
        positions_with_holding = [p for p in self.positions if p.holding_period_days is not None]
        overnight = [p for p in positions_with_holding if p.holding_period_days >= 1]
        intraday = [p for p in positions_with_holding if p.holding_period_days == 0]

        if len(overnight) >= 10 and len(intraday) >= 10:
            overnight_losers = [p for p in overnight if p.net_pnl and float(p.net_pnl) <= 0]
            overnight_loss_rate = len(overnight_losers) / len(overnight) * 100
            intraday_losers = [p for p in intraday if p.net_pnl and float(p.net_pnl) <= 0]
            intraday_loss_rate = len(intraday_losers) / len(intraday) * 100

            if overnight_loss_rate > intraday_loss_rate + 15:
                self._add_insight(TradingInsight(
                    id="R08",
                    type=InsightType.REMINDER,
                    category=InsightCategory.RISK,
                    priority=68,
                    title="隔夜持仓风险较高",
                    description=f"隔夜持仓亏损率{overnight_loss_rate:.0f}%，高于日内的{intraday_loss_rate:.0f}%",
                    suggestion="建议减少隔夜持仓，或对隔夜仓位设置更严格的止损",
                    data_points={
                        "overnight_count": len(overnight),
                        "overnight_loss_rate": round(overnight_loss_rate, 1),
                        "intraday_count": len(intraday),
                        "intraday_loss_rate": round(intraday_loss_rate, 1),
                    }
                ))

    # ========== 6. BEHAVIOR PATTERN ANALYSIS ==========

    def _analyze_behavior_patterns(self):
        """
        B01: Revenge trading
        B02: Overconfidence after big win
        B03: Abnormal trading frequency
        B05: Overconfidence after winning streak
        """
        if len(self.positions) < 5:
            return

        # Analyze pattern: what happens after loss/win
        after_loss_results = []
        after_big_win_results = []
        after_streak_results = []

        avg_win = sum(float(p.net_pnl) for p in self._winners) / len(self._winners) if self._winners else 0

        consecutive_wins = 0
        prev_pnl = None

        for i, p in enumerate(self.positions):
            pnl = float(p.net_pnl or 0)

            if i > 0:
                # B01: After loss
                if prev_pnl is not None and prev_pnl < 0:
                    after_loss_results.append(pnl > 0)

                # B02: After big win (>2x average win)
                if prev_pnl is not None and prev_pnl > avg_win * 2:
                    after_big_win_results.append(pnl > 0)

                # B05: After 3+ consecutive wins
                if consecutive_wins >= 3:
                    after_streak_results.append(pnl > 0)

            if pnl > 0:
                consecutive_wins += 1
            else:
                consecutive_wins = 0

            prev_pnl = pnl

        # B01: Revenge trading pattern
        if len(after_loss_results) >= 5:
            win_rate_after_loss = sum(after_loss_results) / len(after_loss_results) * 100
            if win_rate_after_loss < 40:
                self._add_insight(TradingInsight(
                    id="B01",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.BEHAVIOR,
                    priority=92,
                    title="可能存在报复性交易",
                    description=f"亏损后的下一笔交易仅{win_rate_after_loss:.0f}%盈利，低于平均水平",
                    suggestion="亏损后建议暂停交易，避免情绪化操作",
                    data_points={
                        "trades_after_loss": len(after_loss_results),
                        "win_rate_after_loss": round(win_rate_after_loss, 1),
                        "average_win_rate": round(self._win_rate, 1),
                    }
                ))

        # B02: Overconfidence after big win
        if len(after_big_win_results) >= 3:
            win_rate_after_big_win = sum(after_big_win_results) / len(after_big_win_results) * 100
            if win_rate_after_big_win < 45:
                self._add_insight(TradingInsight(
                    id="B02",
                    type=InsightType.REMINDER,
                    category=InsightCategory.BEHAVIOR,
                    priority=68,
                    title="大赚后需警惕",
                    description=f"大赚后的下一笔交易仅{win_rate_after_big_win:.0f}%盈利",
                    suggestion="大赚后容易放松警惕，建议保持纪律性",
                    data_points={
                        "trades_after_big_win": len(after_big_win_results),
                        "win_rate_after_big_win": round(win_rate_after_big_win, 1),
                    }
                ))

        # B05: Overconfidence after streak
        if len(after_streak_results) >= 3:
            win_rate_after_streak = sum(after_streak_results) / len(after_streak_results) * 100
            if win_rate_after_streak < self._win_rate - 15:
                self._add_insight(TradingInsight(
                    id="B05",
                    type=InsightType.REMINDER,
                    category=InsightCategory.BEHAVIOR,
                    priority=65,
                    title="连胜后需谨慎",
                    description=f"连胜3次后的下一笔交易胜率仅{win_rate_after_streak:.0f}%",
                    suggestion="连续盈利后可能过度自信，需保持谨慎",
                    data_points={
                        "trades_after_streak": len(after_streak_results),
                        "win_rate_after_streak": round(win_rate_after_streak, 1),
                        "average_win_rate": round(self._win_rate, 1),
                    }
                ))

        # B06: Trading hour preference analysis
        hour_stats = defaultdict(lambda: {"count": 0, "winners": 0, "pnl": 0.0})
        for p in self.positions:
            if p.open_date:
                # Try to get hour from datetime
                try:
                    if hasattr(p.open_date, 'hour'):
                        hour = p.open_date.hour
                    else:
                        continue
                    hour_stats[hour]["count"] += 1
                    hour_stats[hour]["pnl"] += float(p.net_pnl or 0)
                    if p.net_pnl and float(p.net_pnl) > 0:
                        hour_stats[hour]["winners"] += 1
                except:
                    continue

        if hour_stats:
            best_hour = None
            best_hour_wr = 0
            worst_hour = None
            worst_hour_wr = 100

            for hour, stats in hour_stats.items():
                if stats["count"] >= 5:
                    hour_wr = stats["winners"] / stats["count"] * 100
                    if hour_wr > best_hour_wr:
                        best_hour = hour
                        best_hour_wr = hour_wr
                    if hour_wr < worst_hour_wr:
                        worst_hour = hour
                        worst_hour_wr = hour_wr

            if best_hour is not None and best_hour_wr > self._win_rate + 15:
                self._add_insight(TradingInsight(
                    id="B06",
                    type=InsightType.STRENGTH,
                    category=InsightCategory.BEHAVIOR,
                    priority=55,
                    title=f"{best_hour}点交易表现最佳",
                    description=f"{best_hour}点开仓的交易胜率{best_hour_wr:.0f}%，明显高于平均",
                    suggestion=f"可以重点关注{best_hour}点左右的交易机会",
                    data_points={
                        "best_hour": best_hour,
                        "best_hour_win_rate": round(best_hour_wr, 1),
                        "best_hour_count": hour_stats[best_hour]["count"],
                        "average_win_rate": round(self._win_rate, 1),
                    }
                ))

            if worst_hour is not None and worst_hour_wr < self._win_rate - 15:
                self._add_insight(TradingInsight(
                    id="B07",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.BEHAVIOR,
                    priority=72,
                    title=f"{worst_hour}点交易需警惕",
                    description=f"{worst_hour}点开仓的交易胜率仅{worst_hour_wr:.0f}%，远低于平均",
                    suggestion=f"建议避免在{worst_hour}点左右进行交易",
                    data_points={
                        "worst_hour": worst_hour,
                        "worst_hour_win_rate": round(worst_hour_wr, 1),
                        "worst_hour_count": hour_stats[worst_hour]["count"],
                        "average_win_rate": round(self._win_rate, 1),
                    }
                ))

        # B08: Adding to position behavior (same symbol multiple trades)
        symbol_sequences = defaultdict(list)
        for p in self.positions:
            symbol_sequences[p.symbol].append(p)

        add_to_position_results = []
        for symbol, trades in symbol_sequences.items():
            if len(trades) >= 2:
                # If trades are close in time (within 7 days), might be adding to position
                for i in range(1, len(trades)):
                    if trades[i].open_date and trades[i-1].close_date:
                        try:
                            gap = (trades[i].open_date - trades[i-1].close_date).days
                            if 0 <= gap <= 7:
                                add_to_position_results.append(
                                    trades[i].net_pnl and float(trades[i].net_pnl) > 0
                                )
                        except:
                            continue

        if len(add_to_position_results) >= 10:
            add_wr = sum(add_to_position_results) / len(add_to_position_results) * 100
            if add_wr < self._win_rate - 10:
                self._add_insight(TradingInsight(
                    id="B08",
                    type=InsightType.REMINDER,
                    category=InsightCategory.BEHAVIOR,
                    priority=62,
                    title="连续交易同一标的风险",
                    description=f"短期内重复交易同一标的的胜率仅{add_wr:.0f}%，低于平均{self._win_rate:.0f}%",
                    suggestion="避免在一个标的上反复操作，每次交易应该有独立的判断",
                    data_points={
                        "add_position_win_rate": round(add_wr, 1),
                        "add_position_count": len(add_to_position_results),
                        "average_win_rate": round(self._win_rate, 1),
                    }
                ))

        # B09: Discipline score and performance (if available)
        positions_with_discipline = [
            p for p in self.positions
            if p.discipline_score is not None
        ]
        if len(positions_with_discipline) >= 20:
            high_discipline = [p for p in positions_with_discipline if float(p.discipline_score) >= 70]
            low_discipline = [p for p in positions_with_discipline if float(p.discipline_score) < 50]

            if len(high_discipline) >= 5 and len(low_discipline) >= 5:
                high_disc_winners = [p for p in high_discipline if p.net_pnl and float(p.net_pnl) > 0]
                low_disc_winners = [p for p in low_discipline if p.net_pnl and float(p.net_pnl) > 0]

                high_disc_wr = len(high_disc_winners) / len(high_discipline) * 100
                low_disc_wr = len(low_disc_winners) / len(low_discipline) * 100

                if high_disc_wr > low_disc_wr + 15:
                    self._add_insight(TradingInsight(
                        id="B09",
                        type=InsightType.REMINDER,
                        category=InsightCategory.BEHAVIOR,
                        priority=70,
                        title="纪律性影响表现",
                        description=f"高纪律性交易胜率{high_disc_wr:.0f}%，低纪律性仅{low_disc_wr:.0f}%",
                        suggestion="提高交易纪律性可以显著提升表现",
                        data_points={
                            "high_discipline_win_rate": round(high_disc_wr, 1),
                            "high_discipline_count": len(high_discipline),
                            "low_discipline_win_rate": round(low_disc_wr, 1),
                            "low_discipline_count": len(low_discipline),
                        }
                    ))

    # ========== 7. FEES ANALYSIS ==========

    def _analyze_fees(self):
        """
        F01: Fee erosion
        F02: Over-trading with high fees
        F03: Ineffective trades (too small P&L)
        """
        total_fees = sum(float(p.total_fees or 0) for p in self.positions)
        gross_profit = sum(float(p.net_pnl or 0) for p in self._winners)

        # F01: Fee erosion
        if gross_profit > 0:
            fee_erosion = total_fees / gross_profit * 100

            if fee_erosion > 10:
                self._add_insight(TradingInsight(
                    id="F01",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.FEES,
                    priority=72,
                    title="交易费用侵蚀利润",
                    description=f"总费用${total_fees:,.0f}占毛利润的{fee_erosion:.0f}%",
                    suggestion="考虑减少交易频率或选择费率更低的券商",
                    data_points={
                        "total_fees": round(total_fees, 2),
                        "gross_profit": round(gross_profit, 2),
                        "fee_erosion_pct": round(fee_erosion, 1),
                    }
                ))

        # F03: Ineffective trades (P&L between -$20 and $20)
        ineffective = [p for p in self.positions if p.net_pnl and -20 <= float(p.net_pnl) <= 20]
        ineffective_pct = len(ineffective) / len(self.positions) * 100 if self.positions else 0

        if ineffective_pct > 40:
            self._add_insight(TradingInsight(
                id="F03",
                type=InsightType.REMINDER,
                category=InsightCategory.FEES,
                priority=58,
                title="存在较多无效交易",
                description=f"{ineffective_pct:.0f}%的交易盈亏在±$20以内",
                suggestion="这些交易主要为券商贡献费用，建议提高交易质量",
                data_points={
                    "ineffective_count": len(ineffective),
                    "total_count": len(self.positions),
                    "ineffective_pct": round(ineffective_pct, 1),
                }
            ))

    # ========== 8. OPTIONS ANALYSIS ==========

    def _analyze_options(self):
        """
        O01: Call vs Put preference
        O02: High premium risk (for options)
        """
        options = [p for p in self.positions if p.is_option]

        if len(options) < 5:
            return

        # Simple call/put detection from symbol
        calls = [p for p in options if 'C' in p.symbol.upper()]
        puts = [p for p in options if 'P' in p.symbol.upper()]

        if len(calls) >= 3 and len(puts) >= 3:
            call_winners = [p for p in calls if p.net_pnl and float(p.net_pnl) > 0]
            put_winners = [p for p in puts if p.net_pnl and float(p.net_pnl) > 0]

            call_wr = len(call_winners) / len(calls) * 100
            put_wr = len(put_winners) / len(puts) * 100

            if abs(call_wr - put_wr) > 15:
                better = "Call" if call_wr > put_wr else "Put"
                worse = "Put" if call_wr > put_wr else "Call"
                better_wr = max(call_wr, put_wr)

                self._add_insight(TradingInsight(
                    id="O03",
                    type=InsightType.REMINDER,
                    category=InsightCategory.OPTIONS,
                    priority=60,
                    title=f"{better}期权更擅长",
                    description=f"{better}期权胜率{better_wr:.0f}%，而{worse}期权表现较弱",
                    suggestion=f"可以考虑增加{better}期权的交易比重",
                    data_points={
                        "call_count": len(calls),
                        "call_win_rate": round(call_wr, 1),
                        "put_count": len(puts),
                        "put_win_rate": round(put_wr, 1),
                    }
                ))

    # ========== 10. TREND ANALYSIS ==========

    def _analyze_trends(self):
        """
        P01: Win rate improvement
        P02: Performance deterioration
        """
        if len(self.positions) < 10:
            return

        # Split into first half and second half
        mid = len(self.positions) // 2
        first_half = self.positions[:mid]
        second_half = self.positions[mid:]

        first_winners = [p for p in first_half if p.net_pnl and float(p.net_pnl) > 0]
        second_winners = [p for p in second_half if p.net_pnl and float(p.net_pnl) > 0]

        first_wr = len(first_winners) / len(first_half) * 100 if first_half else 0
        second_wr = len(second_winners) / len(second_half) * 100 if second_half else 0

        wr_change = second_wr - first_wr

        # P01: Win rate improvement
        if wr_change > 10:
            self._add_insight(TradingInsight(
                id="P01",
                type=InsightType.STRENGTH,
                category=InsightCategory.TREND,
                priority=50,
                title="胜率正在提升",
                description=f"近期胜率{second_wr:.0f}%，比早期的{first_wr:.0f}%提升了{wr_change:.0f}个百分点",
                suggestion="继续保持，你正在进步！",
                data_points={
                    "early_win_rate": round(first_wr, 1),
                    "recent_win_rate": round(second_wr, 1),
                    "improvement": round(wr_change, 1),
                    "early_trades": len(first_half),
                    "recent_trades": len(second_half),
                }
            ))

        # P02: Performance deterioration
        elif wr_change < -10:
            self._add_insight(TradingInsight(
                id="P02",
                type=InsightType.PROBLEM,
                category=InsightCategory.TREND,
                priority=78,
                title="近期表现下滑",
                description=f"近期胜率{second_wr:.0f}%，比早期的{first_wr:.0f}%下降了{abs(wr_change):.0f}个百分点",
                suggestion="建议暂停交易，复盘近期交易，找出问题所在",
                data_points={
                    "early_win_rate": round(first_wr, 1),
                    "recent_win_rate": round(second_wr, 1),
                    "decline": round(abs(wr_change), 1),
                    "early_trades": len(first_half),
                    "recent_trades": len(second_half),
                }
            ))

        # Check for consecutive weekly losses (P02 variant)
        weekly_pnl = defaultdict(float)
        for p in self.positions:
            if p.close_date:
                week_start = p.close_date - timedelta(days=p.close_date.weekday())
                weekly_pnl[week_start] += float(p.net_pnl or 0)

        sorted_weeks = sorted(weekly_pnl.keys())
        if len(sorted_weeks) >= 3:
            recent_3_weeks = sorted_weeks[-3:]
            consecutive_negative = all(weekly_pnl[w] < 0 for w in recent_3_weeks)

            if consecutive_negative:
                total_loss = sum(weekly_pnl[w] for w in recent_3_weeks)
                self._add_insight(TradingInsight(
                    id="P02",
                    type=InsightType.PROBLEM,
                    category=InsightCategory.TREND,
                    priority=85,
                    title="连续3周亏损",
                    description=f"最近3周连续亏损，共亏损${abs(total_loss):,.0f}",
                    suggestion="建议暂停交易，深入分析原因后再恢复",
                    data_points={
                        "weeks_negative": 3,
                        "total_loss": round(total_loss, 2),
                    }
                ))
