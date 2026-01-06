"""
MarketEnvironmentScorer - 市场环境评分器

评估交易时的市场环境质量:
1. VIX波动率水平 (30%)
2. 大盘趋势 (35%)
3. 板块强弱 (25%)
4. 事件日检测 (10%)
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class MarketEnvScore:
    """市场环境评分结果"""
    total_score: float  # 综合评分 0-100
    vix_score: float  # VIX评分 0-100
    trend_score: float  # 趋势评分 0-100
    sector_score: float  # 板块评分 0-100
    event_score: float  # 事件评分 0-100
    details: Dict[str, Any]  # 详细信息


class MarketEnvironmentScorer:
    """
    市场环境评分器

    根据交易发生时的市场状态给出环境评分:
    - VIX低位 = 市场平静，风险较低
    - 大盘趋势顺应 = 顺势交易加分
    - 板块强势 = 选股正确加分
    - 避开事件日 = 风险控制加分
    """

    # 权重配置
    WEIGHT_VIX = 0.30
    WEIGHT_TREND = 0.35
    WEIGHT_SECTOR = 0.25
    WEIGHT_EVENT = 0.10

    # VIX 阈值
    VIX_LOW = 15
    VIX_NORMAL = 20
    VIX_ELEVATED = 25
    VIX_HIGH = 30

    # FOMC 会议日期 (2024-2025)
    FOMC_DATES = [
        # 2024
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
        "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
        # 2025
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
        "2025-07-30", "2025-09-17", "2025-11-05", "2025-12-17",
    ]

    def __init__(self):
        """初始化市场环境评分器"""
        self._fomc_dates = set(
            datetime.strptime(d, "%Y-%m-%d").date()
            for d in self.FOMC_DATES
        )
        logger.info("MarketEnvironmentScorer initialized")

    def score(
        self,
        trade_date: date,
        direction: str,
        symbol: str,
        market_snapshot: Optional[Dict] = None,
        market_data: Optional[Any] = None
    ) -> MarketEnvScore:
        """
        计算市场环境评分

        Args:
            trade_date: 交易日期
            direction: 交易方向 ('long' 或 'short')
            symbol: 交易标的
            market_snapshot: 市场快照数据 (VIX, SPY等)
            market_data: 标的市场数据

        Returns:
            MarketEnvScore: 评分结果
        """
        details = {}
        is_long = direction in ['long', 'buy', 'buy_to_open']

        # 1. VIX评分 (30%)
        vix_score, vix_details = self._score_vix(market_snapshot, is_long)
        details['vix'] = vix_details

        # 2. 大盘趋势评分 (35%)
        trend_score, trend_details = self._score_market_trend(
            market_snapshot, is_long
        )
        details['trend'] = trend_details

        # 3. 板块强弱评分 (25%)
        sector_score, sector_details = self._score_sector_strength(
            symbol, market_snapshot, market_data, is_long
        )
        details['sector'] = sector_details

        # 4. 事件日评分 (10%)
        event_score, event_details = self._score_event_day(trade_date)
        details['event'] = event_details

        # 计算综合评分
        total_score = (
            vix_score * self.WEIGHT_VIX +
            trend_score * self.WEIGHT_TREND +
            sector_score * self.WEIGHT_SECTOR +
            event_score * self.WEIGHT_EVENT
        )

        return MarketEnvScore(
            total_score=round(total_score, 2),
            vix_score=vix_score,
            trend_score=trend_score,
            sector_score=sector_score,
            event_score=event_score,
            details=details
        )

    def _score_vix(
        self,
        snapshot: Optional[Dict],
        is_long: bool
    ) -> tuple[float, Dict]:
        """
        VIX波动率评分

        低VIX = 市场平静，适合趋势交易
        高VIX = 市场恐慌，适合逆向/做空
        """
        if not snapshot or 'vix_close' not in snapshot:
            return 70.0, {'status': 'no_data', 'vix': None}

        vix = snapshot['vix_close']

        if vix is None:
            return 70.0, {'status': 'no_data', 'vix': None}

        details = {'vix': vix}

        if is_long:
            # 做多: 低VIX更有利
            if vix < self.VIX_LOW:
                score = 90
                details['status'] = 'very_low'
                details['description'] = '极低波动，市场平静'
            elif vix < self.VIX_NORMAL:
                score = 75
                details['status'] = 'low'
                details['description'] = '低波动，正常市场'
            elif vix < self.VIX_ELEVATED:
                score = 60
                details['status'] = 'normal'
                details['description'] = '中等波动'
            elif vix < self.VIX_HIGH:
                score = 40
                details['status'] = 'elevated'
                details['description'] = '波动偏高，风险增加'
            else:
                score = 30
                details['status'] = 'high'
                details['description'] = '高波动，做多风险大'
        else:
            # 做空: 高VIX可能更有利 (恐慌情绪)
            if vix > self.VIX_HIGH:
                score = 85
                details['status'] = 'high'
                details['description'] = '高波动，做空机会'
            elif vix > self.VIX_ELEVATED:
                score = 75
                details['status'] = 'elevated'
                details['description'] = '波动升高'
            elif vix > self.VIX_NORMAL:
                score = 60
                details['status'] = 'normal'
                details['description'] = '中等波动'
            else:
                score = 45
                details['status'] = 'low'
                details['description'] = '低波动做空，逆市'

        return score, details

    def _score_market_trend(
        self,
        snapshot: Optional[Dict],
        is_long: bool
    ) -> tuple[float, Dict]:
        """
        大盘趋势评分

        使用SPY的均线关系和RSI判断趋势
        """
        if not snapshot:
            return 70.0, {'status': 'no_data'}

        spy_close = snapshot.get('spy_close')
        spy_ma5 = snapshot.get('spy_ma5')
        spy_ma20 = snapshot.get('spy_ma20')
        spy_ma50 = snapshot.get('spy_ma50')
        spy_rsi = snapshot.get('spy_rsi_14')
        spy_change = snapshot.get('spy_change_pct')
        market_trend = snapshot.get('market_trend')

        details = {
            'spy_close': spy_close,
            'spy_ma5': spy_ma5,
            'spy_ma20': spy_ma20,
            'market_trend': market_trend
        }

        # 计算确认信号数量
        confirmations = 0
        total_checks = 0

        # 1. 均线排列
        if spy_ma5 and spy_ma20 and spy_ma50:
            total_checks += 1
            if is_long:
                if spy_ma5 > spy_ma20 > spy_ma50:
                    confirmations += 1
                    details['ma_status'] = 'bullish_alignment'
            else:
                if spy_ma5 < spy_ma20 < spy_ma50:
                    confirmations += 1
                    details['ma_status'] = 'bearish_alignment'

        # 2. 价格相对均线位置
        if spy_close and spy_ma20:
            total_checks += 1
            if is_long and spy_close > spy_ma20:
                confirmations += 1
                details['price_vs_ma'] = 'above_ma20'
            elif not is_long and spy_close < spy_ma20:
                confirmations += 1
                details['price_vs_ma'] = 'below_ma20'

        # 3. RSI位置
        if spy_rsi:
            total_checks += 1
            if is_long and spy_rsi > 50 and spy_rsi < 70:
                confirmations += 1
                details['rsi_status'] = 'bullish_momentum'
            elif not is_long and spy_rsi < 50 and spy_rsi > 30:
                confirmations += 1
                details['rsi_status'] = 'bearish_momentum'

        # 4. 当日涨跌
        if spy_change is not None:
            total_checks += 1
            if is_long and spy_change > 0:
                confirmations += 1
            elif not is_long and spy_change < 0:
                confirmations += 1
            details['spy_change'] = spy_change

        # 计算评分
        if total_checks == 0:
            return 70.0, details

        confirm_ratio = confirmations / total_checks
        details['confirm_ratio'] = confirm_ratio

        if confirm_ratio >= 0.75:
            score = 95
            details['trend_alignment'] = 'strong'
        elif confirm_ratio >= 0.5:
            score = 80
            details['trend_alignment'] = 'moderate'
        elif confirm_ratio >= 0.25:
            score = 60
            details['trend_alignment'] = 'weak'
        else:
            score = 40
            details['trend_alignment'] = 'contrary'

        return score, details

    def _score_sector_strength(
        self,
        symbol: str,
        snapshot: Optional[Dict],
        market_data: Optional[Any],
        is_long: bool
    ) -> tuple[float, Dict]:
        """
        板块强弱评分

        比较标的与大盘的相对强度
        """
        details = {'symbol': symbol}

        # 如果有市场数据，计算相对强度
        if market_data and snapshot and snapshot.get('spy_change_pct') is not None:
            spy_change = snapshot['spy_change_pct']

            # 获取标的涨跌幅
            symbol_change = None
            if hasattr(market_data, 'change_pct') and market_data.change_pct is not None:
                symbol_change = float(market_data.change_pct)
            elif hasattr(market_data, 'close') and hasattr(market_data, 'open'):
                if market_data.open and market_data.close:
                    symbol_change = ((float(market_data.close) - float(market_data.open))
                                   / float(market_data.open) * 100)

            if symbol_change is not None:
                relative_strength = symbol_change - spy_change
                details['symbol_change'] = symbol_change
                details['spy_change'] = spy_change
                details['relative_strength'] = relative_strength

                if is_long:
                    # 做多: 相对强度越高越好
                    if relative_strength > 2:
                        score = 95
                        details['status'] = 'very_strong'
                    elif relative_strength > 1:
                        score = 85
                        details['status'] = 'strong'
                    elif relative_strength > 0:
                        score = 75
                        details['status'] = 'slightly_strong'
                    elif relative_strength > -1:
                        score = 60
                        details['status'] = 'neutral'
                    else:
                        score = 45
                        details['status'] = 'weak'
                else:
                    # 做空: 相对强度越低越好
                    if relative_strength < -2:
                        score = 95
                        details['status'] = 'very_weak'
                    elif relative_strength < -1:
                        score = 85
                        details['status'] = 'weak'
                    elif relative_strength < 0:
                        score = 75
                        details['status'] = 'slightly_weak'
                    elif relative_strength < 1:
                        score = 60
                        details['status'] = 'neutral'
                    else:
                        score = 45
                        details['status'] = 'strong'

                return score, details

        # 无法计算相对强度，返回默认分
        return 70.0, {'status': 'no_data'}

    def _score_event_day(self, trade_date: date) -> tuple[float, Dict]:
        """
        事件日评分

        检查是否在FOMC、期权到期日等特殊日期交易
        """
        details = {'trade_date': str(trade_date)}
        events = []

        # 转换日期格式
        if isinstance(trade_date, datetime):
            trade_date = trade_date.date()

        # 检查FOMC日
        if trade_date in self._fomc_dates:
            events.append('FOMC')

        # 检查FOMC前一天
        fomc_eve = trade_date + timedelta(days=1)
        if fomc_eve in self._fomc_dates:
            events.append('FOMC_Eve')

        # 检查期权到期日 (每月第三个周五)
        if self._is_opex_day(trade_date):
            events.append('OPEX')

        # 检查季度期权到期日 (3/6/9/12月)
        if self._is_quad_witching(trade_date):
            events.append('Quad_Witching')

        details['events'] = events

        if not events:
            score = 90
            details['status'] = 'clean'
            details['description'] = '无重大事件'
        elif 'Quad_Witching' in events:
            score = 40
            details['status'] = 'high_risk'
            details['description'] = '四重到期日，高波动风险'
        elif 'FOMC' in events:
            score = 50
            details['status'] = 'risky'
            details['description'] = 'FOMC会议日，方向不确定'
        elif 'FOMC_Eve' in events:
            score = 60
            details['status'] = 'cautious'
            details['description'] = 'FOMC前夕，市场观望'
        elif 'OPEX' in events:
            score = 65
            details['status'] = 'moderate_risk'
            details['description'] = '期权到期日，波动可能增加'
        else:
            score = 75
            details['status'] = 'minor_event'

        return score, details

    def _is_opex_day(self, d: date) -> bool:
        """检查是否为月度期权到期日 (第三个周五)"""
        if d.weekday() != 4:  # 不是周五
            return False

        # 计算该月第三个周五
        first_day = d.replace(day=1)
        first_friday = first_day + timedelta(days=(4 - first_day.weekday() + 7) % 7)
        third_friday = first_friday + timedelta(weeks=2)

        return d == third_friday

    def _is_quad_witching(self, d: date) -> bool:
        """检查是否为四重到期日 (3/6/9/12月第三个周五)"""
        if d.month not in [3, 6, 9, 12]:
            return False
        return self._is_opex_day(d)

    def get_market_snapshot(
        self,
        session: Session,
        trade_date: date
    ) -> Optional[Dict]:
        """
        从数据库获取市场快照

        Args:
            session: 数据库会话
            trade_date: 交易日期

        Returns:
            市场快照数据字典
        """
        try:
            from sqlalchemy import text

            # 查询 market_snapshots 表
            result = session.execute(
                text("""
                    SELECT * FROM market_snapshots
                    WHERE date = :date
                """),
                {'date': trade_date}
            ).fetchone()

            if result:
                return dict(result._mapping)

            # 如果没有快照，尝试从 market_data 表获取 SPY 数据
            spy_data = session.execute(
                text("""
                    SELECT close, ma_5, ma_20, ma_50, rsi_14
                    FROM market_data
                    WHERE symbol = 'SPY' AND date = :date
                """),
                {'date': trade_date}
            ).fetchone()

            if spy_data:
                return {
                    'spy_close': spy_data[0],
                    'spy_ma5': spy_data[1],
                    'spy_ma20': spy_data[2],
                    'spy_ma50': spy_data[3],
                    'spy_rsi_14': spy_data[4],
                }

            return None

        except Exception as e:
            logger.warning(f"Failed to get market snapshot for {trade_date}: {e}")
            return None

    def __repr__(self) -> str:
        return (
            f"MarketEnvironmentScorer("
            f"vix={self.WEIGHT_VIX:.0%}, "
            f"trend={self.WEIGHT_TREND:.0%}, "
            f"sector={self.WEIGHT_SECTOR:.0%}, "
            f"event={self.WEIGHT_EVENT:.0%})"
        )
