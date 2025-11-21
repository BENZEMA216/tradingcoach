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

    def close(self):
        """关闭数据库连接"""
        if self.session:
            self.session.close()


# 创建全局实例（用于 Streamlit 缓存）
_loader = None


def get_data_loader() -> DataLoader:
    """获取数据加载器实例（单例模式）"""
    global _loader
    if _loader is None:
        _loader = DataLoader()
    return _loader
