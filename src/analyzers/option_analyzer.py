"""
OptionTradeAnalyzer - 期权交易分析器

基于正股数据对期权交易进行深度分析：
1. 入场环境分析 - 正股技术指标、Moneyness、趋势方向
2. 正股走势分析 - 持有期间正股表现、是否触及行权价
3. Greeks影响估算 - Delta、Theta的影响估算
4. 策略评估 - 到期日选择、行权价选择、入场/出场时机
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.utils.option_parser import OptionParser, parse_option, is_option, get_underlying

logger = logging.getLogger(__name__)


class OptionTradeAnalyzer:
    """
    期权交易分析器

    使用正股OHLCV数据和期权交易记录进行分析，
    无需期权本身的市场数据
    """

    # Moneyness 分类阈值
    MONEYNESS_ITM_THRESHOLD = 0.02   # ITM: moneyness > 2%
    MONEYNESS_ATM_THRESHOLD = 0.02   # ATM: -2% < moneyness < 2%
    MONEYNESS_OTM_THRESHOLD = -0.02  # OTM: moneyness < -2%

    # DTE (Days to Expiry) 分类
    DTE_SHORT = 7      # 短期: < 7天
    DTE_MEDIUM = 30    # 中期: 7-30天
    DTE_LONG = 90      # 长期: 30-90天

    # Delta 估算值
    ESTIMATED_DELTA = {
        'deep_itm_call': 0.85,
        'itm_call': 0.70,
        'atm_call': 0.50,
        'otm_call': 0.30,
        'deep_otm_call': 0.15,
        'deep_itm_put': -0.85,
        'itm_put': -0.70,
        'atm_put': -0.50,
        'otm_put': -0.30,
        'deep_otm_put': -0.15,
    }

    def __init__(self, session: Session):
        """
        初始化期权分析器

        Args:
            session: 数据库会话
        """
        self.session = session
        logger.info("OptionTradeAnalyzer initialized")

    def analyze_position(self, position: Position) -> Dict:
        """
        分析单个期权持仓

        Args:
            position: Position对象（必须是期权）

        Returns:
            Dict: 完整的期权分析结果
        """
        if not is_option(position.symbol):
            logger.warning(f"Position {position.id} is not an option")
            return {'error': 'Not an option position'}

        # 解析期权合约信息
        option_info = parse_option(position.symbol)
        if not option_info:
            logger.error(f"Failed to parse option symbol: {position.symbol}")
            return {'error': 'Failed to parse option symbol'}

        # 获取正股市场数据
        underlying_symbol = option_info['underlying']
        entry_md = self._get_underlying_market_data(underlying_symbol, position.open_time)
        exit_md = self._get_underlying_market_data(underlying_symbol, position.close_time) if position.close_time else None

        # 构建分析结果
        result = {
            'position_id': position.id,
            'option_symbol': position.symbol,
            'option_info': self._format_option_info(option_info),
            'entry_context': self.analyze_entry_context(position, option_info, entry_md),
            'underlying_movement': self.analyze_underlying_movement(position, option_info, entry_md, exit_md),
            'greeks_impact': self.estimate_greeks_impact(position, option_info, entry_md, exit_md),
            'strategy_evaluation': self.evaluate_option_strategy(position, option_info, entry_md, exit_md),
        }

        # 计算期权专属评分
        result['option_scores'] = self.calculate_option_scores(result)

        return result

    def _format_option_info(self, option_info: Dict) -> Dict:
        """格式化期权信息"""
        return {
            'underlying': option_info['underlying'],
            'expiry_date': option_info['expiry_date'].strftime('%Y-%m-%d'),
            'option_type': option_info['option_type'],  # 'call' or 'put'
            'strike': float(option_info['strike']),
            'readable': OptionParser.get_option_info_string(option_info['raw_symbol'])
        }

    def _get_underlying_market_data(
        self,
        symbol: str,
        timestamp: Optional[datetime]
    ) -> Optional[MarketData]:
        """获取标的股票的市场数据"""
        if not timestamp:
            return None

        target_date = timestamp.date() if hasattr(timestamp, 'date') else timestamp

        # 查找当天或最近的市场数据
        market_data = self.session.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.date == target_date
        ).first()

        if not market_data:
            # 尝试查找最近的数据
            market_data = self.session.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.date <= target_date
            ).order_by(MarketData.date.desc()).first()

        return market_data

    # ==================== 入场环境分析 ====================

    def analyze_entry_context(
        self,
        position: Position,
        option_info: Dict,
        entry_md: Optional[MarketData]
    ) -> Dict:
        """
        分析期权入场时的环境

        Args:
            position: 持仓
            option_info: 解析后的期权信息
            entry_md: 入场时正股市场数据

        Returns:
            Dict: 入场环境分析结果
        """
        result = {
            'has_market_data': entry_md is not None
        }

        if not entry_md:
            result['warning'] = 'No underlying market data available'
            return result

        # 1. 计算 Moneyness
        stock_price = float(entry_md.close) if entry_md.close else None
        strike = float(option_info['strike'])
        option_type = option_info['option_type']

        if stock_price:
            moneyness = self._calculate_moneyness(stock_price, strike, option_type)
            result['moneyness'] = {
                'value': round(moneyness, 4),
                'percentage': f"{moneyness * 100:.2f}%",
                'classification': self._classify_moneyness(moneyness),
                'stock_price': stock_price,
                'strike': strike
            }

        # 2. 计算 DTE (Days to Expiry)
        entry_date = position.open_time.date() if position.open_time else None
        expiry_date = option_info['expiry_date'].date() if hasattr(option_info['expiry_date'], 'date') else option_info['expiry_date']

        if entry_date:
            dte = (expiry_date - entry_date).days
            result['dte'] = {
                'days': dte,
                'classification': self._classify_dte(dte),
                'expiry_date': expiry_date.strftime('%Y-%m-%d')
            }

        # 3. 正股技术指标状态
        result['underlying_indicators'] = self._analyze_underlying_indicators(entry_md)

        # 4. 趋势方向与期权类型一致性
        result['trend_alignment'] = self._check_trend_alignment(entry_md, option_type)

        # 5. 波动率环境
        result['volatility_environment'] = self._analyze_volatility_environment(entry_md)

        return result

    def _calculate_moneyness(self, stock_price: float, strike: float, option_type: str) -> float:
        """
        计算 Moneyness

        对于 Call: moneyness = (stock_price - strike) / strike
        对于 Put:  moneyness = (strike - stock_price) / strike

        正值表示 ITM，负值表示 OTM
        """
        if option_type == 'call':
            return (stock_price - strike) / strike
        else:  # put
            return (strike - stock_price) / strike

    def _classify_moneyness(self, moneyness: float) -> str:
        """分类 Moneyness"""
        if moneyness > 0.10:
            return 'deep_itm'
        elif moneyness > self.MONEYNESS_ITM_THRESHOLD:
            return 'itm'
        elif moneyness >= self.MONEYNESS_OTM_THRESHOLD:
            return 'atm'
        elif moneyness > -0.10:
            return 'otm'
        else:
            return 'deep_otm'

    def _classify_dte(self, dte: int) -> str:
        """分类 DTE"""
        if dte < self.DTE_SHORT:
            return 'short_term'
        elif dte < self.DTE_MEDIUM:
            return 'medium_term'
        elif dte < self.DTE_LONG:
            return 'long_term'
        else:
            return 'leaps'

    def _analyze_underlying_indicators(self, md: MarketData) -> Dict:
        """分析正股技术指标"""
        indicators = {}

        # RSI
        if md.rsi_14:
            rsi = float(md.rsi_14)
            indicators['rsi'] = {
                'value': round(rsi, 2),
                'status': 'oversold' if rsi < 30 else ('overbought' if rsi > 70 else 'neutral')
            }

        # MACD
        if md.macd and md.macd_signal:
            macd_diff = float(md.macd) - float(md.macd_signal)
            indicators['macd'] = {
                'macd': round(float(md.macd), 4),
                'signal': round(float(md.macd_signal), 4),
                'histogram': round(macd_diff, 4),
                'status': 'bullish' if macd_diff > 0 else 'bearish'
            }

        # 布林带位置
        if md.bb_upper and md.bb_lower and md.close:
            bb_width = float(md.bb_upper) - float(md.bb_lower)
            bb_position = (float(md.close) - float(md.bb_lower)) / bb_width if bb_width > 0 else 0.5
            indicators['bollinger'] = {
                'position': round(bb_position, 2),  # 0=下轨, 0.5=中轨, 1=上轨
                'status': 'near_lower' if bb_position < 0.2 else ('near_upper' if bb_position > 0.8 else 'middle')
            }

        # ADX 趋势强度
        if md.adx:
            adx = float(md.adx)
            indicators['adx'] = {
                'value': round(adx, 2),
                'trend_strength': 'strong' if adx >= 40 else ('moderate' if adx >= 25 else 'weak')
            }

        return indicators

    def _check_trend_alignment(self, md: MarketData, option_type: str) -> Dict:
        """
        检查趋势方向与期权类型的一致性

        Call 应该在看涨趋势中买入
        Put 应该在看跌趋势中买入
        """
        if not md:
            return {'aligned': None, 'reason': 'No market data'}

        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0

        # MACD 方向
        if md.macd:
            total_signals += 1
            if float(md.macd) > 0:
                bullish_signals += 1
            else:
                bearish_signals += 1

        # 均线排列
        if md.ma_5 and md.ma_20 and md.ma_50:
            total_signals += 1
            if float(md.ma_5) > float(md.ma_20) > float(md.ma_50):
                bullish_signals += 1
            elif float(md.ma_5) < float(md.ma_20) < float(md.ma_50):
                bearish_signals += 1

        # 价格相对 MA20
        if md.close and md.ma_20:
            total_signals += 1
            if float(md.close) > float(md.ma_20):
                bullish_signals += 1
            else:
                bearish_signals += 1

        if total_signals == 0:
            return {'aligned': None, 'reason': 'Insufficient indicators'}

        trend = 'bullish' if bullish_signals > bearish_signals else ('bearish' if bearish_signals > bullish_signals else 'neutral')
        aligned = (option_type == 'call' and trend == 'bullish') or (option_type == 'put' and trend == 'bearish')

        return {
            'aligned': aligned,
            'trend': trend,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'total_signals': total_signals
        }

    def _analyze_volatility_environment(self, md: MarketData) -> Dict:
        """分析波动率环境"""
        result = {}

        # ATR 波动率
        if md.atr_14 and md.close:
            atr_pct = float(md.atr_14) / float(md.close) * 100
            result['atr'] = {
                'value': round(float(md.atr_14), 4),
                'percentage': round(atr_pct, 2),
                'level': 'high' if atr_pct > 3 else ('moderate' if atr_pct > 1.5 else 'low')
            }

        # 布林带宽度（波动率代理）
        if md.bb_upper and md.bb_lower and md.close:
            bb_width_pct = (float(md.bb_upper) - float(md.bb_lower)) / float(md.close) * 100
            result['bb_width'] = {
                'percentage': round(bb_width_pct, 2),
                'level': 'expanded' if bb_width_pct > 10 else ('compressed' if bb_width_pct < 4 else 'normal')
            }

        return result

    # ==================== 正股走势分析 ====================

    def analyze_underlying_movement(
        self,
        position: Position,
        option_info: Dict,
        entry_md: Optional[MarketData],
        exit_md: Optional[MarketData]
    ) -> Dict:
        """
        分析持有期间正股的表现

        Args:
            position: 持仓
            option_info: 期权信息
            entry_md: 入场时市场数据
            exit_md: 出场时市场数据

        Returns:
            Dict: 正股走势分析
        """
        result = {}

        if not entry_md or not entry_md.close:
            result['warning'] = 'No entry market data'
            return result

        entry_price = float(entry_md.close)
        strike = float(option_info['strike'])
        option_type = option_info['option_type']

        result['entry_price'] = entry_price
        result['strike'] = strike

        if exit_md and exit_md.close:
            exit_price = float(exit_md.close)
            result['exit_price'] = exit_price

            # 正股价格变动
            price_change = exit_price - entry_price
            price_change_pct = (price_change / entry_price) * 100

            result['price_movement'] = {
                'change': round(price_change, 4),
                'change_pct': round(price_change_pct, 2),
                'direction': 'up' if price_change > 0 else ('down' if price_change < 0 else 'flat')
            }

            # 是否突破/触及行权价
            result['strike_analysis'] = self._analyze_strike_breach(
                entry_price, exit_price, strike, option_type
            )

            # 正股走势对期权的影响
            result['impact_on_option'] = self._analyze_impact_on_option(
                price_change_pct, option_type
            )

        # 如果有 MAE/MFE 数据
        if position.mae_pct is not None:
            result['underlying_mae'] = round(float(position.mae_pct), 2)
        if position.mfe_pct is not None:
            result['underlying_mfe'] = round(float(position.mfe_pct), 2)

        return result

    def _analyze_strike_breach(
        self,
        entry_price: float,
        exit_price: float,
        strike: float,
        option_type: str
    ) -> Dict:
        """分析行权价突破情况"""
        result = {}

        # 入场时距离行权价
        entry_distance = (entry_price - strike) / strike
        exit_distance = (exit_price - strike) / strike

        result['entry_distance_from_strike'] = round(entry_distance * 100, 2)
        result['exit_distance_from_strike'] = round(exit_distance * 100, 2)

        if option_type == 'call':
            # Call: 希望股价上涨突破行权价
            crossed_itm = entry_price < strike and exit_price >= strike
            crossed_deeper_itm = entry_price >= strike and exit_price > entry_price
            result['favorable_movement'] = crossed_itm or crossed_deeper_itm
            result['crossed_strike'] = crossed_itm
        else:
            # Put: 希望股价下跌突破行权价
            crossed_itm = entry_price > strike and exit_price <= strike
            crossed_deeper_itm = entry_price <= strike and exit_price < entry_price
            result['favorable_movement'] = crossed_itm or crossed_deeper_itm
            result['crossed_strike'] = crossed_itm

        return result

    def _analyze_impact_on_option(self, price_change_pct: float, option_type: str) -> Dict:
        """分析正股走势对期权的影响"""
        result = {}

        # 对于 Call，正股上涨有利
        # 对于 Put，正股下跌有利
        if option_type == 'call':
            favorable = price_change_pct > 0
            impact_direction = 'favorable' if favorable else 'unfavorable'
        else:
            favorable = price_change_pct < 0
            impact_direction = 'favorable' if favorable else 'unfavorable'

        result['direction'] = impact_direction
        result['favorable'] = favorable

        # 估算 Delta 影响
        # 简化假设 ATM Delta = 0.5
        estimated_delta = 0.5 if option_type == 'call' else -0.5
        delta_impact = abs(price_change_pct) * abs(estimated_delta)

        result['estimated_delta_contribution'] = round(delta_impact, 2)

        return result

    # ==================== Greeks 影响估算 ====================

    def estimate_greeks_impact(
        self,
        position: Position,
        option_info: Dict,
        entry_md: Optional[MarketData],
        exit_md: Optional[MarketData]
    ) -> Dict:
        """
        估算 Greeks 对期权价值的影响

        无需实际 Greeks 数据，基于经验规则估算
        """
        result = {}

        if not entry_md or not entry_md.close:
            result['warning'] = 'Cannot estimate without market data'
            return result

        stock_price = float(entry_md.close)
        strike = float(option_info['strike'])
        option_type = option_info['option_type']

        # 1. Delta 估算
        moneyness = self._calculate_moneyness(stock_price, strike, option_type)
        moneyness_class = self._classify_moneyness(moneyness)
        delta_key = f"{moneyness_class}_{option_type}"
        estimated_delta = self.ESTIMATED_DELTA.get(delta_key, 0.5 if option_type == 'call' else -0.5)

        result['delta'] = {
            'estimated_value': estimated_delta,
            'moneyness': moneyness_class,
            'explanation': f"Based on {moneyness_class} {option_type}, estimated delta is {estimated_delta}"
        }

        # 2. Theta 影响估算
        entry_date = position.open_time.date() if position.open_time else None
        exit_date = position.close_time.date() if position.close_time else None
        expiry_date = option_info['expiry_date'].date() if hasattr(option_info['expiry_date'], 'date') else option_info['expiry_date']

        if entry_date:
            entry_dte = (expiry_date - entry_date).days
            exit_dte = (expiry_date - exit_date).days if exit_date else entry_dte
            days_held = (exit_date - entry_date).days if exit_date else 0

            result['theta'] = {
                'entry_dte': entry_dte,
                'exit_dte': exit_dte,
                'days_held': days_held,
                'theta_decay_level': self._estimate_theta_decay(entry_dte, exit_dte),
                'explanation': self._get_theta_explanation(entry_dte, exit_dte, days_held)
            }

        # 3. Vega 影响（波动率变化）
        if entry_md.atr_14 and exit_md and exit_md.atr_14:
            entry_vol = float(entry_md.atr_14)
            exit_vol = float(exit_md.atr_14)
            vol_change = (exit_vol - entry_vol) / entry_vol if entry_vol > 0 else 0

            result['vega'] = {
                'volatility_change_pct': round(vol_change * 100, 2),
                'impact': 'favorable' if vol_change > 0 else 'unfavorable',
                'explanation': f"ATR changed by {vol_change*100:.1f}%, affecting option premium"
            }

        # 4. 综合影响估算
        result['summary'] = self._summarize_greeks_impact(result, position)

        return result

    def _estimate_theta_decay(self, entry_dte: int, exit_dte: int) -> str:
        """估算 Theta 衰减水平"""
        # Theta 衰减在到期前加速
        if exit_dte <= 7:
            return 'severe'  # 最后一周衰减最快
        elif exit_dte <= 14:
            return 'high'
        elif exit_dte <= 30:
            return 'moderate'
        else:
            return 'low'

    def _get_theta_explanation(self, entry_dte: int, exit_dte: int, days_held: int) -> str:
        """获取 Theta 影响说明"""
        if days_held == 0:
            return "No time decay (same day trade)"

        if exit_dte <= 7:
            return f"Held through high theta decay period ({days_held} days, exited at {exit_dte} DTE)"
        elif exit_dte <= 14:
            return f"Moderate theta decay ({days_held} days held, {exit_dte} DTE remaining)"
        else:
            return f"Low theta impact ({days_held} days held, {exit_dte} DTE remaining)"

    def _summarize_greeks_impact(self, greeks_result: Dict, position: Position) -> Dict:
        """汇总 Greeks 影响"""
        summary = {
            'primary_driver': None,
            'explanation': []
        }

        # 基于盈亏判断主要驱动因素
        if position.net_pnl:
            pnl = float(position.net_pnl)

            if pnl > 0:
                summary['outcome'] = 'profitable'
                if 'delta' in greeks_result:
                    summary['explanation'].append("Delta likely contributed to gains")
            else:
                summary['outcome'] = 'loss'
                if greeks_result.get('theta', {}).get('theta_decay_level') in ['severe', 'high']:
                    summary['primary_driver'] = 'theta_decay'
                    summary['explanation'].append("Theta decay likely contributed to losses")

        return summary

    # ==================== 策略评估 ====================

    def evaluate_option_strategy(
        self,
        position: Position,
        option_info: Dict,
        entry_md: Optional[MarketData],
        exit_md: Optional[MarketData]
    ) -> Dict:
        """
        评估期权交易策略

        Args:
            position: 持仓
            option_info: 期权信息
            entry_md: 入场市场数据
            exit_md: 出场市场数据

        Returns:
            Dict: 策略评估结果
        """
        result = {}

        # 1. 到期日选择评估
        result['expiry_selection'] = self._evaluate_expiry_selection(position, option_info)

        # 2. 行权价选择评估
        result['strike_selection'] = self._evaluate_strike_selection(position, option_info, entry_md)

        # 3. 入场时机评估
        result['entry_timing'] = self._evaluate_entry_timing(position, option_info, entry_md)

        # 4. 出场时机评估
        if position.close_time:
            result['exit_timing'] = self._evaluate_exit_timing(position, option_info, exit_md)

        # 5. 整体策略评估
        result['overall_assessment'] = self._assess_overall_strategy(result, position)

        return result

    def _evaluate_expiry_selection(self, position: Position, option_info: Dict) -> Dict:
        """评估到期日选择"""
        entry_date = position.open_time.date() if position.open_time else None
        expiry_date = option_info['expiry_date'].date() if hasattr(option_info['expiry_date'], 'date') else option_info['expiry_date']

        if not entry_date:
            return {'evaluation': 'unknown'}

        dte_at_entry = (expiry_date - entry_date).days
        holding_days = position.holding_period_days or 0

        result = {
            'dte_at_entry': dte_at_entry,
            'holding_days': holding_days,
            'dte_classification': self._classify_dte(dte_at_entry)
        }

        # 评估是否匹配
        if dte_at_entry < 7 and holding_days > 3:
            result['assessment'] = 'poor'
            result['reason'] = 'Short DTE with multi-day hold - high theta risk'
        elif dte_at_entry < 14 and holding_days > 7:
            result['assessment'] = 'risky'
            result['reason'] = 'Near-term expiry held through high decay period'
        elif dte_at_entry >= 30:
            result['assessment'] = 'good'
            result['reason'] = 'Adequate time buffer for the trade'
        else:
            result['assessment'] = 'moderate'
            result['reason'] = 'Standard DTE selection'

        return result

    def _evaluate_strike_selection(
        self,
        position: Position,
        option_info: Dict,
        entry_md: Optional[MarketData]
    ) -> Dict:
        """评估行权价选择"""
        if not entry_md or not entry_md.close:
            return {'evaluation': 'unknown'}

        stock_price = float(entry_md.close)
        strike = float(option_info['strike'])
        option_type = option_info['option_type']

        moneyness = self._calculate_moneyness(stock_price, strike, option_type)
        moneyness_class = self._classify_moneyness(moneyness)

        result = {
            'stock_price_at_entry': stock_price,
            'strike': strike,
            'moneyness': round(moneyness * 100, 2),
            'classification': moneyness_class
        }

        # 根据 moneyness 评估
        if moneyness_class == 'atm':
            result['assessment'] = 'balanced'
            result['reason'] = 'ATM strike offers balanced risk/reward'
        elif moneyness_class in ['itm', 'deep_itm']:
            result['assessment'] = 'conservative'
            result['reason'] = 'ITM strike - higher delta but more expensive'
        elif moneyness_class == 'otm':
            result['assessment'] = 'aggressive'
            result['reason'] = 'OTM strike - lower cost but lower probability'
        else:  # deep_otm
            result['assessment'] = 'speculative'
            result['reason'] = 'Deep OTM - very low probability of profit'

        return result

    def _evaluate_entry_timing(
        self,
        position: Position,
        option_info: Dict,
        entry_md: Optional[MarketData]
    ) -> Dict:
        """评估入场时机"""
        result = {}

        if not entry_md:
            return {'assessment': 'unknown'}

        option_type = option_info['option_type']
        is_call = option_type == 'call'

        # 基于技术指标评估
        score = 50  # 基础分

        # RSI
        if entry_md.rsi_14:
            rsi = float(entry_md.rsi_14)
            if is_call:
                if rsi < 30:
                    score += 20  # 超卖买 Call 好
                elif rsi > 70:
                    score -= 15  # 超买买 Call 差
            else:
                if rsi > 70:
                    score += 20  # 超买买 Put 好
                elif rsi < 30:
                    score -= 15

        # MACD
        if entry_md.macd and entry_md.macd_signal:
            macd_diff = float(entry_md.macd) - float(entry_md.macd_signal)
            if is_call and macd_diff > 0:
                score += 10
            elif not is_call and macd_diff < 0:
                score += 10

        # 评级
        if score >= 70:
            result['assessment'] = 'good'
        elif score >= 50:
            result['assessment'] = 'moderate'
        else:
            result['assessment'] = 'poor'

        result['score'] = score

        return result

    def _evaluate_exit_timing(
        self,
        position: Position,
        option_info: Dict,
        exit_md: Optional[MarketData]
    ) -> Dict:
        """评估出场时机"""
        result = {}

        entry_date = position.open_time.date() if position.open_time else None
        exit_date = position.close_time.date() if position.close_time else None
        expiry_date = option_info['expiry_date'].date() if hasattr(option_info['expiry_date'], 'date') else option_info['expiry_date']

        if exit_date and expiry_date:
            dte_at_exit = (expiry_date - exit_date).days
            result['dte_at_exit'] = dte_at_exit

            # 检查是否在高衰减期出场
            if dte_at_exit <= 0:
                result['assessment'] = 'expired'
                result['reason'] = 'Held to expiration'
            elif dte_at_exit <= 7:
                result['assessment'] = 'late'
                result['reason'] = 'Exited during high theta decay period'
            else:
                result['assessment'] = 'timely'
                result['reason'] = f'Exited with {dte_at_exit} days remaining'

        # 基于盈亏评估
        if position.net_pnl:
            pnl = float(position.net_pnl)
            result['profitable'] = pnl > 0

        return result

    def _assess_overall_strategy(self, evaluations: Dict, position: Position) -> Dict:
        """整体策略评估"""
        result = {
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }

        # 分析优势
        if evaluations.get('expiry_selection', {}).get('assessment') == 'good':
            result['strengths'].append('Good expiry selection with adequate time')

        if evaluations.get('strike_selection', {}).get('assessment') == 'balanced':
            result['strengths'].append('Balanced strike selection (ATM)')

        if evaluations.get('entry_timing', {}).get('assessment') == 'good':
            result['strengths'].append('Good entry timing based on technicals')

        # 分析弱点
        if evaluations.get('expiry_selection', {}).get('assessment') == 'poor':
            result['weaknesses'].append('Short DTE increased theta risk')
            result['recommendations'].append('Consider longer-dated options to reduce theta decay')

        if evaluations.get('strike_selection', {}).get('assessment') == 'speculative':
            result['weaknesses'].append('Deep OTM strike had low probability of profit')
            result['recommendations'].append('Consider ATM or slight OTM for better probability')

        if evaluations.get('exit_timing', {}).get('assessment') == 'late':
            result['weaknesses'].append('Late exit during high theta decay')
            result['recommendations'].append('Consider exiting before final week to avoid theta acceleration')

        # 整体评级
        strength_count = len(result['strengths'])
        weakness_count = len(result['weaknesses'])

        if strength_count >= 2 and weakness_count == 0:
            result['overall_grade'] = 'A'
        elif strength_count >= 1 and weakness_count <= 1:
            result['overall_grade'] = 'B'
        elif weakness_count <= 1:
            result['overall_grade'] = 'C'
        else:
            result['overall_grade'] = 'D'

        return result

    # ==================== 期权专属评分 ====================

    def calculate_option_scores(self, analysis: Dict) -> Dict:
        """
        计算期权专属评分

        Args:
            analysis: 完整分析结果

        Returns:
            Dict: 各维度评分
        """
        scores = {}

        # 1. Moneyness 选择评分 (25%)
        scores['moneyness_score'] = self._score_moneyness_selection(analysis)

        # 2. 趋势一致性评分 (25%)
        scores['trend_alignment_score'] = self._score_trend_alignment(analysis)

        # 3. 波动率环境评分 (25%)
        scores['volatility_score'] = self._score_volatility_environment(analysis)

        # 4. 时间价值评分 (25%)
        scores['time_value_score'] = self._score_time_value(analysis)

        # 综合评分
        scores['overall_option_score'] = (
            scores['moneyness_score'] * 0.25 +
            scores['trend_alignment_score'] * 0.25 +
            scores['volatility_score'] * 0.25 +
            scores['time_value_score'] * 0.25
        )

        return scores

    def _score_moneyness_selection(self, analysis: Dict) -> float:
        """评估 Moneyness 选择"""
        moneyness_class = analysis.get('entry_context', {}).get('moneyness', {}).get('classification')

        if not moneyness_class:
            return 50.0

        # ATM 通常是风险/收益最均衡的选择
        scores = {
            'atm': 85,
            'itm': 75,
            'otm': 65,
            'deep_itm': 60,
            'deep_otm': 40
        }

        return scores.get(moneyness_class, 50.0)

    def _score_trend_alignment(self, analysis: Dict) -> float:
        """评估趋势一致性"""
        alignment = analysis.get('entry_context', {}).get('trend_alignment', {})

        if alignment.get('aligned') is None:
            return 50.0

        if alignment.get('aligned'):
            # 方向一致
            ratio = alignment.get('bullish_signals', 0) + alignment.get('bearish_signals', 0)
            total = alignment.get('total_signals', 1)
            strength = max(alignment.get('bullish_signals', 0), alignment.get('bearish_signals', 0)) / total

            if strength >= 0.8:
                return 95
            elif strength >= 0.6:
                return 80
            else:
                return 70
        else:
            # 方向不一致（逆势交易）
            return 40

    def _score_volatility_environment(self, analysis: Dict) -> float:
        """评估波动率环境"""
        vol_env = analysis.get('entry_context', {}).get('volatility_environment', {})

        # 买入期权时，低波动率环境更有利（期权便宜）
        atr_level = vol_env.get('atr', {}).get('level')
        bb_level = vol_env.get('bb_width', {}).get('level')

        score = 70  # 基础分

        if atr_level == 'low':
            score += 15  # 低波动买期权好
        elif atr_level == 'high':
            score -= 10

        if bb_level == 'compressed':
            score += 10  # 压缩状态，可能即将突破
        elif bb_level == 'expanded':
            score -= 5

        return min(100, max(0, score))

    def _score_time_value(self, analysis: Dict) -> float:
        """评估时间价值管理"""
        theta_info = analysis.get('greeks_impact', {}).get('theta', {})
        expiry_eval = analysis.get('strategy_evaluation', {}).get('expiry_selection', {})

        if not theta_info:
            return 50.0

        entry_dte = theta_info.get('entry_dte', 30)
        exit_dte = theta_info.get('exit_dte', entry_dte)
        decay_level = theta_info.get('theta_decay_level', 'moderate')

        # 评分逻辑
        score = 70

        # DTE 选择
        if entry_dte >= 30:
            score += 10
        elif entry_dte < 7:
            score -= 20

        # 出场时机
        if decay_level == 'severe':
            score -= 15
        elif decay_level == 'low':
            score += 10

        # 到期日选择评估
        if expiry_eval.get('assessment') == 'good':
            score += 10
        elif expiry_eval.get('assessment') == 'poor':
            score -= 15

        return min(100, max(0, score))

    # ==================== 批量分析 ====================

    def analyze_all_options(self, update_db: bool = False) -> Dict:
        """
        分析所有期权持仓

        Args:
            update_db: 是否更新数据库

        Returns:
            Dict: 统计信息
        """
        # 查询所有期权持仓
        positions = self.session.query(Position).filter(
            Position.is_option == 1,
            Position.status == PositionStatus.CLOSED
        ).all()

        stats = {
            'total': len(positions),
            'analyzed': 0,
            'failed': 0,
            'results': []
        }

        for position in positions:
            try:
                result = self.analyze_position(position)
                stats['results'].append(result)
                stats['analyzed'] += 1

                logger.info(f"Analyzed option position {position.id}: {position.symbol}")

            except Exception as e:
                logger.error(f"Failed to analyze position {position.id}: {e}")
                stats['failed'] += 1

        logger.info(f"Analyzed {stats['analyzed']}/{stats['total']} option positions")

        return stats
