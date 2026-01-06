"""
Data Loader Utility
数据加载工具

提供统一的数据库查询和数据加载接口。
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy import func

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.base import init_database, get_session
from src.models.trade import Trade
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'tradingcoach.db'


class DataLoader:
    """数据加载器"""

    def __init__(self):
        self.session = None
        self._connect_db()

    def _connect_db(self):
        """连接数据库"""
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found at: {DB_PATH}")

        init_database(f'sqlite:///{DB_PATH}', echo=False)
        self.session = get_session()

    def get_overview_stats(self) -> Dict:
        """获取概览统计"""
        stats = {
            'total_trades': self.session.query(Trade).count(),
            'total_positions': self.session.query(Position).count(),
            'closed_positions': self.session.query(Position).filter(
                Position.status == PositionStatus.CLOSED
            ).count(),
            'open_positions': self.session.query(Position).filter(
                Position.status == PositionStatus.OPEN
            ).count(),
            'scored_positions': self.session.query(Position).filter(
                Position.overall_score.isnot(None)
            ).count(),
            'total_market_data': self.session.query(MarketData).count(),
            'symbols_with_data': self.session.query(MarketData.symbol).distinct().count(),
            'total_symbols': self.session.query(Trade.symbol).distinct().count(),
        }

        # 计算总盈亏
        total_pnl = self.session.query(func.sum(Position.net_pnl)).filter(
            Position.status == PositionStatus.CLOSED
        ).scalar() or 0

        stats['total_net_pnl'] = float(total_pnl)

        # 计算胜率
        winning_positions = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.net_pnl > 0
        ).count()

        stats['win_rate'] = (winning_positions / max(stats['closed_positions'], 1)) * 100

        return stats

    def get_data_coverage(self) -> pd.DataFrame:
        """获取数据覆盖率"""
        # 获取所有交易的股票及交易次数
        trade_counts = self.session.query(
            Trade.symbol,
            func.count(Trade.id).label('trade_count'),
            func.min(Trade.filled_time).label('first_trade'),
            func.max(Trade.filled_time).label('last_trade')
        ).group_by(Trade.symbol).all()

        # 获取市场数据记录数
        market_data_counts = {}
        for symbol, count in self.session.query(
            MarketData.symbol,
            func.count(MarketData.id)
        ).group_by(MarketData.symbol).all():
            market_data_counts[symbol] = count

        # 构建DataFrame
        data = []
        for symbol, trade_count, first_trade, last_trade in trade_counts:
            data_count = market_data_counts.get(symbol, 0)
            has_data = data_count > 0

            data.append({
                'symbol': symbol,
                'trade_count': trade_count,
                'data_count': data_count,
                'has_data': has_data,
                'first_trade': first_trade,
                'last_trade': last_trade
            })

        df = pd.DataFrame(data)
        df = df.sort_values('trade_count', ascending=False)

        return df

    def get_quality_scores(self) -> pd.DataFrame:
        """获取质量评分数据"""
        positions = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.overall_score.isnot(None)
        ).all()

        data = []
        for pos in positions:
            data.append({
                'id': pos.id,
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'open_price': float(pos.open_price),
                'close_price': float(pos.close_price) if pos.close_price else None,
                'net_pnl': float(pos.net_pnl) if pos.net_pnl else 0,
                'net_pnl_pct': float(pos.net_pnl_pct) if pos.net_pnl_pct else 0,
                'overall_score': float(pos.overall_score),
                'grade': pos.score_grade,
                'entry_score': float(pos.entry_quality_score) if pos.entry_quality_score else 0,
                'exit_score': float(pos.exit_quality_score) if pos.exit_quality_score else 0,
                'trend_score': float(pos.trend_quality_score) if pos.trend_quality_score else 0,
                'risk_score': float(pos.risk_mgmt_score) if pos.risk_mgmt_score else 0,
                'open_time': pos.open_time,
                'close_time': pos.close_time,
                'holding_days': pos.holding_period_days
            })

        df = pd.DataFrame(data)
        return df

    def get_symbol_trades(self, symbol: str) -> List[Trade]:
        """获取特定股票的所有交易"""
        trades = self.session.query(Trade).filter(
            Trade.symbol == symbol
        ).order_by(Trade.filled_time).all()

        return trades

    def get_symbol_positions(self, symbol: str) -> List[Position]:
        """获取特定股票的所有持仓"""
        positions = self.session.query(Position).filter(
            Position.symbol == symbol
        ).order_by(Position.open_time).all()

        return positions

    def get_market_data(self, symbol: str,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """获取市场数据"""
        query = self.session.query(MarketData).filter(
            MarketData.symbol == symbol
        )

        if start_date:
            query = query.filter(MarketData.date >= start_date.date())
        if end_date:
            query = query.filter(MarketData.date <= end_date.date())

        data = query.order_by(MarketData.date).all()

        if not data:
            return pd.DataFrame()

        df_data = []
        for md in data:
            df_data.append({
                'date': md.timestamp if hasattr(md, 'timestamp') else md.date,
                'open': float(md.open) if md.open else None,
                'high': float(md.high) if md.high else None,
                'low': float(md.low) if md.low else None,
                'close': float(md.close),
                'volume': md.volume if md.volume else 0,
                'rsi': float(md.rsi_14) if md.rsi_14 else None,
                'macd': float(md.macd) if md.macd else None,
                'macd_signal': float(md.macd_signal) if md.macd_signal else None,
                'macd_hist': float(md.macd_hist) if md.macd_hist else None,
                'ma_5': float(md.ma_5) if md.ma_5 else None,
                'ma_20': float(md.ma_20) if md.ma_20 else None,
                'ma_50': float(md.ma_50) if md.ma_50 else None,
                'bb_upper': float(md.bb_upper) if md.bb_upper else None,
                'bb_middle': float(md.bb_middle) if md.bb_middle else None,
                'bb_lower': float(md.bb_lower) if md.bb_lower else None,
                'atr': float(md.atr_14) if md.atr_14 else None
            })

        df = pd.DataFrame(df_data)
        return df

    def get_all_symbols(self) -> List[str]:
        """获取所有股票代码"""
        symbols = self.session.query(Trade.symbol).distinct().all()
        return sorted([s[0] for s in symbols])

    def get_symbols_with_scores(self) -> List[str]:
        """获取有评分的股票代码"""
        symbols = self.session.query(Position.symbol).filter(
            Position.overall_score.isnot(None)
        ).distinct().all()
        return sorted([s[0] for s in symbols])

    def get_symbols_with_market_data(self) -> List[str]:
        """获取有市场数据的股票代码"""
        symbols = self.session.query(MarketData.symbol).distinct().all()
        return sorted([s[0] for s in symbols])

    def get_position_by_id(self, position_id: int) -> Optional[Position]:
        """根据ID获取持仓"""
        return self.session.query(Position).filter(
            Position.id == position_id
        ).first()

    def get_positions_with_trades(self) -> pd.DataFrame:
        """
        获取所有已平仓持仓及其关联交易信息

        返回包含开仓/平仓交易ID的完整DataFrame
        """
        positions = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.open_time.desc()).all()

        data = []
        for pos in positions:
            # 获取关联的交易
            trades = self.session.query(Trade).filter(
                Trade.position_id == pos.id
            ).order_by(Trade.filled_time).all()

            # 分离买入和卖出交易
            buy_trades = [t for t in trades if t.direction in ['买入', 'buy', 'buy_to_open']]
            sell_trades = [t for t in trades if t.direction in ['卖出', 'sell', 'sell_to_close']]

            # 提取交易ID
            buy_trade_ids = ','.join([str(t.id) for t in buy_trades]) if buy_trades else ''
            sell_trade_ids = ','.join([str(t.id) for t in sell_trades]) if sell_trades else ''

            data.append({
                # 基本信息
                'id': pos.id,
                'symbol': pos.symbol,
                'symbol_name': pos.symbol_name,
                'direction': pos.direction,
                'quantity': pos.quantity,

                # 价格信息
                'open_price': float(pos.open_price) if pos.open_price else None,
                'close_price': float(pos.close_price) if pos.close_price else None,

                # 时间信息
                'open_time': pos.open_time,
                'close_time': pos.close_time,
                'holding_days': pos.holding_period_days,

                # 费用信息
                'open_fee': float(pos.open_fee) if pos.open_fee else 0,
                'close_fee': float(pos.close_fee) if pos.close_fee else 0,
                'total_fees': float(pos.total_fees) if pos.total_fees else 0,

                # 盈亏信息
                'realized_pnl': float(pos.realized_pnl) if pos.realized_pnl else 0,
                'net_pnl': float(pos.net_pnl) if pos.net_pnl else 0,
                'net_pnl_pct': float(pos.net_pnl_pct) if pos.net_pnl_pct else 0,

                # 风险指标
                'mae_pct': float(pos.mae_pct) if pos.mae_pct else None,
                'mfe_pct': float(pos.mfe_pct) if pos.mfe_pct else None,
                'risk_reward_ratio': float(pos.risk_reward_ratio) if pos.risk_reward_ratio else None,

                # 评分信息
                'overall_score': float(pos.overall_score) if pos.overall_score else None,
                'grade': pos.score_grade,
                'entry_score': float(pos.entry_quality_score) if pos.entry_quality_score else None,
                'exit_score': float(pos.exit_quality_score) if pos.exit_quality_score else None,
                'trend_score': float(pos.trend_quality_score) if pos.trend_quality_score else None,
                'risk_score': float(pos.risk_mgmt_score) if pos.risk_mgmt_score else None,

                # FIFO 交易配对
                'buy_trade_ids': buy_trade_ids,
                'sell_trade_ids': sell_trade_ids,
                'trade_count': len(trades)
            })

        return pd.DataFrame(data)

    def get_trades_by_position(self, position_id: int) -> List[Dict]:
        """
        获取指定持仓的所有关联交易详情

        返回交易列表，包含完整的交易信息
        """
        trades = self.session.query(Trade).filter(
            Trade.position_id == position_id
        ).order_by(Trade.filled_time).all()

        result = []
        for t in trades:
            result.append({
                'id': t.id,
                'direction': t.direction,
                'symbol': t.symbol,
                'quantity': t.filled_quantity,
                'price': float(t.filled_price) if t.filled_price else None,
                'amount': float(t.filled_amount) if t.filled_amount else None,
                'fee': float(t.filled_fee) if t.filled_fee else 0,
                'time': t.filled_time,
                'matched_trade_id': t.matched_trade_id
            })

        return result

    def close(self):
        """关闭数据库连接"""
        if self.session:
            self.session.close()

    # ================================================================
    # Dashboard 专用方法
    # ================================================================

    def get_dashboard_kpis(self, days: Optional[int] = None) -> Dict:
        """
        获取 Dashboard KPI 数据

        Args:
            days: 限制最近N天的数据，None表示全部

        Returns:
            Dict: 包含 total_pnl, win_rate, avg_score, trade_count 等
        """
        query = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        )

        if days:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)
            query = query.filter(Position.close_time >= cutoff)

        positions = query.all()

        if not positions:
            return {
                'total_pnl': 0,
                'win_rate': 0,
                'avg_score': 0,
                'trade_count': 0,
                'total_fees': 0,
                'avg_holding_days': 0,
            }

        total_pnl = sum(float(p.net_pnl or 0) for p in positions)
        winners = sum(1 for p in positions if (p.net_pnl or 0) > 0)
        win_rate = (winners / len(positions)) * 100 if positions else 0

        scores = [float(p.overall_score) for p in positions if p.overall_score]
        avg_score = sum(scores) / len(scores) if scores else 0

        total_fees = sum(float(p.total_fees or 0) for p in positions)

        holding_days = [p.holding_period_days for p in positions if p.holding_period_days]
        avg_holding = sum(holding_days) / len(holding_days) if holding_days else 0

        return {
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_score': avg_score,
            'trade_count': len(positions),
            'total_fees': total_fees,
            'avg_holding_days': avg_holding,
        }

    def get_equity_curve_data(self, days: Optional[int] = None) -> pd.DataFrame:
        """
        获取权益曲线数据

        Args:
            days: 限制最近N天

        Returns:
            DataFrame: 包含 close_date, net_pnl, cumulative_pnl
        """
        query = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.close_time.isnot(None)
        )

        if days:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)
            query = query.filter(Position.close_time >= cutoff)

        positions = query.order_by(Position.close_time).all()

        if not positions:
            return pd.DataFrame()

        data = []
        cumulative = 0
        for pos in positions:
            pnl = float(pos.net_pnl or 0)
            cumulative += pnl
            data.append({
                'close_date': pos.close_time.date() if pos.close_time else None,
                'close_time': pos.close_time,
                'symbol': pos.symbol,
                'net_pnl': pnl,
                'cumulative_pnl': cumulative,
                'is_winner': pnl > 0,
            })

        return pd.DataFrame(data)

    def get_recent_trades(self, limit: int = 5) -> pd.DataFrame:
        """
        获取最近的交易

        Args:
            limit: 返回条数

        Returns:
            DataFrame: 最近的已平仓持仓
        """
        positions = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_time.desc()).limit(limit).all()

        data = []
        for pos in positions:
            data.append({
                'id': pos.id,
                'symbol': pos.symbol,
                'close_date': pos.close_time.date() if pos.close_time else None,
                'net_pnl': float(pos.net_pnl or 0),
                'net_pnl_pct': float(pos.net_pnl_pct or 0),
                'score': float(pos.overall_score) if pos.overall_score else None,
                'grade': pos.score_grade,
                'holding_days': pos.holding_period_days,
            })

        return pd.DataFrame(data)

    def get_needs_review_trades(self, limit: int = 5) -> pd.DataFrame:
        """
        获取需要复盘的交易（低评分+亏损）

        Args:
            limit: 返回条数

        Returns:
            DataFrame: 需要复盘的持仓
        """
        # 优先级: 1) 亏损+低评分  2) 亏损  3) 低评分
        positions = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            (Position.net_pnl < 0) | (Position.overall_score < 60)
        ).order_by(
            # 亏损金额越大越靠前，评分越低越靠前
            Position.net_pnl.asc(),
            Position.overall_score.asc()
        ).limit(limit).all()

        data = []
        for pos in positions:
            data.append({
                'id': pos.id,
                'symbol': pos.symbol,
                'close_date': pos.close_time.date() if pos.close_time else None,
                'net_pnl': float(pos.net_pnl or 0),
                'net_pnl_pct': float(pos.net_pnl_pct or 0),
                'score': float(pos.overall_score) if pos.overall_score else None,
                'grade': pos.score_grade,
                'holding_days': pos.holding_period_days,
                'reason': self._get_review_reason(pos),
            })

        return pd.DataFrame(data)

    def _get_review_reason(self, pos: Position) -> str:
        """获取需要复盘的原因"""
        reasons = []
        if pos.net_pnl and float(pos.net_pnl) < 0:
            reasons.append("亏损")
        if pos.overall_score and float(pos.overall_score) < 60:
            reasons.append("低评分")
        return " + ".join(reasons) if reasons else "需关注"

    def get_strategy_breakdown(self) -> pd.DataFrame:
        """
        获取策略分布数据

        Returns:
            DataFrame: 按策略类型分组的统计
        """
        positions = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        if not positions:
            return pd.DataFrame()

        # 按策略分组
        strategy_stats = {}
        for pos in positions:
            strategy = pos.strategy_type or 'unknown'
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'count': 0,
                    'total_pnl': 0,
                    'winners': 0,
                    'total_score': 0,
                    'score_count': 0,
                }

            stats = strategy_stats[strategy]
            stats['count'] += 1
            stats['total_pnl'] += float(pos.net_pnl or 0)
            if pos.net_pnl and float(pos.net_pnl) > 0:
                stats['winners'] += 1
            if pos.overall_score:
                stats['total_score'] += float(pos.overall_score)
                stats['score_count'] += 1

        # 转换为 DataFrame
        data = []
        strategy_names = {
            'trend': '趋势跟踪',
            'mean_reversion': '均值回归',
            'breakout': '突破交易',
            'range': '区间交易',
            'momentum': '动量交易',
            'unknown': '未分类',
        }

        for strategy, stats in strategy_stats.items():
            data.append({
                'strategy': strategy,
                'strategy_name': strategy_names.get(strategy, strategy),
                'count': stats['count'],
                'total_pnl': stats['total_pnl'],
                'avg_pnl': stats['total_pnl'] / stats['count'] if stats['count'] > 0 else 0,
                'win_rate': (stats['winners'] / stats['count'] * 100) if stats['count'] > 0 else 0,
                'avg_score': stats['total_score'] / stats['score_count'] if stats['score_count'] > 0 else 0,
            })

        df = pd.DataFrame(data)
        df = df.sort_values('count', ascending=False)
        return df

    def get_daily_pnl(self, year: Optional[int] = None, month: Optional[int] = None) -> pd.DataFrame:
        """
        获取每日盈亏汇总

        Args:
            year: 年份
            month: 月份

        Returns:
            DataFrame: 每日盈亏
        """
        query = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.close_time.isnot(None)
        )

        if year:
            from sqlalchemy import extract
            query = query.filter(extract('year', Position.close_time) == year)
        if month:
            from sqlalchemy import extract
            query = query.filter(extract('month', Position.close_time) == month)

        positions = query.all()

        if not positions:
            return pd.DataFrame()

        # 按日期分组
        daily_data = {}
        for pos in positions:
            date = pos.close_time.date()
            if date not in daily_data:
                daily_data[date] = {'pnl': 0, 'count': 0, 'winners': 0}

            daily_data[date]['pnl'] += float(pos.net_pnl or 0)
            daily_data[date]['count'] += 1
            if pos.net_pnl and float(pos.net_pnl) > 0:
                daily_data[date]['winners'] += 1

        data = []
        for date, stats in sorted(daily_data.items()):
            data.append({
                'date': date,
                'pnl': stats['pnl'],
                'trade_count': stats['count'],
                'winners': stats['winners'],
                'win_rate': (stats['winners'] / stats['count'] * 100) if stats['count'] > 0 else 0,
            })

        return pd.DataFrame(data)

    def get_all_strategies(self) -> List[str]:
        """获取所有策略类型"""
        strategies = self.session.query(Position.strategy_type).filter(
            Position.strategy_type.isnot(None)
        ).distinct().all()
        return sorted([s[0] for s in strategies if s[0]])

    def get_all_grades(self) -> List[str]:
        """获取所有评分等级"""
        grades = self.session.query(Position.score_grade).filter(
            Position.score_grade.isnot(None)
        ).distinct().all()
        return sorted([g[0] for g in grades if g[0]])

    def get_positions_with_scores(self) -> pd.DataFrame:
        """
        获取所有已平仓持仓及其评分信息

        Returns:
            DataFrame: 包含持仓信息和评分的完整数据
        """
        positions = self.session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_time.desc()).all()

        data = []
        for pos in positions:
            data.append({
                # 基本信息
                'id': pos.id,
                'symbol': pos.symbol,
                'symbol_name': pos.symbol_name,
                'direction': pos.direction,
                'quantity': pos.quantity,
                'strategy_type': pos.strategy_type,

                # 价格信息
                'open_price': float(pos.open_price) if pos.open_price else None,
                'close_price': float(pos.close_price) if pos.close_price else None,

                # 时间信息
                'open_time': pos.open_time,
                'close_time': pos.close_time,
                'open_date': pos.open_time.date() if pos.open_time else None,
                'close_date': pos.close_time.date() if pos.close_time else None,
                'holding_days': pos.holding_period_days,

                # 费用信息
                'open_fee': float(pos.open_fee) if pos.open_fee else 0,
                'close_fee': float(pos.close_fee) if pos.close_fee else 0,
                'total_fees': float(pos.total_fees) if pos.total_fees else 0,

                # 盈亏信息
                'realized_pnl': float(pos.realized_pnl) if pos.realized_pnl else 0,
                'net_pnl': float(pos.net_pnl) if pos.net_pnl else 0,
                'net_pnl_pct': float(pos.net_pnl_pct) if pos.net_pnl_pct else 0,

                # 风险指标
                'mae_pct': float(pos.mae_pct) if pos.mae_pct else None,
                'mfe_pct': float(pos.mfe_pct) if pos.mfe_pct else None,
                'risk_reward_ratio': float(pos.risk_reward_ratio) if pos.risk_reward_ratio else None,

                # 评分信息
                'overall_score': float(pos.overall_score) if pos.overall_score else None,
                'grade': pos.score_grade,
                'entry_score': float(pos.entry_quality_score) if pos.entry_quality_score else None,
                'exit_score': float(pos.exit_quality_score) if pos.exit_quality_score else None,
                'trend_score': float(pos.trend_quality_score) if pos.trend_quality_score else None,
                'risk_score': float(pos.risk_mgmt_score) if pos.risk_mgmt_score else None,
            })

        return pd.DataFrame(data)


# 创建全局实例（用于 Streamlit 缓存）
_loader = None


def get_data_loader() -> DataLoader:
    """获取数据加载器实例（单例模式）"""
    global _loader
    if _loader is None:
        _loader = DataLoader()
    return _loader
