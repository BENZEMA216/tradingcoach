"""
QualityScorer - 交易质量评分引擎 (v2.1)

input: Position持仓, MarketData市场数据, 技术指标, 新闻搜索
output: 9维度评分(0-100), 综合评分, 等级(A-F)
pos: 分析引擎层核心 - 量化评估交易质量，输出可比较的分数

维度权重: 进场18% | 出场17% | 趋势14% | 风险12% | 市场环境11% | 行为11% | 新闻契合7% | 执行5% | 期权5%

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import json
import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.models.news_context import NewsContext
from src.utils.option_parser import OptionParser
from src.analyzers.market_env_scorer import MarketEnvironmentScorer
from src.analyzers.behavior_scorer import TradingBehaviorScorer
from src.analyzers.execution_scorer import ExecutionQualityScorer
from src.analyzers.news_searcher import NewsSearcher
from src.analyzers.news_alignment_scorer import NewsAlignmentScorer
from src.analyzers.news_adapters import create_search_func_from_config
from config import (
    SCORE_WEIGHT_ENTRY,
    SCORE_WEIGHT_EXIT,
    SCORE_WEIGHT_TREND,
    SCORE_WEIGHT_RISK,
    RSI_OVERSOLD,
    RSI_OVERBOUGHT,
    STOCH_OVERSOLD,
    STOCH_OVERBOUGHT,
    ADX_WEAK_TREND,
    ADX_MODERATE_TREND,
    ADX_STRONG_TREND,
    NEWS_SEARCH_ENABLED,
    NEWS_SEARCH_RANGE_DAYS,
    SCORE_WEIGHT_NEWS_ALIGNMENT
)

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    交易质量评分器

    功能：
    1. 计算四维度评分（进场、出场、趋势、风险）
    2. 生成综合评分和等级
    3. 批量评分多个交易
    4. 更新positions表的评分字段
    """

    # 新版9维度权重配置 (含新闻契合度)
    WEIGHTS_V2 = {
        'entry': 0.18,        # 入场质量 (原20%, -2%)
        'exit': 0.17,         # 出场质量 (原18%, -1%)
        'market_env': 0.11,   # 市场环境 (原12%, -1%)
        'behavior': 0.11,     # 交易行为 (原12%, -1%)
        'trend': 0.14,        # 趋势把握 (原15%, -1%)
        'risk': 0.12,         # 风险管理 (原13%, -1%)
        'execution': 0.05,    # 执行质量
        'options': 0.05,      # 期权希腊字母 (条件应用)
        'news_alignment': 0.07,  # 新闻契合度 (新增7%)
    }

    def __init__(self, use_v2: bool = True):
        """
        初始化评分器

        Args:
            use_v2: 是否使用新版8维度评分系统
        """
        self.use_v2 = use_v2

        if use_v2:
            self.weights = self.WEIGHTS_V2.copy()
        else:
            # 兼容旧版4维度权重
            self.weights = {
                'entry': SCORE_WEIGHT_ENTRY,
                'exit': SCORE_WEIGHT_EXIT,
                'trend': SCORE_WEIGHT_TREND,
                'risk': SCORE_WEIGHT_RISK
            }

        # 初始化子评分器
        self.market_env_scorer = MarketEnvironmentScorer()
        self.behavior_scorer = TradingBehaviorScorer()
        self.execution_scorer = ExecutionQualityScorer()

        # 新闻评分器 (可选)
        self.news_search_enabled = NEWS_SEARCH_ENABLED
        if self.news_search_enabled:
            # 从配置自动获取新闻搜索函数（支持国际/中国网络）
            search_func = create_search_func_from_config()
            self.news_searcher = NewsSearcher(search_func=search_func)
            self.news_alignment_scorer = NewsAlignmentScorer()
            if search_func:
                logger.info("News search adapter configured from config")
            else:
                logger.warning("No news search adapter available, news search will return empty results")
        else:
            self.news_searcher = None
            self.news_alignment_scorer = None

        # 市场数据缓存 (用于批量评分时避免 N+1 查询)
        # 格式: {(symbol, date_str): MarketData}
        self._market_data_cache: Dict[Tuple[str, str], Optional[MarketData]] = {}

        logger.info(f"QualityScorer initialized (v2={use_v2}, news_search={self.news_search_enabled})")

    # ==================== 进场质量评分（30%权重）====================

    def score_entry_quality(
        self,
        position: Position,
        entry_market_data: Optional[MarketData]
    ) -> Dict[str, float]:
        """
        评估进场质量（0-100分）

        Args:
            position: Position对象
            entry_market_data: 进场时的市场数据

        Returns:
            dict: {
                'entry_score': 总分,
                'indicator_score': 技术指标得分,
                'position_score': 位置得分,
                'volume_score': 成交量得分,
                'market_score': 市场环境得分
            }
        """
        if not entry_market_data:
            logger.warning(f"No entry market data for position {position.id}")
            return {'entry_score': 50.0}  # 默认中等评分

        # 1. 技术指标配合度（40%）
        indicator_score = self._score_entry_indicators(
            position, entry_market_data
        )

        # 2. 支撑/阻力位置（30%）
        position_score = self._score_entry_position(
            position, entry_market_data
        )

        # 3. 成交量确认（20%）
        volume_score = self._score_entry_volume(
            position, entry_market_data
        )

        # 4. 市场环境（10%）- 简化版本，后续可增强
        market_score = 70.0  # 默认中等

        # 加权计算总分
        entry_score = (
            indicator_score * 0.40 +
            position_score * 0.30 +
            volume_score * 0.20 +
            market_score * 0.10
        )

        return {
            'entry_score': entry_score,
            'indicator_score': indicator_score,
            'position_score': position_score,
            'volume_score': volume_score,
            'market_score': market_score
        }

    def _score_entry_indicators(
        self,
        position: Position,
        md: MarketData
    ) -> float:
        """
        评估进场时的技术指标配合度（加权平均）

        权重分配（新增指标后重新分配）：
        - RSI评分 (15%)
        - MACD评分 (12%)
        - 布林带评分 (10%)
        - ADX趋势强度评分 (10%)
        - Stochastic评分 (10%)
        - 成交量确认评分 (8%)
        - NEW: CCI评分 (8%)
        - NEW: MFI资金流评分 (8%)
        - NEW: Ichimoku云图评分 (10%)
        - NEW: 挤压信号评分 (5%)
        - NEW: OBV背离评分 (4%)
        """
        weighted_scores = []
        is_long = position.direction in ['buy', 'buy_to_open', 'long']

        # 1. RSI评分 (权重15%)
        rsi_score = self._score_rsi(md, is_long)
        if rsi_score is not None:
            weighted_scores.append((rsi_score, 0.15))

        # 2. MACD评分 (权重12%)
        macd_score = self._score_macd(md, is_long)
        if macd_score is not None:
            weighted_scores.append((macd_score, 0.12))

        # 3. 布林带评分 (权重10%)
        bb_score = self._score_bollinger(md, is_long)
        if bb_score is not None:
            weighted_scores.append((bb_score, 0.10))

        # 4. ADX趋势强度评分 (权重10%)
        adx_score = self._score_adx(md, is_long)
        if adx_score is not None:
            weighted_scores.append((adx_score, 0.10))

        # 5. Stochastic评分 (权重10%)
        stoch_score = self._score_stochastic(md, is_long)
        if stoch_score is not None:
            weighted_scores.append((stoch_score, 0.10))

        # 6. 成交量确认评分 (权重8%)
        volume_score = self._score_volume_confirmation(md)
        if volume_score is not None:
            weighted_scores.append((volume_score, 0.08))

        # ==================== 新增指标评分 ====================

        # 7. CCI评分 (权重8%)
        cci_score = self._score_cci(md, is_long)
        if cci_score is not None:
            weighted_scores.append((cci_score, 0.08))

        # 8. MFI资金流评分 (权重8%)
        mfi_score = self._score_mfi(md, is_long)
        if mfi_score is not None:
            weighted_scores.append((mfi_score, 0.08))

        # 9. Ichimoku云图评分 (权重10%)
        ichimoku_score = self._score_ichimoku(md, is_long)
        if ichimoku_score is not None:
            weighted_scores.append((ichimoku_score, 0.10))

        # 10. 挤压信号评分 (权重5%)
        squeeze_score = self._score_squeeze(md)
        if squeeze_score is not None:
            weighted_scores.append((squeeze_score, 0.05))

        # 11. SuperTrend方向评分 (权重4%)
        supertrend_score = self._score_supertrend(md, is_long)
        if supertrend_score is not None:
            weighted_scores.append((supertrend_score, 0.04))

        # 计算加权平均分
        if not weighted_scores:
            return 50.0

        total_weight = sum(w for _, w in weighted_scores)
        weighted_sum = sum(s * w for s, w in weighted_scores)

        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _score_rsi(self, md: MarketData, is_long: bool) -> Optional[float]:
        """RSI评分：超买超卖区域判断"""
        if md.rsi_14 is None:
            return None

        if is_long:
            # 做多：RSI越低越好（超卖区买入）
            if md.rsi_14 < RSI_OVERSOLD:
                return 95
            elif md.rsi_14 < 40:
                return 80
            elif md.rsi_14 < 50:
                return 65
            elif md.rsi_14 < 60:
                return 50
            elif md.rsi_14 < RSI_OVERBOUGHT:
                return 35
            else:
                return 20  # 超买区买入，风险大
        else:
            # 做空：RSI越高越好（超买区卖出）
            if md.rsi_14 > RSI_OVERBOUGHT:
                return 95
            elif md.rsi_14 > 60:
                return 80
            elif md.rsi_14 > 50:
                return 65
            elif md.rsi_14 > 40:
                return 50
            elif md.rsi_14 > RSI_OVERSOLD:
                return 35
            else:
                return 20

    def _score_macd(self, md: MarketData, is_long: bool) -> Optional[float]:
        """MACD评分：金叉死叉判断"""
        if md.macd is None or md.macd_signal is None:
            return None

        macd_diff = float(md.macd) - float(md.macd_signal)

        if is_long:
            # 做多：MACD在信号线上方（金叉）
            if macd_diff > 0 and float(md.macd) > 0:
                return 90  # 强势金叉
            elif macd_diff > 0:
                return 75  # 金叉但在0轴下方
            elif macd_diff > -0.5:
                return 55  # 接近金叉
            else:
                return 35  # 死叉状态
        else:
            # 做空：MACD在信号线下方（死叉）
            if macd_diff < 0 and float(md.macd) < 0:
                return 90  # 强势死叉
            elif macd_diff < 0:
                return 75  # 死叉但在0轴上方
            elif macd_diff < 0.5:
                return 55  # 接近死叉
            else:
                return 35  # 金叉状态

    def _score_bollinger(self, md: MarketData, is_long: bool) -> Optional[float]:
        """布林带评分：价格在通道中的位置"""
        if not all([md.bb_upper, md.bb_middle, md.bb_lower, md.close]):
            return None

        bb_width = float(md.bb_upper) - float(md.bb_lower)
        if bb_width <= 0:
            return None

        bb_position = (float(md.close) - float(md.bb_lower)) / bb_width

        if is_long:
            # 做多：在下轨附近买入
            if bb_position < 0.2:
                return 92
            elif bb_position < 0.35:
                return 80
            elif bb_position < 0.5:
                return 65
            elif bb_position < 0.7:
                return 50
            else:
                return 30  # 上轨附近买入风险大
        else:
            # 做空：在上轨附近卖出
            if bb_position > 0.8:
                return 92
            elif bb_position > 0.65:
                return 80
            elif bb_position > 0.5:
                return 65
            elif bb_position > 0.3:
                return 50
            else:
                return 30

    def _score_adx(self, md: MarketData, is_long: bool) -> Optional[float]:
        """
        ADX趋势强度评分

        评分逻辑：
        - ADX衡量趋势强度（不区分方向）
        - +DI和-DI判断趋势方向
        - 做多时：+DI > -DI且ADX强，得分高
        - 做空时：-DI > +DI且ADX强，得分高
        """
        if md.adx is None:
            return None

        adx = float(md.adx)
        plus_di = float(md.plus_di) if md.plus_di is not None else None
        minus_di = float(md.minus_di) if md.minus_di is not None else None

        # 仅有ADX时，仅评估趋势强度
        if plus_di is None or minus_di is None:
            if adx >= ADX_STRONG_TREND:
                return 75  # 强趋势但方向未知
            elif adx >= ADX_MODERATE_TREND:
                return 65
            elif adx >= ADX_WEAK_TREND:
                return 55
            else:
                return 45  # 震荡市，趋势策略风险大

        # 有完整DI数据时，综合评分
        direction_correct = (is_long and plus_di > minus_di) or (not is_long and minus_di > plus_di)
        di_diff = abs(plus_di - minus_di)

        if direction_correct:
            # 方向正确
            if adx >= ADX_STRONG_TREND and di_diff >= 10:
                return 95  # 强趋势+方向明确
            elif adx >= ADX_MODERATE_TREND and di_diff >= 5:
                return 85  # 中等趋势+方向正确
            elif adx >= ADX_WEAK_TREND:
                return 70  # 弱趋势+方向正确
            else:
                return 55  # 震荡但方向正确
        else:
            # 方向错误（逆势交易）
            if adx >= ADX_STRONG_TREND:
                return 25  # 强逆势，风险很大
            elif adx >= ADX_MODERATE_TREND:
                return 35  # 中等逆势
            elif adx >= ADX_WEAK_TREND:
                return 45  # 弱趋势逆势
            else:
                return 50  # 震荡市，方向不重要

    def _score_stochastic(self, md: MarketData, is_long: bool) -> Optional[float]:
        """
        Stochastic随机指标评分

        评分逻辑：
        - 做多：%K在超卖区且%K上穿%D（金叉），得分高
        - 做空：%K在超买区且%K下穿%D（死叉），得分高
        """
        if md.stoch_k is None:
            return None

        stoch_k = float(md.stoch_k)
        stoch_d = float(md.stoch_d) if md.stoch_d is not None else stoch_k

        # 计算K-D差值（正值表示金叉趋势，负值表示死叉趋势）
        kd_diff = stoch_k - stoch_d

        if is_long:
            # 做多：超卖区 + 金叉
            if stoch_k < STOCH_OVERSOLD:
                if kd_diff > 0:
                    return 95  # 超卖区金叉，最佳买入
                else:
                    return 80  # 超卖区，等待金叉
            elif stoch_k < 35:
                if kd_diff > 0:
                    return 80  # 低位金叉
                else:
                    return 65
            elif stoch_k < 50:
                return 60 if kd_diff > 0 else 50
            elif stoch_k < 65:
                return 45
            elif stoch_k < STOCH_OVERBOUGHT:
                return 35
            else:
                return 20  # 超买区做多，风险大
        else:
            # 做空：超买区 + 死叉
            if stoch_k > STOCH_OVERBOUGHT:
                if kd_diff < 0:
                    return 95  # 超买区死叉，最佳卖出
                else:
                    return 80  # 超买区，等待死叉
            elif stoch_k > 65:
                if kd_diff < 0:
                    return 80  # 高位死叉
                else:
                    return 65
            elif stoch_k > 50:
                return 60 if kd_diff < 0 else 50
            elif stoch_k > 35:
                return 45
            elif stoch_k > STOCH_OVERSOLD:
                return 35
            else:
                return 20  # 超卖区做空，风险大

    def _score_volume_confirmation(self, md: MarketData) -> Optional[float]:
        """
        成交量确认评分

        评分逻辑：
        - 成交量 > 20日均量：放量，确认信号有效
        - 成交量 < 20日均量：缩量，信号可靠性降低
        """
        if md.volume is None or md.volume <= 0:
            return None

        volume = float(md.volume)

        # 优先使用volume_sma_20
        if md.volume_sma_20 is not None and md.volume_sma_20 > 0:
            volume_sma = float(md.volume_sma_20)
            volume_ratio = volume / volume_sma

            if volume_ratio >= 2.0:
                return 95  # 大幅放量，强确认
            elif volume_ratio >= 1.5:
                return 85  # 明显放量
            elif volume_ratio >= 1.2:
                return 75  # 温和放量
            elif volume_ratio >= 1.0:
                return 65  # 正常成交量
            elif volume_ratio >= 0.7:
                return 55  # 轻度缩量
            elif volume_ratio >= 0.5:
                return 45  # 明显缩量
            else:
                return 35  # 极度缩量，信号不可靠
        else:
            # 无均量数据，给基本分
            return 60

    # ==================== 新增指标评分方法 ====================

    def _score_cci(self, md: MarketData, is_long: bool) -> Optional[float]:
        """
        CCI商品通道指数评分

        CCI范围: -300 ~ +300，通常 -100 ~ +100 为正常区域
        - 做多：CCI < -100 超卖区买入得分高
        - 做空：CCI > +100 超买区卖出得分高
        """
        if md.cci_20 is None:
            return None

        cci = float(md.cci_20)

        if is_long:
            if cci < -200:
                return 95  # 极度超卖
            elif cci < -100:
                return 85  # 超卖区
            elif cci < -50:
                return 70  # 接近超卖
            elif cci < 50:
                return 55  # 中性区
            elif cci < 100:
                return 40  # 偏高
            else:
                return 25  # 超买区做多风险大
        else:
            if cci > 200:
                return 95  # 极度超买
            elif cci > 100:
                return 85  # 超买区
            elif cci > 50:
                return 70  # 接近超买
            elif cci > -50:
                return 55  # 中性区
            elif cci > -100:
                return 40  # 偏低
            else:
                return 25  # 超卖区做空风险大

    def _score_mfi(self, md: MarketData, is_long: bool) -> Optional[float]:
        """
        MFI资金流量指数评分

        MFI是量加权的RSI，范围0-100
        - 做多：MFI < 20 超卖买入，MFI > 80 超买避免
        - 做空：MFI > 80 超买卖出，MFI < 20 超卖避免
        """
        if md.mfi_14 is None:
            return None

        mfi = float(md.mfi_14)

        if is_long:
            if mfi < 20:
                return 95  # 资金严重流出，买入良机
            elif mfi < 30:
                return 80  # 资金流出
            elif mfi < 50:
                return 65  # 中性偏弱
            elif mfi < 70:
                return 50  # 中性
            elif mfi < 80:
                return 35  # 资金流入强
            else:
                return 20  # 超买
        else:
            if mfi > 80:
                return 95  # 资金严重流入，卖出良机
            elif mfi > 70:
                return 80  # 资金流入
            elif mfi > 50:
                return 65  # 中性偏强
            elif mfi > 30:
                return 50  # 中性
            elif mfi > 20:
                return 35  # 资金流出强
            else:
                return 20  # 超卖

    def _score_ichimoku(self, md: MarketData, is_long: bool) -> Optional[float]:
        """
        Ichimoku一目均衡图评分

        评分维度：
        1. 价格相对云图位置
        2. 转换线与基准线关系
        3. 迟行线位置
        """
        # 检查必要数据
        if md.close is None:
            return None

        close = float(md.close)
        scores = []

        # 1. 云图位置评分
        if md.ichi_senkou_a is not None and md.ichi_senkou_b is not None:
            senkou_a = float(md.ichi_senkou_a)
            senkou_b = float(md.ichi_senkou_b)
            cloud_top = max(senkou_a, senkou_b)
            cloud_bottom = min(senkou_a, senkou_b)

            if is_long:
                if close > cloud_top:
                    scores.append(90)  # 价格在云上方，强势
                elif close > cloud_bottom:
                    scores.append(60)  # 价格在云中
                else:
                    scores.append(30)  # 价格在云下方
            else:
                if close < cloud_bottom:
                    scores.append(90)  # 价格在云下方，弱势
                elif close < cloud_top:
                    scores.append(60)  # 价格在云中
                else:
                    scores.append(30)  # 价格在云上方

        # 2. 转换线与基准线关系
        if md.ichi_tenkan is not None and md.ichi_kijun is not None:
            tenkan = float(md.ichi_tenkan)
            kijun = float(md.ichi_kijun)

            if is_long:
                if tenkan > kijun:
                    scores.append(85)  # 金叉
                else:
                    scores.append(40)  # 死叉
            else:
                if tenkan < kijun:
                    scores.append(85)  # 死叉
                else:
                    scores.append(40)  # 金叉

        return np.mean(scores) if scores else None

    def _score_squeeze(self, md: MarketData) -> Optional[float]:
        """
        布林带挤压信号评分

        bb_squeeze = 1 表示布林带在肯特纳通道内（挤压状态）
        挤压通常预示即将有大波动
        """
        if md.bb_squeeze is None:
            return None

        if md.bb_squeeze == 1:
            return 85  # 挤压状态，准备突破
        else:
            return 60  # 非挤压状态

    def _score_supertrend(self, md: MarketData, is_long: bool) -> Optional[float]:
        """
        SuperTrend方向评分

        supertrend_dir: 1=多头, -1=空头
        """
        if md.supertrend_dir is None:
            return None

        if is_long:
            if md.supertrend_dir == 1:
                return 90  # SuperTrend多头，顺势做多
            else:
                return 35  # SuperTrend空头，逆势做多
        else:
            if md.supertrend_dir == -1:
                return 90  # SuperTrend空头，顺势做空
            else:
                return 35  # SuperTrend多头，逆势做空

    def _score_psar(self, md: MarketData, is_long: bool) -> Optional[float]:
        """
        Parabolic SAR评分

        psar_dir: 1=多头, -1=空头
        """
        if md.psar_dir is None:
            return None

        if is_long:
            if md.psar_dir == 1:
                return 85  # SAR在价格下方，多头
            else:
                return 40  # SAR在价格上方，空头
        else:
            if md.psar_dir == -1:
                return 85  # SAR在价格上方，空头
            else:
                return 40  # SAR在价格下方，多头

    def _score_williams_r(self, md: MarketData, is_long: bool) -> Optional[float]:
        """
        Williams %R评分

        范围: -100 ~ 0
        - < -80: 超卖
        - > -20: 超买
        """
        if md.willr_14 is None:
            return None

        willr = float(md.willr_14)

        if is_long:
            if willr < -80:
                return 90  # 超卖，买入良机
            elif willr < -60:
                return 75  # 偏弱
            elif willr < -40:
                return 55  # 中性
            elif willr < -20:
                return 40  # 偏强
            else:
                return 25  # 超买
        else:
            if willr > -20:
                return 90  # 超买，卖出良机
            elif willr > -40:
                return 75  # 偏强
            elif willr > -60:
                return 55  # 中性
            elif willr > -80:
                return 40  # 偏弱
            else:
                return 25  # 超卖

    def _score_volatility_environment(self, md: MarketData) -> Optional[float]:
        """
        波动率环境评分

        使用hvol_20（历史波动率）和atr_pct评估
        """
        scores = []

        # ATR百分比评分
        if md.atr_pct is not None:
            atr_pct = float(md.atr_pct)
            if atr_pct < 2:
                scores.append(90)  # 低波动
            elif atr_pct < 3:
                scores.append(75)  # 中等波动
            elif atr_pct < 5:
                scores.append(55)  # 中高波动
            else:
                scores.append(40)  # 高波动

        # 波动率排名评分
        if md.vol_rank is not None:
            vol_rank = float(md.vol_rank)
            if vol_rank < 25:
                scores.append(85)  # 低位波动率
            elif vol_rank < 50:
                scores.append(70)  # 中等波动率
            elif vol_rank < 75:
                scores.append(55)  # 中高波动率
            else:
                scores.append(40)  # 高位波动率

        return np.mean(scores) if scores else None

    def _score_entry_position(
        self,
        position: Position,
        md: MarketData
    ) -> float:
        """
        评估进场价格相对关键支撑/阻力位置

        使用均线作为支撑/阻力参考
        """
        if md.close is None:
            return 50.0

        scores = []
        is_long = position.direction in ['buy', 'buy_to_open', 'long']

        # 检查与MA20的关系（短期支撑/阻力）
        if md.ma_20 is not None:
            distance_pct = abs((float(md.close) - float(md.ma_20)) / float(md.ma_20) * 100)

            if is_long:
                # 做多：接近MA20支撑
                if float(md.close) >= float(md.ma_20) * 0.98 and float(md.close) <= float(md.ma_20) * 1.02:
                    ma20_score = 90  # 在MA20附近
                elif float(md.close) < float(md.ma_20):
                    ma20_score = 75  # 略低于MA20
                elif distance_pct < 3:
                    ma20_score = 65
                else:
                    ma20_score = 50
            else:
                # 做空：远离MA20
                if float(md.close) > float(md.ma_20) * 1.05:
                    ma20_score = 85
                elif float(md.close) > float(md.ma_20):
                    ma20_score = 70
                else:
                    ma20_score = 50

            scores.append(ma20_score)

        # 检查与MA50的关系（中期支撑/阻力）
        if md.ma_50 is not None:
            if is_long:
                # 做多：接近MA50强支撑
                if float(md.close) >= float(md.ma_50) * 0.98 and float(md.close) <= float(md.ma_50) * 1.02:
                    ma50_score = 95  # 在MA50附近
                elif float(md.close) < float(md.ma_50):
                    ma50_score = 80
                else:
                    ma50_score = 60
            else:
                # 做空：远离MA50
                if float(md.close) > float(md.ma_50) * 1.05:
                    ma50_score = 85
                else:
                    ma50_score = 60

            scores.append(ma50_score)

        return np.mean(scores) if scores else 50.0

    def _score_entry_volume(
        self,
        position: Position,
        md: MarketData
    ) -> float:
        """
        评估进场时的成交量确认

        使用成交量与20日均量的比值评估
        """
        # 复用 _score_volume_confirmation 方法
        score = self._score_volume_confirmation(md)
        return score if score is not None else 60.0

    # ==================== 出场质量评分（25%权重）====================

    def score_exit_quality(
        self,
        position: Position,
        exit_market_data: Optional[MarketData]
    ) -> Dict[str, float]:
        """
        评估出场质量（0-100分）

        Args:
            position: Position对象
            exit_market_data: 出场时的市场数据

        Returns:
            dict: {
                'exit_score': 总分,
                'timing_score': 时机得分,
                'target_score': 目标达成得分,
                'stop_score': 止损执行得分,
                'duration_score': 持仓时间得分
            }
        """
        # 1. 出场时机（40%）- 基于技术指标
        timing_score = self._score_exit_timing(position, exit_market_data)

        # 2. 盈亏目标达成（30%）
        target_score = self._score_profit_target(position)

        # 3. 止损执行（20%）
        stop_score = self._score_stop_loss(position)

        # 4. 持仓时间合理性（10%）
        duration_score = self._score_holding_duration(position)

        # 加权计算
        exit_score = (
            timing_score * 0.40 +
            target_score * 0.30 +
            stop_score * 0.20 +
            duration_score * 0.10
        )

        return {
            'exit_score': exit_score,
            'timing_score': timing_score,
            'target_score': target_score,
            'stop_score': stop_score,
            'duration_score': duration_score
        }

    def _score_exit_timing(
        self,
        position: Position,
        md: Optional[MarketData]
    ) -> float:
        """评估出场时机（基于技术指标）"""
        if not md:
            return 60.0

        is_long = position.direction in ['buy', 'buy_to_open', 'long']
        is_profit = position.realized_pnl and position.realized_pnl > 0
        scores = []

        # RSI出场评分
        if md.rsi_14 is not None:
            if is_long and is_profit:
                # 做多盈利：RSI高位出场好
                if md.rsi_14 > 70:
                    rsi_score = 90
                elif md.rsi_14 > 60:
                    rsi_score = 75
                else:
                    rsi_score = 60
            elif is_long and not is_profit:
                # 做多亏损：RSI低于50出场合理
                rsi_score = 70 if md.rsi_14 < 50 else 55
            elif not is_long and is_profit:
                # 做空盈利：RSI低位出场好
                if md.rsi_14 < 30:
                    rsi_score = 90
                elif md.rsi_14 < 40:
                    rsi_score = 75
                else:
                    rsi_score = 60
            else:
                # 做空亏损：RSI高于50出场合理
                rsi_score = 70 if md.rsi_14 > 50 else 55

            scores.append(rsi_score)

        # MACD出场评分
        if md.macd is not None and md.macd_signal is not None:
            macd_diff = float(md.macd) - float(md.macd_signal)

            if is_long and is_profit:
                # 做多盈利：死叉时出场好
                macd_score = 85 if macd_diff < 0 else 65
            elif is_long and not is_profit:
                # 做多亏损：任何时候止损都合理
                macd_score = 75
            elif not is_long and is_profit:
                # 做空盈利：金叉时出场好
                macd_score = 85 if macd_diff > 0 else 65
            else:
                # 做空亏损：任何时候止损都合理
                macd_score = 75

            scores.append(macd_score)

        return np.mean(scores) if scores else 60.0

    def _score_profit_target(self, position: Position) -> float:
        """评估盈亏目标达成情况"""
        if position.realized_pnl is None:
            return 50.0

        pnl_pct = position.realized_pnl_pct or 0

        # 基于盈亏百分比评分
        if pnl_pct >= 5.0:
            return 95  # 大幅盈利
        elif pnl_pct >= 3.0:
            return 85  # 良好盈利
        elif pnl_pct >= 1.0:
            return 75  # 小幅盈利
        elif pnl_pct >= 0:
            return 60  # 微利
        elif pnl_pct >= -1.0:
            return 55  # 小亏
        elif pnl_pct >= -2.0:
            return 70  # 控制在2%内，止损及时
        elif pnl_pct >= -3.0:
            return 60  # 止损稍晚
        else:
            return 40  # 大幅亏损，止损太晚

    def _score_stop_loss(self, position: Position) -> float:
        """
        评估止损执行

        使用MAE（最大不利偏移）评估
        """
        if position.mae_pct is None:
            return 65.0  # 无MAE数据

        mae_pct = position.mae_pct

        # 基于MAE评分（控制回撤能力）
        if abs(mae_pct) <= 1.0:
            return 95  # 回撤控制极好
        elif abs(mae_pct) <= 2.0:
            return 85  # 回撤控制良好
        elif abs(mae_pct) <= 3.0:
            return 70  # 回撤控制尚可
        elif abs(mae_pct) <= 5.0:
            return 55  # 回撤较大
        else:
            return 40  # 回撤过大

    def _score_holding_duration(self, position: Position) -> float:
        """
        评估持仓时间合理性

        基于持仓效率：日均收益率
        """
        if not position.holding_period_days or position.holding_period_days <= 0:
            return 50.0

        if position.realized_pnl is None:
            return 50.0

        # 计算日均收益率
        daily_return = (position.realized_pnl_pct or 0) / position.holding_period_days

        # 基于日均收益率评分
        if daily_return >= 0.5:
            return 95  # 高效率
        elif daily_return >= 0.3:
            return 85  # 良好效率
        elif daily_return >= 0.1:
            return 75  # 中等效率
        elif daily_return >= 0:
            return 60  # 低效率但盈利
        elif daily_return >= -0.1:
            return 55  # 小幅亏损
        else:
            return 40  # 效率差

    # ==================== 趋势把握评分（25%权重）====================

    def score_trend_quality(
        self,
        position: Position,
        entry_market_data: Optional[MarketData],
        exit_market_data: Optional[MarketData]
    ) -> Dict[str, float]:
        """
        评估趋势把握质量（0-100分）

        Args:
            position: Position对象
            entry_market_data: 进场时市场数据
            exit_market_data: 出场时市场数据

        Returns:
            dict: {
                'trend_score': 总分,
                'direction_score': 方向一致性得分,
                'strength_score': 趋势强度得分,
                'consistency_score': 趋势持续性得分
            }
        """
        # 1. 趋势方向一致性（40%）
        direction_score = self._score_trend_direction(position, entry_market_data)

        # 2. 趋势强度（30%）
        strength_score = self._score_trend_strength(entry_market_data)

        # 3. 趋势持续性（30%）- 对比进出场
        consistency_score = self._score_trend_consistency(
            position, entry_market_data, exit_market_data
        )

        # 加权计算
        trend_score = (
            direction_score * 0.40 +
            strength_score * 0.30 +
            consistency_score * 0.30
        )

        return {
            'trend_score': trend_score,
            'direction_score': direction_score,
            'strength_score': strength_score,
            'consistency_score': consistency_score
        }

    def _score_trend_direction(
        self,
        position: Position,
        md: Optional[MarketData]
    ) -> float:
        """评估交易方向与趋势的一致性"""
        if not md:
            return 50.0

        is_long = position.direction in ['buy', 'buy_to_open', 'long']
        confirmations = 0
        total_checks = 0

        # 均线趋势确认
        if md.ma_5 and md.ma_20 and md.ma_50:
            total_checks += 1
            if is_long:
                # 做多：均线多头排列
                if float(md.ma_5) > float(md.ma_20) > float(md.ma_50):
                    confirmations += 1
            else:
                # 做空：均线空头排列
                if float(md.ma_5) < float(md.ma_20) < float(md.ma_50):
                    confirmations += 1

        # MACD趋势确认
        if md.macd is not None:
            total_checks += 1
            if is_long and float(md.macd) > 0:
                confirmations += 1
            elif not is_long and float(md.macd) < 0:
                confirmations += 1

        # 价格相对MA的位置
        if md.close and md.ma_20:
            total_checks += 1
            if is_long and float(md.close) > float(md.ma_20):
                confirmations += 1
            elif not is_long and float(md.close) < float(md.ma_20):
                confirmations += 1

        if total_checks == 0:
            return 50.0

        # 根据确认比例评分
        confirm_ratio = confirmations / total_checks
        if confirm_ratio >= 0.8:
            return 95
        elif confirm_ratio >= 0.6:
            return 80
        elif confirm_ratio >= 0.4:
            return 65
        else:
            return 45

    def _score_trend_strength(self, md: Optional[MarketData]) -> float:
        """
        评估趋势强度

        使用ADX作为主要趋势强度指标（权重50%）
        辅以均线分离度（权重30%）和MACD柱状图强度（权重20%）
        """
        if not md:
            return 50.0

        weighted_scores = []

        # 1. ADX趋势强度（权重50%）- 主要指标
        if md.adx is not None:
            adx = float(md.adx)

            if adx >= ADX_STRONG_TREND:
                adx_score = 95  # 强趋势
            elif adx >= ADX_MODERATE_TREND:
                adx_score = 80  # 中等趋势
            elif adx >= ADX_WEAK_TREND:
                adx_score = 60  # 弱趋势
            else:
                adx_score = 40  # 震荡市

            weighted_scores.append((adx_score, 0.50))

        # 2. 均线分离度（权重30%）
        if md.ma_5 and md.ma_20 and md.ma_50:
            # 计算MA5与MA50的分离度
            separation = abs((float(md.ma_5) - float(md.ma_50)) / float(md.ma_50) * 100)

            if separation >= 10:
                ma_score = 90  # 强趋势
            elif separation >= 5:
                ma_score = 75  # 中等趋势
            elif separation >= 2:
                ma_score = 60  # 弱趋势
            else:
                ma_score = 45  # 震荡

            weighted_scores.append((ma_score, 0.30))

        # 3. MACD柱状图强度（权重20%）
        if md.macd_hist is not None:
            hist_abs = abs(md.macd_hist)

            if hist_abs >= 2.0:
                macd_score = 85
            elif hist_abs >= 1.0:
                macd_score = 70
            elif hist_abs >= 0.5:
                macd_score = 60
            else:
                macd_score = 50

            weighted_scores.append((macd_score, 0.20))

        # 计算加权平均
        if not weighted_scores:
            return 50.0

        total_weight = sum(w for _, w in weighted_scores)
        weighted_sum = sum(s * w for s, w in weighted_scores)

        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _score_trend_consistency(
        self,
        position: Position,
        entry_md: Optional[MarketData],
        exit_md: Optional[MarketData]
    ) -> float:
        """评估持仓期间趋势的持续性"""
        # 简化版本：基于最终盈亏判断趋势是否持续
        if position.realized_pnl is None:
            return 50.0

        is_profit = position.realized_pnl > 0

        if is_profit:
            # 盈利说明趋势持续，按盈亏幅度评分
            pnl_pct = position.realized_pnl_pct or 0
            if pnl_pct >= 5.0:
                return 95
            elif pnl_pct >= 3.0:
                return 85
            elif pnl_pct >= 1.0:
                return 75
            else:
                return 65
        else:
            # 亏损说明趋势未持续或逆转
            pnl_pct = abs(position.realized_pnl_pct or 0)
            if pnl_pct <= 2.0:
                return 60  # 及时止损
            else:
                return 40  # 趋势逆转损失大

    # ==================== 风险管理评分（20%权重）====================

    def score_risk_management(
        self,
        position: Position,
        entry_market_data: Optional[MarketData]
    ) -> Dict[str, float]:
        """
        评估风险管理质量（0-100分）

        Args:
            position: Position对象
            entry_market_data: 进场时市场数据

        Returns:
            dict: {
                'risk_score': 总分,
                'rr_ratio_score': RR比得分,
                'mae_mfe_score': MAE/MFE得分,
                'position_size_score': 仓位管理得分
            }
        """
        # 1. 计划RR比（40%）- 使用ATR估算
        rr_ratio_score = self._score_risk_reward_ratio(position, entry_market_data)

        # 2. 实际RR比（30%）- MAE vs MFE
        mae_mfe_score = self._score_mae_mfe(position)

        # 3. 仓位管理（30%）
        position_size_score = self._score_position_size(position)

        # 加权计算
        risk_score = (
            rr_ratio_score * 0.40 +
            mae_mfe_score * 0.30 +
            position_size_score * 0.30
        )

        return {
            'risk_score': risk_score,
            'rr_ratio_score': rr_ratio_score,
            'mae_mfe_score': mae_mfe_score,
            'position_size_score': position_size_score
        }

    def _score_risk_reward_ratio(
        self,
        position: Position,
        md: Optional[MarketData]
    ) -> float:
        """
        评估风险收益比

        理想止损距离 = 1.5-2倍ATR
        理想目标 = 2-3倍止损
        """
        if not md or not md.atr_14:
            return 60.0

        # 使用ATR估算合理止损
        ideal_stop_distance = 1.5 * float(md.atr_14)
        ideal_target = 2.0 * ideal_stop_distance

        # 计算潜在RR比
        potential_rr = ideal_target / ideal_stop_distance if ideal_stop_distance > 0 else 0

        # 评分
        if potential_rr >= 2.5:
            return 95
        elif potential_rr >= 2.0:
            return 85
        elif potential_rr >= 1.5:
            return 70
        elif potential_rr >= 1.0:
            return 55
        else:
            return 40

    def _score_mae_mfe(self, position: Position) -> float:
        """
        评估实际风险收益比（MAE vs MFE）

        MAE: Maximum Adverse Excursion（最大不利偏移）
        MFE: Maximum Favorable Excursion（最大有利偏移）
        """
        if position.mae_pct is None or position.mfe_pct is None:
            return 60.0

        mae_abs = abs(position.mae_pct)
        mfe_abs = abs(position.mfe_pct)

        if mae_abs == 0:
            return 90  # 无回撤

        # 计算MFE/MAE比率
        ratio = mfe_abs / mae_abs if mae_abs > 0 else 0

        if ratio >= 3.0:
            return 95  # 优秀RR比
        elif ratio >= 2.0:
            return 85  # 良好RR比
        elif ratio >= 1.5:
            return 75  # 尚可
        elif ratio >= 1.0:
            return 60  # 勉强盈亏平衡
        else:
            return 45  # RR比差

    def _score_position_size(self, position: Position) -> float:
        """
        评估仓位管理

        注意：当前版本简化处理，未来可增加账户总资金计算
        """
        # 简化版本：基于交易金额评分
        # 假设理想单笔交易金额在1000-5000美元

        if position.open_price is None or position.quantity is None:
            return 60.0

        # 计算开仓金额
        amount = abs(float(position.open_price) * position.quantity)

        if 1000 <= amount <= 5000:
            return 85  # 理想仓位
        elif 500 <= amount < 1000 or 5000 < amount <= 10000:
            return 70  # 偏小或偏大
        elif amount < 500:
            return 60  # 仓位过小
        else:
            return 50  # 仓位过大

    # ==================== 综合评分 ====================

    def calculate_overall_score(
        self,
        session: Session,
        position: Position
    ) -> Dict[str, Any]:
        """
        计算交易的综合质量评分

        Args:
            session: Database session
            position: Position对象

        Returns:
            dict: 包含所有评分维度和综合评分
        """
        # 获取进场和出场时的市场数据
        entry_md = self._get_market_data(
            session, position.symbol, position.open_time
        )
        exit_md = self._get_market_data(
            session, position.symbol, position.close_time
        ) if position.close_time else None

        # 计算基础四维度评分
        entry_result = self.score_entry_quality(position, entry_md)
        exit_result = self.score_exit_quality(position, exit_md)
        trend_result = self.score_trend_quality(position, entry_md, exit_md)
        risk_result = self.score_risk_management(position, entry_md)

        # V2: 计算新增维度评分
        if self.use_v2:
            return self._calculate_v2_score(
                session, position, entry_md, exit_md,
                entry_result, exit_result, trend_result, risk_result
            )
        else:
            # V1 兼容模式
            overall_score = (
                entry_result['entry_score'] * self.weights['entry'] +
                exit_result['exit_score'] * self.weights['exit'] +
                trend_result['trend_score'] * self.weights['trend'] +
                risk_result['risk_score'] * self.weights['risk']
            )

            grade = self._assign_grade(overall_score)

            return {
                'overall_score': overall_score,
                'grade': grade,
                'entry_score': entry_result['entry_score'],
                'exit_score': exit_result['exit_score'],
                'trend_score': trend_result['trend_score'],
                'risk_score': risk_result['risk_score'],
                **entry_result,
                **exit_result,
                **trend_result,
                **risk_result
            }

    def _calculate_v2_score(
        self,
        session: Session,
        position: Position,
        entry_md: Optional[MarketData],
        exit_md: Optional[MarketData],
        entry_result: Dict,
        exit_result: Dict,
        trend_result: Dict,
        risk_result: Dict
    ) -> Dict[str, Any]:
        """
        计算V2版本8维度评分

        Args:
            session: Database session
            position: Position对象
            entry_md: 入场市场数据
            exit_md: 出场市场数据
            entry_result: 入场评分结果
            exit_result: 出场评分结果
            trend_result: 趋势评分结果
            risk_result: 风险评分结果

        Returns:
            完整的评分结果字典
        """
        score_details = {}

        # 1. 市场环境评分
        trade_date = position.open_date or (
            position.open_time.date() if position.open_time else None
        )
        if trade_date:
            market_snapshot = self.market_env_scorer.get_market_snapshot(
                session, trade_date
            )
            market_env_result = self.market_env_scorer.score(
                trade_date=trade_date,
                direction=position.direction,
                symbol=position.symbol,
                market_snapshot=market_snapshot,
                market_data=entry_md
            )
            market_env_score = market_env_result.total_score
            score_details['market_env'] = market_env_result.details
        else:
            market_env_score = 70.0
            score_details['market_env'] = {'status': 'no_date'}

        # 2. 交易行为评分
        recent_trades = self.behavior_scorer.get_recent_trades(
            session,
            symbol=position.underlying_symbol or position.symbol,
            before_date=position.open_time,
            days=7
        ) if position.open_time else []

        historical_prices = self._get_historical_prices(entry_md)

        behavior_result = self.behavior_scorer.score(
            position=position,
            market_data=entry_md,
            recent_trades=recent_trades,
            historical_prices=historical_prices
        )
        behavior_score = behavior_result.total_score
        score_details['behavior'] = behavior_result.details
        behavior_warnings = behavior_result.warnings

        # 3. 执行质量评分
        trades = list(position.trades) if hasattr(position, 'trades') else None
        execution_result = self.execution_scorer.score(
            position=position,
            trades=trades
        )
        execution_score = execution_result.total_score
        score_details['execution'] = execution_result.details

        # 4. 期权评分 (仅期权)
        is_option = bool(position.is_option)
        if is_option:
            options_score = self._calculate_options_score(position, entry_md, exit_md)
            score_details['options'] = {'score': options_score}
        else:
            options_score = None

        # 5. 新闻契合度评分 (可选)
        news_alignment_score = None
        news_search_result = None
        news_alignment_result = None

        if self.news_search_enabled and self.news_searcher and trade_date:
            try:
                # 搜索新闻
                underlying = position.underlying_symbol or position.symbol
                news_search_result = self.news_searcher.search(
                    symbol=position.symbol,
                    trade_date=trade_date,
                    range_days=NEWS_SEARCH_RANGE_DAYS,
                    underlying_symbol=underlying if position.is_option else None
                )

                # 计算新闻契合度评分
                news_alignment_result = self.news_alignment_scorer.score(
                    news_result=news_search_result,
                    position_direction=position.direction or 'long',
                    position_open_date=trade_date
                )

                news_alignment_score = news_alignment_result.overall_score
                score_details['news_alignment'] = {
                    'score': news_alignment_score,
                    'news_count': news_search_result.news_count,
                    'sentiment': news_search_result.overall_sentiment,
                    'impact_level': news_search_result.news_impact_level,
                    'breakdown': news_alignment_result.breakdown,
                    'warnings': news_alignment_result.warnings,
                }

                logger.debug(
                    f"News alignment score for {position.symbol}: "
                    f"{news_alignment_score:.1f} (news={news_search_result.news_count})"
                )

            except Exception as e:
                logger.warning(f"News alignment scoring failed for position {position.id}: {e}")
                news_alignment_score = 50.0  # 失败时给默认分
                score_details['news_alignment'] = {'error': str(e)}

        # 计算综合评分
        weights = self.weights.copy()

        # 非期权时重新分配期权权重
        if not is_option:
            options_weight = weights.pop('options', 0)
            # 将期权权重分配给其他维度
            remaining_weights = [k for k in weights if k != 'news_alignment']
            for key in remaining_weights:
                weights[key] += options_weight / len(remaining_weights)

        # 新闻搜索未启用时重新分配权重
        if not self.news_search_enabled or news_alignment_score is None:
            news_weight = weights.pop('news_alignment', 0)
            remaining_weights = list(weights.keys())
            for key in remaining_weights:
                weights[key] += news_weight / len(remaining_weights)

        overall_score = (
            entry_result['entry_score'] * weights['entry'] +
            exit_result['exit_score'] * weights['exit'] +
            market_env_score * weights['market_env'] +
            behavior_score * weights['behavior'] +
            trend_result['trend_score'] * weights['trend'] +
            risk_result['risk_score'] * weights['risk'] +
            execution_score * weights['execution']
        )

        if is_option and options_score is not None:
            overall_score += options_score * weights.get('options', 0.05)

        # 添加新闻契合度评分
        if news_alignment_score is not None and 'news_alignment' in weights:
            overall_score += news_alignment_score * weights['news_alignment']

        grade = self._assign_grade(overall_score)

        # 构建完整结果
        result = {
            'overall_score': round(overall_score, 2),
            'grade': grade,
            # 9维度评分
            'entry_score': entry_result['entry_score'],
            'exit_score': exit_result['exit_score'],
            'market_env_score': market_env_score,
            'behavior_score': behavior_score,
            'trend_score': trend_result['trend_score'],
            'risk_score': risk_result['risk_score'],
            'execution_score': execution_score,
            'options_greeks_score': options_score,
            'news_alignment_score': news_alignment_score,
            # 新闻搜索结果 (用于保存到 NewsContext)
            'news_search_result': news_search_result,
            'news_alignment_result': news_alignment_result,
            # 详细信息
            'score_details': score_details,
            'behavior_warnings': behavior_warnings,
            # 兼容旧字段
            **entry_result,
            **exit_result,
            **trend_result,
            **risk_result
        }

        return result

    def _get_historical_prices(self, md: Optional[MarketData]) -> Optional[Dict]:
        """从市场数据提取历史价格信息"""
        if not md:
            return None

        result = {}

        if hasattr(md, 'high') and md.high:
            result['high_5d'] = float(md.high) * 1.02  # 估算
        if hasattr(md, 'low') and md.low:
            result['low_5d'] = float(md.low) * 0.98  # 估算
        if hasattr(md, 'prev_close') and md.prev_close:
            result['prev_close'] = float(md.prev_close)
        if hasattr(md, 'change_pct') and md.change_pct:
            result['prev_change_pct'] = float(md.change_pct)

        return result if result else None

    def _calculate_options_score(
        self,
        position: Position,
        entry_md: Optional[MarketData],
        exit_md: Optional[MarketData]
    ) -> float:
        """
        计算期权希腊字母评分

        简化版本: 基于现有期权评分
        """
        scores = []

        if position.option_entry_score:
            scores.append(float(position.option_entry_score))
        if position.option_exit_score:
            scores.append(float(position.option_exit_score))
        if position.option_strategy_score:
            scores.append(float(position.option_strategy_score))

        if scores:
            return sum(scores) / len(scores)
        else:
            return 70.0  # 默认分数

    def _preload_market_data(
        self,
        session: Session,
        positions: list
    ) -> None:
        """
        批量预加载所有需要的 MarketData，避免 N+1 查询

        将 1000+ 次查询减少到 1 次，提升评分速度 5-10 倍

        Args:
            session: Database session
            positions: Position 列表
        """
        if not positions:
            return

        # 清空旧缓存
        self._market_data_cache.clear()

        # 收集所有需要查询的 (symbol, date) 组合
        symbol_dates = set()
        for position in positions:
            # 处理 symbol（期权需要转换为标的）
            symbol = position.symbol
            if OptionParser.is_option_symbol(symbol):
                symbol = OptionParser.extract_underlying(symbol)

            # 进场日期
            if position.open_time:
                open_date = position.open_time.date() if hasattr(position.open_time, 'date') else position.open_time
                symbol_dates.add((symbol, open_date))

            # 出场日期
            if position.close_time:
                close_date = position.close_time.date() if hasattr(position.close_time, 'date') else position.close_time
                symbol_dates.add((symbol, close_date))

        if not symbol_dates:
            logger.info("No market data to preload")
            return

        logger.info(f"Preloading market data for {len(symbol_dates)} symbol-date combinations...")

        # 一次性查询所有需要的 MarketData
        # 使用 OR 条件批量查询
        from sqlalchemy import or_, and_

        conditions = [
            and_(MarketData.symbol == symbol, MarketData.date == date)
            for symbol, date in symbol_dates
        ]

        market_data_list = session.query(MarketData).filter(
            or_(*conditions)
        ).all()

        # 构建缓存字典
        for md in market_data_list:
            date_str = str(md.date)
            cache_key = (md.symbol, date_str)
            self._market_data_cache[cache_key] = md

        # 对于没有找到数据的组合，缓存 None 避免重复查询
        for symbol, date in symbol_dates:
            date_str = str(date)
            cache_key = (symbol, date_str)
            if cache_key not in self._market_data_cache:
                self._market_data_cache[cache_key] = None

        logger.info(f"Preloaded {len(market_data_list)} market data records into cache")

    def _get_market_data(
        self,
        session: Session,
        symbol: str,
        timestamp: Optional[datetime]
    ) -> Optional[MarketData]:
        """
        获取指定时间的市场数据（支持缓存优化）

        查找最接近指定时间的市场数据记录
        批量评分时优先从缓存获取，避免 N+1 查询

        对于期权符号，自动使用标的股票的市场数据
        """
        if not timestamp:
            return None

        try:
            # 检查是否为期权，如果是则使用标的股票
            if OptionParser.is_option_symbol(symbol):
                underlying = OptionParser.extract_underlying(symbol)
                logger.debug(f"Option detected: {symbol} → Using underlying: {underlying}")
                search_symbol = underlying
            else:
                search_symbol = symbol

            # 获取目标日期
            target_date = timestamp.date() if hasattr(timestamp, 'date') else timestamp
            date_str = str(target_date)

            # 优先从缓存获取（批量评分时已预加载）
            cache_key = (search_symbol, date_str)
            if cache_key in self._market_data_cache:
                return self._market_data_cache[cache_key]

            # 缓存未命中，执行数据库查询
            market_data = session.query(MarketData).filter(
                MarketData.symbol == search_symbol,
                MarketData.date == target_date
            ).first()

            # 如果没找到，尝试用timestamp查找最接近的
            if not market_data:
                market_data = session.query(MarketData).filter(
                    MarketData.symbol == search_symbol,
                    MarketData.timestamp <= timestamp
                ).order_by(
                    MarketData.timestamp.desc()
                ).first()

            if market_data:
                logger.debug(f"Found market data for {search_symbol} at {target_date}")
            else:
                logger.warning(f"No market data found for {search_symbol} at {target_date}")

            return market_data
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol} at {timestamp}: {e}")
            return None

    def _assign_grade(self, score: float) -> str:
        """
        根据分数分配等级

        等级划分：
        A+: 95-100, A: 90-94, A-: 85-89
        B+: 80-84, B: 75-79, B-: 70-74
        C+: 65-69, C: 60-64, C-: 55-59
        D: 50-54, F: 0-49
        """
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'B-'
        elif score >= 65:
            return 'C+'
        elif score >= 60:
            return 'C'
        elif score >= 55:
            return 'C-'
        elif score >= 50:
            return 'D'
        else:
            return 'F'

    # ==================== 期权专属评分 ====================

    def score_option_entry(
        self,
        position: Position,
        entry_market_data: Optional[MarketData],
        option_info: Dict
    ) -> Dict[str, float]:
        """
        期权入场质量评分（0-100分）

        评分维度：
        1. Moneyness选择 (25%): ATM通常风险/收益均衡
        2. 正股趋势一致性 (25%): Call要看涨趋势，Put要看跌
        3. 波动率环境 (25%): 低波动时买入期权更有利
        4. 时间价值 (25%): DTE是否与预期持有匹配

        Args:
            position: Position对象
            entry_market_data: 入场时标的股票的市场数据
            option_info: 期权合约信息 {type, strike, expiry, underlying}

        Returns:
            dict: 包含各维度评分和总分
        """
        if not entry_market_data or not option_info:
            return {'option_entry_score': 50.0}

        # 1. Moneyness选择评分 (25%)
        moneyness_score = self._score_option_moneyness(
            entry_market_data, option_info
        )

        # 2. 正股趋势一致性评分 (25%)
        trend_alignment_score = self._score_option_trend_alignment(
            entry_market_data, option_info
        )

        # 3. 波动率环境评分 (25%)
        volatility_score = self._score_option_volatility_entry(
            entry_market_data
        )

        # 4. 时间价值评分 (25%)
        time_value_score = self._score_option_time_value(option_info)

        # 加权计算总分
        option_entry_score = (
            moneyness_score * 0.25 +
            trend_alignment_score * 0.25 +
            volatility_score * 0.25 +
            time_value_score * 0.25
        )

        return {
            'option_entry_score': option_entry_score,
            'moneyness_score': moneyness_score,
            'trend_alignment_score': trend_alignment_score,
            'volatility_score': volatility_score,
            'time_value_score': time_value_score
        }

    def _score_option_moneyness(
        self,
        md: MarketData,
        option_info: Dict
    ) -> float:
        """
        评估期权Moneyness选择

        Moneyness = (正股价格 - 行权价) / 行权价
        - Call: 正值表示ITM，负值表示OTM
        - Put: 负值表示ITM，正值表示OTM

        评分逻辑：
        - ATM (-5% ~ +5%): 风险/收益均衡，适合大多数策略
        - 轻度OTM (-15% ~ -5%): 杠杆更高，适合方向性交易
        - 深度OTM (< -15%): 高风险高回报
        - ITM (> +5%): 更稳健，时间价值损耗小
        """
        if not md.close or not option_info.get('strike'):
            return 50.0

        stock_price = float(md.close)
        strike = float(option_info['strike'])
        option_type = option_info.get('type', '').lower()

        # 计算Moneyness百分比
        moneyness_pct = ((stock_price - strike) / strike) * 100

        # 根据期权类型调整
        if option_type == 'put':
            moneyness_pct = -moneyness_pct

        # 评分逻辑
        abs_moneyness = abs(moneyness_pct)

        if abs_moneyness <= 2:
            return 90  # ATM，最均衡
        elif abs_moneyness <= 5:
            return 85  # 接近ATM
        elif abs_moneyness <= 10:
            if moneyness_pct > 0:
                return 80  # 轻度ITM，稳健
            else:
                return 75  # 轻度OTM，适度杠杆
        elif abs_moneyness <= 15:
            if moneyness_pct > 0:
                return 70  # 中度ITM
            else:
                return 60  # 中度OTM，风险增加
        elif abs_moneyness <= 25:
            if moneyness_pct > 0:
                return 60  # 深度ITM，时间价值少
            else:
                return 45  # 深度OTM，高风险
        else:
            return 35  # 极端OTM/ITM

    def _score_option_trend_alignment(
        self,
        md: MarketData,
        option_info: Dict
    ) -> float:
        """
        评估期权类型与正股趋势的一致性

        - Call期权: 应在正股上涨趋势时买入
        - Put期权: 应在正股下跌趋势时买入

        使用多个技术指标综合判断趋势
        """
        option_type = option_info.get('type', '').lower()
        is_call = option_type == 'call'

        confirmations = 0
        total_checks = 0

        # 1. 价格相对MA20位置
        if md.ma_20 is not None and md.close is not None:
            total_checks += 1
            above_ma20 = float(md.close) > float(md.ma_20)
            if (is_call and above_ma20) or (not is_call and not above_ma20):
                confirmations += 1

        # 2. MA5 vs MA20 (短期趋势)
        if md.ma_5 is not None and md.ma_20 is not None:
            total_checks += 1
            ma_bullish = float(md.ma_5) > float(md.ma_20)
            if (is_call and ma_bullish) or (not is_call and not ma_bullish):
                confirmations += 1

        # 3. MACD方向
        if md.macd is not None:
            total_checks += 1
            macd_positive = float(md.macd) > 0
            if (is_call and macd_positive) or (not is_call and not macd_positive):
                confirmations += 1

        # 4. RSI位置
        if md.rsi_14 is not None:
            total_checks += 1
            rsi = float(md.rsi_14)
            if is_call:
                # Call: RSI < 70 且不在超买区
                if rsi < 70:
                    confirmations += 1
            else:
                # Put: RSI > 30 且不在超卖区
                if rsi > 30:
                    confirmations += 1

        # 5. ADX方向指标
        if md.plus_di is not None and md.minus_di is not None:
            total_checks += 1
            bullish_di = float(md.plus_di) > float(md.minus_di)
            if (is_call and bullish_di) or (not is_call and not bullish_di):
                confirmations += 1

        if total_checks == 0:
            return 50.0

        # 根据确认比例评分
        confirm_ratio = confirmations / total_checks
        if confirm_ratio >= 0.8:
            return 95  # 强趋势一致
        elif confirm_ratio >= 0.6:
            return 80  # 良好一致
        elif confirm_ratio >= 0.4:
            return 60  # 中等
        elif confirm_ratio >= 0.2:
            return 40  # 趋势不明确
        else:
            return 25  # 逆势交易

    def _score_option_volatility_entry(self, md: MarketData) -> float:
        """
        评估入场时的波动率环境

        买入期权时：
        - 低波动率环境更有利（期权便宜）
        - 高波动率环境不利（期权贵，且可能压缩）

        使用ATR和布林带宽度评估波动率
        """
        scores = []

        # 1. ATR相对价格的比率
        if md.atr_14 is not None and md.close is not None and float(md.close) > 0:
            atr_pct = (float(md.atr_14) / float(md.close)) * 100

            if atr_pct < 2:
                scores.append(90)  # 低波动，期权便宜
            elif atr_pct < 3:
                scores.append(80)  # 中低波动
            elif atr_pct < 4:
                scores.append(65)  # 中等波动
            elif atr_pct < 6:
                scores.append(50)  # 中高波动
            else:
                scores.append(35)  # 高波动，期权贵

        # 2. 布林带宽度
        if all([md.bb_upper, md.bb_lower, md.bb_middle]):
            bb_width = (float(md.bb_upper) - float(md.bb_lower)) / float(md.bb_middle) * 100

            if bb_width < 4:
                scores.append(90)  # 压缩，可能即将突破
            elif bb_width < 6:
                scores.append(75)  # 正常波动
            elif bb_width < 10:
                scores.append(55)  # 扩张中
            else:
                scores.append(40)  # 高波动

        return np.mean(scores) if scores else 60.0

    def _score_option_time_value(self, option_info: Dict) -> float:
        """
        评估期权时间价值（DTE合理性）

        DTE（Days to Expiry）分类：
        - 周期权 (< 7天): 时间价值损耗极快，需要方向快速验证
        - 短期 (7-21天): 时间价值损耗快，适合短线
        - 中期 (21-45天): 平衡点，最常用
        - 长期 (45-90天): 时间价值损耗慢，适合波动策略
        - 超长期 (> 90天): LEAPS，时间价值损耗最慢
        """
        dte = option_info.get('dte')

        if dte is None:
            return 50.0

        if dte < 7:
            return 40  # 周期权，高风险
        elif dte < 14:
            return 55  # 短期，时间压力大
        elif dte < 21:
            return 70  # 短中期
        elif dte < 45:
            return 90  # 最佳区间
        elif dte < 60:
            return 85  # 良好
        elif dte < 90:
            return 75  # 中长期
        elif dte < 180:
            return 65  # 长期
        else:
            return 55  # LEAPS，资金效率低

    def score_option_exit(
        self,
        position: Position,
        exit_market_data: Optional[MarketData],
        option_info: Dict
    ) -> Dict[str, float]:
        """
        期权出场质量评分（0-100分）

        评分维度：
        1. 正股方向有利性 (30%): 是否在正股有利方向时出场
        2. 时间价值剩余 (25%): 避免临近到期
        3. 盈利目标达成 (25%): 实际盈亏评估
        4. 止损执行 (20%): 是否及时止损

        Args:
            position: Position对象
            exit_market_data: 出场时标的股票的市场数据
            option_info: 期权合约信息

        Returns:
            dict: 包含各维度评分和总分
        """
        # 1. 正股方向有利性 (30%)
        direction_score = self._score_option_exit_direction(
            position, exit_market_data, option_info
        )

        # 2. 时间价值剩余 (25%)
        time_remaining_score = self._score_option_exit_time(option_info)

        # 3. 盈利目标达成 (25%)
        profit_score = self._score_option_profit(position)

        # 4. 止损执行 (20%)
        stop_score = self._score_option_stop_loss(position)

        # 加权计算总分
        option_exit_score = (
            direction_score * 0.30 +
            time_remaining_score * 0.25 +
            profit_score * 0.25 +
            stop_score * 0.20
        )

        return {
            'option_exit_score': option_exit_score,
            'direction_score': direction_score,
            'time_remaining_score': time_remaining_score,
            'profit_score': profit_score,
            'stop_score': stop_score
        }

    def _score_option_exit_direction(
        self,
        position: Position,
        md: Optional[MarketData],
        option_info: Dict
    ) -> float:
        """
        评估出场时正股方向是否有利

        盈利出场：
        - Call盈利: 正股应该上涨，技术指标应该到达目标
        - Put盈利: 正股应该下跌

        亏损出场：
        - 及时止损比拖延好
        """
        if not md:
            return 60.0

        is_profit = position.realized_pnl and float(position.realized_pnl) > 0
        option_type = option_info.get('type', '').lower()
        is_call = option_type == 'call'

        if is_profit:
            # 盈利出场评估
            confirmations = 0
            total_checks = 0

            # RSI是否到达目标区域
            if md.rsi_14 is not None:
                total_checks += 1
                rsi = float(md.rsi_14)
                if is_call and rsi > 60:  # Call盈利，RSI应该升高
                    confirmations += 1
                elif not is_call and rsi < 40:  # Put盈利，RSI应该降低
                    confirmations += 1

            # 价格相对布林带位置
            if all([md.bb_upper, md.bb_lower, md.close]):
                total_checks += 1
                bb_width = float(md.bb_upper) - float(md.bb_lower)
                if bb_width > 0:
                    bb_position = (float(md.close) - float(md.bb_lower)) / bb_width
                    if is_call and bb_position > 0.7:  # Call盈利，价格应在上轨
                        confirmations += 1
                    elif not is_call and bb_position < 0.3:  # Put盈利，价格应在下轨
                        confirmations += 1

            if total_checks > 0:
                ratio = confirmations / total_checks
                if ratio >= 0.5:
                    return 85  # 良好的盈利出场
                else:
                    return 70  # 可能提前出场
            return 75
        else:
            # 亏损出场 - 及时止损是好的
            pnl_pct = float(position.realized_pnl_pct or 0)
            if pnl_pct >= -20:
                return 75  # 控制在20%内
            elif pnl_pct >= -30:
                return 65  # 控制在30%内
            elif pnl_pct >= -50:
                return 50  # 损失较大
            else:
                return 35  # 损失过大

    def _score_option_exit_time(self, option_info: Dict) -> float:
        """
        评估出场时的剩余时间价值

        避免在DTE过低时出场（除非止损）
        """
        exit_dte = option_info.get('exit_dte')

        if exit_dte is None:
            return 60.0

        if exit_dte >= 21:
            return 90  # 充足时间价值
        elif exit_dte >= 14:
            return 80  # 良好
        elif exit_dte >= 7:
            return 65  # 时间压力增加
        elif exit_dte >= 3:
            return 50  # 临近到期
        elif exit_dte >= 1:
            return 40  # 危险区域
        else:
            return 30  # 到期日

    def _score_option_profit(self, position: Position) -> float:
        """
        评估期权盈利目标达成

        期权收益特点：
        - 盈利可以很大（几倍）
        - 亏损最多为本金（买入期权）
        """
        if position.realized_pnl is None:
            return 50.0

        pnl_pct = float(position.realized_pnl_pct or 0)

        if pnl_pct >= 100:
            return 100  # 翻倍
        elif pnl_pct >= 50:
            return 95  # 优秀
        elif pnl_pct >= 30:
            return 85  # 良好
        elif pnl_pct >= 15:
            return 75  # 不错
        elif pnl_pct >= 5:
            return 65  # 小赚
        elif pnl_pct >= 0:
            return 55  # 保本
        elif pnl_pct >= -20:
            return 60  # 止损及时
        elif pnl_pct >= -50:
            return 45  # 止损偏晚
        else:
            return 30  # 大亏

    def _score_option_stop_loss(self, position: Position) -> float:
        """
        评估期权止损执行

        使用MAE评估回撤控制
        """
        if position.mae_pct is None:
            return 60.0

        mae_pct = abs(float(position.mae_pct))

        if mae_pct <= 10:
            return 95  # 回撤控制极好
        elif mae_pct <= 20:
            return 85  # 良好
        elif mae_pct <= 30:
            return 70  # 尚可
        elif mae_pct <= 50:
            return 55  # 回撤较大
        else:
            return 40  # 回撤过大

    def score_option_strategy(
        self,
        position: Position,
        entry_market_data: Optional[MarketData],
        exit_market_data: Optional[MarketData],
        option_info: Dict
    ) -> Dict[str, float]:
        """
        期权策略整体评分（0-100分）

        评分维度：
        1. 到期日选择 (30%): DTE与实际持有时间匹配
        2. 行权价选择 (30%): Moneyness与策略匹配
        3. 方向判断 (20%): Call/Put选择正确性
        4. 执行效率 (20%): 实际收益vs理论最大收益

        Args:
            position: Position对象
            entry_market_data: 入场时市场数据
            exit_market_data: 出场时市场数据
            option_info: 期权合约信息

        Returns:
            dict: 包含各维度评分和总分
        """
        # 1. 到期日选择评分 (30%)
        expiry_score = self._score_option_expiry_selection(position, option_info)

        # 2. 行权价选择评分 (30%)
        strike_score = self._score_option_strike_selection(
            entry_market_data, exit_market_data, option_info
        )

        # 3. 方向判断评分 (20%)
        direction_score = self._score_option_direction_choice(
            position, entry_market_data, exit_market_data, option_info
        )

        # 4. 执行效率评分 (20%)
        efficiency_score = self._score_option_execution_efficiency(
            position, option_info
        )

        # 加权计算总分
        option_strategy_score = (
            expiry_score * 0.30 +
            strike_score * 0.30 +
            direction_score * 0.20 +
            efficiency_score * 0.20
        )

        return {
            'option_strategy_score': option_strategy_score,
            'expiry_score': expiry_score,
            'strike_score': strike_score,
            'direction_score': direction_score,
            'efficiency_score': efficiency_score
        }

    def _score_option_expiry_selection(
        self,
        position: Position,
        option_info: Dict
    ) -> float:
        """
        评估到期日选择是否合理

        好的到期日选择：
        - 持有时间应该少于DTE的一半（避免时间价值快速损耗）
        - 不应该持有到临近到期
        """
        entry_dte = option_info.get('dte')
        exit_dte = option_info.get('exit_dte')
        holding_days = position.holding_period_days

        if entry_dte is None or holding_days is None:
            return 60.0

        # 计算持有时间占DTE的比例
        hold_ratio = holding_days / entry_dte if entry_dte > 0 else 1

        if hold_ratio <= 0.3:
            return 95  # 持有时间适中
        elif hold_ratio <= 0.5:
            return 85  # 良好
        elif hold_ratio <= 0.7:
            return 70  # 持有偏长
        elif hold_ratio <= 0.9:
            return 55  # 持有太长
        else:
            return 40  # 持有到临近到期

    def _score_option_strike_selection(
        self,
        entry_md: Optional[MarketData],
        exit_md: Optional[MarketData],
        option_info: Dict
    ) -> float:
        """
        评估行权价选择是否合理

        好的行权价选择：
        - 如果盈利：行权价应该被触及或接近
        - 如果亏损：行权价选择可能过于激进
        """
        if not entry_md or not exit_md or not option_info.get('strike'):
            return 60.0

        strike = float(option_info['strike'])
        entry_price = float(entry_md.close) if entry_md.close else None
        exit_price = float(exit_md.close) if exit_md.close else None

        if not entry_price or not exit_price:
            return 60.0

        option_type = option_info.get('type', '').lower()

        # 计算价格变动
        price_change_pct = ((exit_price - entry_price) / entry_price) * 100

        # 计算strike相对入场价的位置
        strike_distance_pct = ((strike - entry_price) / entry_price) * 100

        if option_type == 'call':
            # Call期权：strike高于入场价
            if price_change_pct > 0:  # 正股上涨
                # 如果涨幅足够触及strike
                if exit_price >= strike:
                    return 95  # 完美选择
                elif exit_price >= strike * 0.98:
                    return 85  # 接近strike
                elif price_change_pct >= strike_distance_pct * 0.5:
                    return 70  # 涨了一半
                else:
                    return 55  # strike选太高
            else:  # 正股下跌
                if abs(strike_distance_pct) <= 5:
                    return 60  # ATM选择合理，方向错误
                else:
                    return 45  # OTM且方向错误
        else:  # Put
            strike_distance_pct = -strike_distance_pct  # Put的方向相反
            if price_change_pct < 0:  # 正股下跌
                if exit_price <= strike:
                    return 95
                elif exit_price <= strike * 1.02:
                    return 85
                elif abs(price_change_pct) >= abs(strike_distance_pct) * 0.5:
                    return 70
                else:
                    return 55
            else:
                if abs(strike_distance_pct) <= 5:
                    return 60
                else:
                    return 45

    def _score_option_direction_choice(
        self,
        position: Position,
        entry_md: Optional[MarketData],
        exit_md: Optional[MarketData],
        option_info: Dict
    ) -> float:
        """
        评估Call/Put方向选择是否正确

        基于实际结果评估：
        - 盈利 = 方向选择正确
        - 亏损 = 需要分析是否是方向错误还是执行问题
        """
        if position.realized_pnl is None:
            return 50.0

        is_profit = float(position.realized_pnl) > 0
        pnl_pct = float(position.realized_pnl_pct or 0)

        if is_profit:
            # 盈利情况下，按盈利幅度评分
            if pnl_pct >= 50:
                return 100  # 方向判断完美
            elif pnl_pct >= 20:
                return 90
            elif pnl_pct >= 10:
                return 80
            else:
                return 70  # 小赚，方向正确但幅度不大
        else:
            # 亏损情况下，分析是否可以改善
            if not entry_md or not exit_md:
                return 50.0

            # 检查正股实际走势
            entry_price = float(entry_md.close) if entry_md.close else None
            exit_price = float(exit_md.close) if exit_md.close else None

            if entry_price and exit_price:
                price_change = exit_price - entry_price
                option_type = option_info.get('type', '').lower()

                # 检查方向是否正确
                direction_correct = (
                    (option_type == 'call' and price_change > 0) or
                    (option_type == 'put' and price_change < 0)
                )

                if direction_correct:
                    return 55  # 方向对了但还是亏损（可能strike/dte问题）
                else:
                    # 方向错误
                    if pnl_pct >= -30:
                        return 45  # 及时止损
                    else:
                        return 30  # 方向错误且亏损大

            return 40

    def _score_option_execution_efficiency(
        self,
        position: Position,
        option_info: Dict
    ) -> float:
        """
        评估期权执行效率

        效率 = 实际盈亏 / 理论最大盈亏机会

        考虑因素：
        - 持有时间效率
        - 资金使用效率
        """
        if position.holding_period_days is None or position.holding_period_days <= 0:
            return 60.0

        if position.realized_pnl_pct is None:
            return 50.0

        pnl_pct = float(position.realized_pnl_pct)
        holding_days = position.holding_period_days

        # 计算日均收益率
        daily_return = pnl_pct / holding_days

        # 期权的日均收益期望更高
        if daily_return >= 5:
            return 100  # 极高效率
        elif daily_return >= 2:
            return 90  # 优秀
        elif daily_return >= 1:
            return 80  # 良好
        elif daily_return >= 0.5:
            return 70  # 中等
        elif daily_return >= 0:
            return 60  # 保本但低效
        elif daily_return >= -1:
            return 50  # 小亏
        elif daily_return >= -2:
            return 40  # 亏损
        else:
            return 30  # 大亏

    def calculate_option_overall_score(
        self,
        session: Session,
        position: Position
    ) -> Dict[str, float]:
        """
        计算期权交易的综合质量评分

        结合股票评分和期权专属评分

        Args:
            session: Database session
            position: Position对象（期权持仓）

        Returns:
            dict: 包含所有评分维度和综合评分
        """
        # 检查是否为期权
        if not OptionParser.is_option_symbol(position.symbol):
            logger.warning(f"Position {position.id} is not an option")
            return self.calculate_overall_score(session, position)

        # 解析期权信息
        option_info = OptionParser.parse(position.symbol)
        if not option_info:
            logger.warning(f"Failed to parse option symbol: {position.symbol}")
            return self.calculate_overall_score(session, position)

        # 获取标的股票的市场数据
        underlying = option_info.get('underlying')
        entry_md = self._get_market_data(session, underlying, position.open_time)
        exit_md = self._get_market_data(
            session, underlying, position.close_time
        ) if position.close_time else None

        # 计算DTE
        if option_info.get('expiry') and position.open_time:
            from datetime import datetime
            expiry = option_info['expiry']
            if isinstance(expiry, str):
                expiry = datetime.strptime(expiry, '%Y-%m-%d').date()
            entry_date = position.open_time.date() if hasattr(position.open_time, 'date') else position.open_time
            option_info['dte'] = (expiry - entry_date).days

            if position.close_time:
                exit_date = position.close_time.date() if hasattr(position.close_time, 'date') else position.close_time
                option_info['exit_dte'] = (expiry - exit_date).days

        # 计算股票基础评分
        base_result = self.calculate_overall_score(session, position)

        # 计算期权专属评分
        option_entry_result = self.score_option_entry(position, entry_md, option_info)
        option_exit_result = self.score_option_exit(position, exit_md, option_info)
        option_strategy_result = self.score_option_strategy(
            position, entry_md, exit_md, option_info
        )

        # 综合评分：股票基础评分(60%) + 期权专属评分(40%)
        option_overall_score = (
            base_result['overall_score'] * 0.60 +
            option_entry_result['option_entry_score'] * 0.15 +
            option_exit_result['option_exit_score'] * 0.10 +
            option_strategy_result['option_strategy_score'] * 0.15
        )

        grade = self._assign_grade(option_overall_score)

        return {
            **base_result,
            'option_overall_score': option_overall_score,
            'option_grade': grade,
            'option_entry_score': option_entry_result['option_entry_score'],
            'option_exit_score': option_exit_result['option_exit_score'],
            'option_strategy_score': option_strategy_result['option_strategy_score'],
            **option_entry_result,
            **option_exit_result,
            **option_strategy_result,
            'option_info': option_info
        }

    # ==================== 批量处理 ====================

    def score_all_positions(
        self,
        session: Session,
        update_db: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        批量评分所有已平仓的交易

        Args:
            session: Database session
            update_db: 是否更新数据库
            limit: 限制评分数量 (用于测试)

        Returns:
            dict: 统计信息
        """
        # 查询所有已平仓的交易
        query = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.close_time.isnot(None)
        )

        if limit:
            query = query.limit(limit)

        positions = query.all()

        # 预加载所有需要的 MarketData，避免 N+1 查询
        self._preload_market_data(session, positions)

        stats = {
            'total': len(positions),
            'scored': 0,
            'failed': 0,
            'v2_mode': self.use_v2
        }

        for position in positions:
            try:
                # 计算评分
                result = self.calculate_overall_score(session, position)

                if update_db:
                    # 更新基础评分字段
                    position.entry_quality_score = result['entry_score']
                    position.exit_quality_score = result['exit_score']
                    position.trend_quality_score = result['trend_score']
                    position.risk_mgmt_score = result['risk_score']
                    position.overall_score = result['overall_score']
                    position.score_grade = result['grade']

                    # V2: 更新新增评分字段
                    if self.use_v2:
                        position.market_env_score = result.get('market_env_score')
                        position.behavior_score = result.get('behavior_score')
                        position.execution_score = result.get('execution_score')
                        position.options_greeks_score = result.get('options_greeks_score')

                        # 新闻契合度评分
                        news_score = result.get('news_alignment_score')
                        if news_score is not None:
                            position.news_alignment_score = news_score

                            # 保存 NewsContext 到数据库 (可选)
                            news_search_result = result.get('news_search_result')
                            news_alignment_result = result.get('news_alignment_result')
                            if news_search_result and news_alignment_result:
                                self._save_news_context(
                                    session, position,
                                    news_search_result, news_alignment_result
                                )

                        # 保存详情为JSON
                        if result.get('score_details'):
                            position.score_details = json.dumps(
                                result['score_details'],
                                ensure_ascii=False,
                                default=str
                            )

                        # 保存行为分析
                        if result.get('behavior_warnings'):
                            behavior_analysis = {
                                'warnings': result['behavior_warnings'],
                                'details': result.get('score_details', {}).get('behavior', {})
                            }
                            position.behavior_analysis = json.dumps(
                                behavior_analysis,
                                ensure_ascii=False,
                                default=str
                            )

                stats['scored'] += 1
                logger.info(
                    f"Scored position {position.id}: {result['overall_score']:.1f} ({result['grade']})"
                )

            except Exception as e:
                logger.error(f"Failed to score position {position.id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                stats['failed'] += 1

        if update_db:
            session.commit()
            logger.info(f"Updated {stats['scored']} positions in database")

        return stats

    def _save_news_context(
        self,
        session: Session,
        position: Position,
        news_search_result,
        news_alignment_result
    ):
        """
        保存新闻上下文到数据库

        Args:
            session: Database session
            position: Position对象
            news_search_result: NewsSearchResult
            news_alignment_result: NewsAlignmentScore
        """
        try:
            # 检查是否已存在
            existing = session.query(NewsContext).filter(
                NewsContext.position_id == position.id
            ).first()

            if existing:
                # 更新现有记录
                news_context = existing
            else:
                # 创建新记录
                news_context = NewsContext(position_id=position.id)
                session.add(news_context)

            # 填充数据
            news_context.symbol = news_search_result.symbol
            news_context.underlying_symbol = (
                position.underlying_symbol if position.is_option else None
            )
            news_context.search_date = news_search_result.search_date
            news_context.search_range_days = news_search_result.search_range_days
            news_context.search_source = news_search_result.search_source

            # 类别标记
            news_context.has_earnings = news_search_result.has_earnings
            news_context.has_product_news = news_search_result.has_product_news
            news_context.has_analyst_rating = news_search_result.has_analyst_rating
            news_context.has_sector_news = news_search_result.has_sector_news
            news_context.has_macro_news = news_search_result.has_macro_news
            news_context.has_geopolitical = news_search_result.has_geopolitical

            # 情感分析
            news_context.overall_sentiment = news_search_result.overall_sentiment
            news_context.sentiment_score = news_search_result.sentiment_score
            news_context.news_impact_level = news_search_result.news_impact_level

            # 新闻数据
            news_context.news_items = [
                {
                    'title': item.title,
                    'source': item.source,
                    'date': str(item.date) if item.date else None,
                    'url': item.url,
                    'snippet': item.snippet,
                    'category': item.category,
                    'sentiment': item.sentiment,
                    'relevance': item.relevance,
                }
                for item in news_search_result.news_items
            ]
            news_context.search_queries = news_search_result.search_queries
            news_context.news_count = news_search_result.news_count

            # 评分结果
            news_context.news_alignment_score = news_alignment_result.overall_score
            news_context.score_breakdown = news_alignment_result.breakdown
            news_context.scoring_warnings = news_alignment_result.warnings

            # Flush to get the news_context.id
            session.flush()

            # 更新 Position 的关联
            position.news_context_id = news_context.id

            logger.debug(
                f"Saved NewsContext for position {position.id}: "
                f"score={news_alignment_result.overall_score:.1f}"
            )

        except Exception as e:
            logger.warning(f"Failed to save NewsContext for position {position.id}: {e}")

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"QualityScorer("
            f"entry={self.weights['entry']:.0%}, "
            f"exit={self.weights['exit']:.0%}, "
            f"trend={self.weights['trend']:.0%}, "
            f"risk={self.weights['risk']:.0%})"
        )
