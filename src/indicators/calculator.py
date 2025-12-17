"""
IndicatorCalculator - 技术指标计算器

使用纯 pandas 实现常用技术指标计算
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.market_data import MarketData

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    技术指标计算器

    功能：
    1. 计算常用技术指标（RSI, MACD, Bollinger Bands, ATR, MA）
    2. 批量计算多个symbol的指标
    3. 更新market_data表的指标字段
    4. 支持增量计算
    """

    def __init__(self):
        """初始化计算器"""
        logger.info("IndicatorCalculator initialized")

    # ==================== RSI (Relative Strength Index) ====================

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14, column: str = 'Close') -> pd.Series:
        """
        计算RSI指标

        Args:
            df: DataFrame with OHLCV data
            period: RSI周期（默认14）
            column: 用于计算的列名（默认Close）

        Returns:
            pd.Series: RSI values (0-100)

        Formula:
            RSI = 100 - (100 / (1 + RS))
            RS = 平均涨幅 / 平均跌幅
        """
        if df.empty or column not in df.columns:
            return pd.Series(dtype=float)

        # 计算价格变化
        delta = df[column].diff()

        # 分离涨跌
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # 计算平均涨跌幅（使用 EMA）
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    # ==================== MACD (Moving Average Convergence Divergence) ====================

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        column: str = 'Close'
    ) -> Dict[str, pd.Series]:
        """
        计算MACD指标

        Args:
            df: DataFrame with OHLCV data
            fast: 快线周期（默认12）
            slow: 慢线周期（默认26）
            signal: 信号线周期（默认9）
            column: 用于计算的列名（默认Close）

        Returns:
            dict: {'macd': DIF线, 'signal': DEA信号线, 'histogram': MACD柱}

        Formula:
            DIF = EMA(12) - EMA(26)
            DEA = EMA(DIF, 9)
            MACD柱 = (DIF - DEA) × 2
        """
        if df.empty or column not in df.columns:
            return {
                'macd': pd.Series(dtype=float),
                'signal': pd.Series(dtype=float),
                'histogram': pd.Series(dtype=float)
            }

        # 计算快慢EMA
        ema_fast = df[column].ewm(span=fast, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow, adjust=False).mean()

        # 计算DIF（MACD线）
        macd_line = ema_fast - ema_slow

        # 计算DEA（信号线）
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()

        # 计算MACD柱
        histogram = (macd_line - signal_line) * 2

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    # ==================== Bollinger Bands ====================

    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = 'Close'
    ) -> Dict[str, pd.Series]:
        """
        计算布林带

        Args:
            df: DataFrame with OHLCV data
            period: 周期（默认20）
            std_dev: 标准差倍数（默认2.0）
            column: 用于计算的列名（默认Close）

        Returns:
            dict: {'upper': 上轨, 'middle': 中轨, 'lower': 下轨}

        Formula:
            中轨 = MA(20)
            上轨 = 中轨 + 2 × STD(20)
            下轨 = 中轨 - 2 × STD(20)
        """
        if df.empty or column not in df.columns:
            return {
                'upper': pd.Series(dtype=float),
                'middle': pd.Series(dtype=float),
                'lower': pd.Series(dtype=float)
            }

        # 计算中轨（简单移动平均）
        middle = df[column].rolling(window=period).mean()

        # 计算标准差
        std = df[column].rolling(window=period).std()

        # 计算上下轨
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }

    # ==================== ATR (Average True Range) ====================

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算ATR指标

        Args:
            df: DataFrame with OHLC data
            period: ATR周期（默认14）

        Returns:
            pd.Series: ATR values

        Formula:
            TR = max(高-低, |高-昨收|, |低-昨收|)
            ATR = EMA(TR, period)
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return pd.Series(dtype=float)

        # 计算真实波幅（True Range）
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # 计算ATR（使用EMA）
        atr = tr.ewm(span=period, adjust=False).mean()

        return atr

    # ==================== EMA (Exponential Moving Average) ====================

    def calculate_ema(
        self,
        df: pd.DataFrame,
        periods: List[int] = [12, 26],
        column: str = 'Close'
    ) -> Dict[str, pd.Series]:
        """
        计算多个周期的指数移动平均线

        Args:
            df: DataFrame with OHLCV data
            periods: EMA周期列表（默认[12, 26]）
            column: 用于计算的列名（默认Close）

        Returns:
            dict: {f'ema_{period}': EMA值}

        Formula:
            EMA = Close × k + EMA(前一天) × (1 - k)
            k = 2 / (period + 1)
        """
        if df.empty or column not in df.columns:
            return {f'ema_{p}': pd.Series(dtype=float) for p in periods}

        result = {}
        for period in periods:
            result[f'ema_{period}'] = df[column].ewm(span=period, adjust=False).mean()

        return result

    # ==================== ADX (Average Directional Index) ====================

    def calculate_adx(
        self,
        df: pd.DataFrame,
        period: int = 14
    ) -> Dict[str, pd.Series]:
        """
        计算ADX趋势强度指标和方向性指标

        Args:
            df: DataFrame with OHLC data
            period: ADX周期（默认14）

        Returns:
            dict: {
                'adx': ADX趋势强度 (0-100),
                'plus_di': +DI方向指标 (0-100),
                'minus_di': -DI方向指标 (0-100)
            }

        Formula:
            +DM = High - PrevHigh (if positive and > |Low - PrevLow|, else 0)
            -DM = PrevLow - Low (if positive and > High - PrevHigh, else 0)
            TR = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
            +DI = 100 × EMA(+DM) / EMA(TR)
            -DI = 100 × EMA(-DM) / EMA(TR)
            DX = 100 × |+DI - -DI| / (+DI + -DI)
            ADX = EMA(DX, period)

        Note:
            ADX > 25: 强趋势
            ADX < 20: 弱趋势或震荡
            +DI > -DI: 上升趋势
            -DI > +DI: 下降趋势
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return {
                'adx': pd.Series(dtype=float),
                'plus_di': pd.Series(dtype=float),
                'minus_di': pd.Series(dtype=float)
            }

        high = df['High']
        low = df['Low']
        close = df['Close']

        # 计算+DM和-DM
        up_move = high.diff()
        down_move = low.shift(1) - low

        # +DM: 当日高点上移幅度大于低点下移幅度时取值
        plus_dm = pd.Series(0.0, index=df.index)
        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move

        # -DM: 当日低点下移幅度大于高点上移幅度时取值
        minus_dm = pd.Series(0.0, index=df.index)
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

        # 计算True Range
        high_low = high - low
        high_close = (high - close.shift()).abs()
        low_close = (low - close.shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # 使用EMA平滑
        atr = tr.ewm(span=period, adjust=False).mean()
        plus_dm_smooth = plus_dm.ewm(span=period, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(span=period, adjust=False).mean()

        # 计算+DI和-DI
        plus_di = 100 * plus_dm_smooth / atr
        minus_di = 100 * minus_dm_smooth / atr

        # 处理除零情况
        plus_di = plus_di.replace([np.inf, -np.inf], 0).fillna(0)
        minus_di = minus_di.replace([np.inf, -np.inf], 0).fillna(0)

        # 计算DX
        di_sum = plus_di + minus_di
        di_diff = (plus_di - minus_di).abs()
        dx = 100 * di_diff / di_sum
        dx = dx.replace([np.inf, -np.inf], 0).fillna(0)

        # 计算ADX (DX的EMA)
        adx = dx.ewm(span=period, adjust=False).mean()

        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }

    # ==================== Stochastic Oscillator ====================

    def calculate_stochastic(
        self,
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3
    ) -> Dict[str, pd.Series]:
        """
        计算Stochastic随机指标

        Args:
            df: DataFrame with OHLC data
            k_period: %K周期（默认14）
            d_period: %D周期（默认3）
            smooth_k: %K平滑周期（默认3）

        Returns:
            dict: {
                'stoch_k': %K值 (0-100),
                'stoch_d': %D值 (0-100)
            }

        Formula:
            %K = 100 × (Close - LowestLow) / (HighestHigh - LowestLow)
            Slow %K = SMA(%K, smooth_k)
            %D = SMA(Slow %K, d_period)

        Note:
            %K < 20: 超卖
            %K > 80: 超买
            %K上穿%D: 金叉，看涨信号
            %K下穿%D: 死叉，看跌信号
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return {
                'stoch_k': pd.Series(dtype=float),
                'stoch_d': pd.Series(dtype=float)
            }

        high = df['High']
        low = df['Low']
        close = df['Close']

        # 计算周期内最高价和最低价
        highest_high = high.rolling(window=k_period).max()
        lowest_low = low.rolling(window=k_period).min()

        # 计算Fast %K
        fast_k = 100 * (close - lowest_low) / (highest_high - lowest_low)

        # 处理除零情况
        fast_k = fast_k.replace([np.inf, -np.inf], 50).fillna(50)

        # 计算Slow %K (平滑后的%K)
        stoch_k = fast_k.rolling(window=smooth_k).mean()

        # 计算%D (Slow %K的移动平均)
        stoch_d = stoch_k.rolling(window=d_period).mean()

        return {
            'stoch_k': stoch_k,
            'stoch_d': stoch_d
        }

    # ==================== MA (Moving Average) ====================

    def calculate_ma(
        self,
        df: pd.DataFrame,
        periods: List[int] = [5, 10, 20, 50, 200],
        column: str = 'Close'
    ) -> Dict[str, pd.Series]:
        """
        计算多个周期的移动平均线

        Args:
            df: DataFrame with OHLCV data
            periods: MA周期列表（默认[5, 10, 20, 50, 200]）
            column: 用于计算的列名（默认Close）

        Returns:
            dict: {f'ma_{period}': MA值}
        """
        if df.empty or column not in df.columns:
            return {f'ma_{p}': pd.Series(dtype=float) for p in periods}

        result = {}
        for period in periods:
            result[f'ma_{period}'] = df[column].rolling(window=period).mean()

        return result

    # ==================== 成交量指标 ====================

    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """
        计算OBV能量潮指标

        Formula:
            如果今日收盘价 > 昨日收盘价: OBV = 昨日OBV + 今日成交量
            如果今日收盘价 < 昨日收盘价: OBV = 昨日OBV - 今日成交量
            如果今日收盘价 = 昨日收盘价: OBV = 昨日OBV
        """
        if df.empty or 'Close' not in df.columns or 'Volume' not in df.columns:
            return pd.Series(dtype=float)

        close = df['Close']
        volume = df['Volume']

        # 计算价格变化方向
        direction = np.sign(close.diff())
        direction.iloc[0] = 0

        # OBV = 累积(方向 × 成交量)
        obv = (direction * volume).cumsum()

        return obv

    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """
        计算VWAP成交量加权平均价

        Formula:
            VWAP = Σ(典型价格 × 成交量) / Σ(成交量)
            典型价格 = (High + Low + Close) / 3
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close', 'Volume']):
            return pd.Series(dtype=float)

        # 典型价格
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3

        # 累积成交量加权价格
        cum_tp_vol = (typical_price * df['Volume']).cumsum()
        cum_vol = df['Volume'].cumsum()

        # VWAP
        vwap = cum_tp_vol / cum_vol
        vwap = vwap.replace([np.inf, -np.inf], np.nan)

        return vwap

    def calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算MFI资金流量指标 (成交量加权RSI)

        Formula:
            典型价格 = (High + Low + Close) / 3
            资金流量 = 典型价格 × 成交量
            正向资金流 = 典型价格上涨时的资金流量
            负向资金流 = 典型价格下跌时的资金流量
            资金流比率 = 正向资金流(N日) / 负向资金流(N日)
            MFI = 100 - (100 / (1 + 资金流比率))
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close', 'Volume']):
            return pd.Series(dtype=float)

        # 典型价格
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3

        # 资金流量
        money_flow = typical_price * df['Volume']

        # 价格变化方向
        tp_diff = typical_price.diff()

        # 正向和负向资金流
        positive_flow = money_flow.where(tp_diff > 0, 0)
        negative_flow = money_flow.where(tp_diff < 0, 0)

        # N日累积
        positive_sum = positive_flow.rolling(window=period).sum()
        negative_sum = negative_flow.rolling(window=period).sum()

        # 资金流比率
        mf_ratio = positive_sum / negative_sum
        mf_ratio = mf_ratio.replace([np.inf, -np.inf], 0)

        # MFI
        mfi = 100 - (100 / (1 + mf_ratio))

        return mfi

    def calculate_ad_line(self, df: pd.DataFrame) -> pd.Series:
        """
        计算A/D累积分布线

        Formula:
            CLV = ((Close - Low) - (High - Close)) / (High - Low)
            A/D = 累积(CLV × Volume)
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close', 'Volume']):
            return pd.Series(dtype=float)

        high = df['High']
        low = df['Low']
        close = df['Close']
        volume = df['Volume']

        # Close Location Value
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.replace([np.inf, -np.inf], 0).fillna(0)

        # A/D Line
        ad = (clv * volume).cumsum()

        return ad

    def calculate_cmf(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算CMF蔡金资金流

        Formula:
            CLV = ((Close - Low) - (High - Close)) / (High - Low)
            CMF = Σ(CLV × Volume, N日) / Σ(Volume, N日)
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close', 'Volume']):
            return pd.Series(dtype=float)

        high = df['High']
        low = df['Low']
        close = df['Close']
        volume = df['Volume']

        # Close Location Value
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.replace([np.inf, -np.inf], 0).fillna(0)

        # CMF
        cmf = (clv * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
        cmf = cmf.replace([np.inf, -np.inf], np.nan)

        return cmf

    def calculate_volume_ratio(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算成交量比率

        Formula:
            成交量比率 = 当日成交量 / N日平均成交量
        """
        if df.empty or 'Volume' not in df.columns:
            return pd.Series(dtype=float)

        vol_sma = df['Volume'].rolling(window=period).mean()
        vol_ratio = df['Volume'] / vol_sma
        vol_ratio = vol_ratio.replace([np.inf, -np.inf], np.nan)

        return vol_ratio

    # ==================== 动量指标补充 ====================

    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算CCI商品通道指数

        Formula:
            TP = (High + Low + Close) / 3
            CCI = (TP - MA(TP)) / (0.015 × MAD(TP))
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return pd.Series(dtype=float)

        # 典型价格
        tp = (df['High'] + df['Low'] + df['Close']) / 3

        # TP的移动平均
        tp_ma = tp.rolling(window=period).mean()

        # 平均绝对偏差
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)

        # CCI
        cci = (tp - tp_ma) / (0.015 * mad)
        cci = cci.replace([np.inf, -np.inf], np.nan)

        return cci

    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算威廉指标 Williams %R

        Formula:
            %R = (最高价N日 - 收盘价) / (最高价N日 - 最低价N日) × -100
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return pd.Series(dtype=float)

        highest_high = df['High'].rolling(window=period).max()
        lowest_low = df['Low'].rolling(window=period).min()

        willr = ((highest_high - df['Close']) / (highest_high - lowest_low)) * -100
        willr = willr.replace([np.inf, -np.inf], np.nan)

        return willr

    def calculate_roc(self, df: pd.DataFrame, period: int = 12) -> pd.Series:
        """
        计算ROC变动率

        Formula:
            ROC = (今日收盘价 - N日前收盘价) / N日前收盘价 × 100
        """
        if df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=float)

        roc = ((df['Close'] - df['Close'].shift(period)) / df['Close'].shift(period)) * 100
        roc = roc.replace([np.inf, -np.inf], np.nan)

        return roc

    def calculate_momentum(self, df: pd.DataFrame, period: int = 10) -> pd.Series:
        """
        计算动量指标

        Formula:
            Momentum = 今日收盘价 - N日前收盘价
        """
        if df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=float)

        return df['Close'] - df['Close'].shift(period)

    def calculate_ultimate_oscillator(
        self,
        df: pd.DataFrame,
        period1: int = 7,
        period2: int = 14,
        period3: int = 28
    ) -> pd.Series:
        """
        计算终极震荡指标 Ultimate Oscillator

        Formula:
            BP = Close - min(Low, PrevClose)
            TR = max(High, PrevClose) - min(Low, PrevClose)
            Avg(BP/TR, N)
            UO = 100 × (4×Avg7 + 2×Avg14 + Avg28) / 7
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return pd.Series(dtype=float)

        prev_close = df['Close'].shift(1)

        # Buying Pressure
        bp = df['Close'] - pd.concat([df['Low'], prev_close], axis=1).min(axis=1)

        # True Range
        tr = pd.concat([df['High'], prev_close], axis=1).max(axis=1) - \
             pd.concat([df['Low'], prev_close], axis=1).min(axis=1)

        # 三个周期的平均
        avg1 = bp.rolling(window=period1).sum() / tr.rolling(window=period1).sum()
        avg2 = bp.rolling(window=period2).sum() / tr.rolling(window=period2).sum()
        avg3 = bp.rolling(window=period3).sum() / tr.rolling(window=period3).sum()

        # Ultimate Oscillator
        uo = 100 * (4 * avg1 + 2 * avg2 + avg3) / 7
        uo = uo.replace([np.inf, -np.inf], np.nan)

        return uo

    # ==================== 波动率指标补充 ====================

    def calculate_keltner_channel(
        self,
        df: pd.DataFrame,
        ema_period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        计算肯特纳通道

        Formula:
            中轨 = EMA(Close, N)
            上轨 = 中轨 + multiplier × ATR
            下轨 = 中轨 - multiplier × ATR
        """
        if df.empty or 'Close' not in df.columns:
            return {
                'kc_upper': pd.Series(dtype=float),
                'kc_middle': pd.Series(dtype=float),
                'kc_lower': pd.Series(dtype=float)
            }

        # 中轨 (EMA)
        middle = df['Close'].ewm(span=ema_period, adjust=False).mean()

        # ATR
        atr = self.calculate_atr(df, period=atr_period)

        # 上下轨
        upper = middle + (multiplier * atr)
        lower = middle - (multiplier * atr)

        return {
            'kc_upper': upper,
            'kc_middle': middle,
            'kc_lower': lower
        }

    def calculate_donchian_channel(self, df: pd.DataFrame, period: int = 20) -> Dict[str, pd.Series]:
        """
        计算唐奇安通道

        Formula:
            上轨 = N日最高价
            下轨 = N日最低价
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low']):
            return {
                'dc_upper': pd.Series(dtype=float),
                'dc_lower': pd.Series(dtype=float)
            }

        upper = df['High'].rolling(window=period).max()
        lower = df['Low'].rolling(window=period).min()

        return {
            'dc_upper': upper,
            'dc_lower': lower
        }

    def calculate_historical_volatility(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算历史波动率 (年化)

        Formula:
            日收益率 = ln(今日收盘 / 昨日收盘)
            历史波动率 = std(日收益率, N) × sqrt(252) × 100
        """
        if df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=float)

        # 对数收益率
        log_returns = np.log(df['Close'] / df['Close'].shift(1))

        # 年化波动率
        hvol = log_returns.rolling(window=period).std() * np.sqrt(252) * 100

        return hvol

    def calculate_bb_squeeze(self, df: pd.DataFrame) -> pd.Series:
        """
        计算布林带挤压信号

        当布林带在肯特纳通道内时，表示波动率收窄（挤压状态）

        Returns:
            1 = 挤压中（低波动率）
            0 = 释放（正常或高波动率）
        """
        if df.empty:
            return pd.Series(dtype=int)

        # 布林带
        bb = self.calculate_bollinger_bands(df)

        # 肯特纳通道
        kc = self.calculate_keltner_channel(df)

        # 挤压：BB上轨 < KC上轨 且 BB下轨 > KC下轨
        squeeze = ((bb['upper'] < kc['kc_upper']) & (bb['lower'] > kc['kc_lower'])).astype(int)

        return squeeze

    # ==================== 趋势指标补充 ====================

    def calculate_ichimoku(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算一目均衡图 (Ichimoku Cloud)

        Formula:
            转换线(Tenkan-sen) = (9日最高 + 9日最低) / 2
            基准线(Kijun-sen) = (26日最高 + 26日最低) / 2
            先行带A(Senkou Span A) = (转换线 + 基准线) / 2，向前位移26日
            先行带B(Senkou Span B) = (52日最高 + 52日最低) / 2，向前位移26日
            迟行线(Chikou Span) = 收盘价向后位移26日
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return {
                'ichi_tenkan': pd.Series(dtype=float),
                'ichi_kijun': pd.Series(dtype=float),
                'ichi_senkou_a': pd.Series(dtype=float),
                'ichi_senkou_b': pd.Series(dtype=float),
                'ichi_chikou': pd.Series(dtype=float)
            }

        high = df['High']
        low = df['Low']
        close = df['Close']

        # 转换线 (9日)
        tenkan = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2

        # 基准线 (26日)
        kijun = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2

        # 先行带A (转换线+基准线)/2
        senkou_a = (tenkan + kijun) / 2

        # 先行带B (52日)
        senkou_b = (high.rolling(window=52).max() + low.rolling(window=52).min()) / 2

        # 迟行线 (收盘价)
        chikou = close

        return {
            'ichi_tenkan': tenkan,
            'ichi_kijun': kijun,
            'ichi_senkou_a': senkou_a,
            'ichi_senkou_b': senkou_b,
            'ichi_chikou': chikou
        }

    def calculate_parabolic_sar(
        self,
        df: pd.DataFrame,
        af_start: float = 0.02,
        af_step: float = 0.02,
        af_max: float = 0.2
    ) -> Dict[str, pd.Series]:
        """
        计算抛物线SAR

        Args:
            af_start: 加速因子初始值
            af_step: 加速因子步进
            af_max: 加速因子最大值
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return {
                'psar': pd.Series(dtype=float),
                'psar_dir': pd.Series(dtype=int)
            }

        high = df['High'].values
        low = df['Low'].values
        close = df['Close'].values
        n = len(df)

        psar = np.zeros(n)
        psar_dir = np.zeros(n)  # 1 = 多头, -1 = 空头
        af = af_start
        ep = 0  # Extreme Point

        # 初始化
        psar[0] = close[0]
        psar_dir[0] = 1 if close[0] > close[0] else -1
        ep = high[0] if psar_dir[0] == 1 else low[0]

        for i in range(1, n):
            if psar_dir[i-1] == 1:  # 多头趋势
                psar[i] = psar[i-1] + af * (ep - psar[i-1])
                psar[i] = min(psar[i], low[i-1], low[i-2] if i > 1 else low[i-1])

                if low[i] < psar[i]:  # 反转为空头
                    psar_dir[i] = -1
                    psar[i] = ep
                    ep = low[i]
                    af = af_start
                else:
                    psar_dir[i] = 1
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + af_step, af_max)
            else:  # 空头趋势
                psar[i] = psar[i-1] + af * (ep - psar[i-1])
                psar[i] = max(psar[i], high[i-1], high[i-2] if i > 1 else high[i-1])

                if high[i] > psar[i]:  # 反转为多头
                    psar_dir[i] = 1
                    psar[i] = ep
                    ep = high[i]
                    af = af_start
                else:
                    psar_dir[i] = -1
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + af_step, af_max)

        return {
            'psar': pd.Series(psar, index=df.index),
            'psar_dir': pd.Series(psar_dir.astype(int), index=df.index)
        }

    def calculate_supertrend(
        self,
        df: pd.DataFrame,
        period: int = 10,
        multiplier: float = 3.0
    ) -> Dict[str, pd.Series]:
        """
        计算SuperTrend指标

        Formula:
            基础上轨 = (High + Low) / 2 + multiplier × ATR
            基础下轨 = (High + Low) / 2 - multiplier × ATR
            SuperTrend根据趋势方向选择上轨或下轨
        """
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return {
                'supertrend': pd.Series(dtype=float),
                'supertrend_dir': pd.Series(dtype=int)
            }

        high = df['High']
        low = df['Low']
        close = df['Close']

        # ATR
        atr = self.calculate_atr(df, period=period)

        # 基础轨道
        hl2 = (high + low) / 2
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)

        n = len(df)
        supertrend = np.zeros(n)
        direction = np.zeros(n)

        # 初始化
        supertrend[0] = basic_upper.iloc[0]
        direction[0] = -1

        for i in range(1, n):
            # 更新上轨
            if basic_upper.iloc[i] < supertrend[i-1] or close.iloc[i-1] > supertrend[i-1]:
                upper = basic_upper.iloc[i]
            else:
                upper = supertrend[i-1] if direction[i-1] == -1 else basic_upper.iloc[i]

            # 更新下轨
            if basic_lower.iloc[i] > supertrend[i-1] or close.iloc[i-1] < supertrend[i-1]:
                lower = basic_lower.iloc[i]
            else:
                lower = supertrend[i-1] if direction[i-1] == 1 else basic_lower.iloc[i]

            # 确定趋势方向
            if direction[i-1] == -1:  # 之前是下跌趋势
                if close.iloc[i] > supertrend[i-1]:
                    direction[i] = 1  # 转为上涨
                    supertrend[i] = lower
                else:
                    direction[i] = -1
                    supertrend[i] = upper
            else:  # 之前是上涨趋势
                if close.iloc[i] < supertrend[i-1]:
                    direction[i] = -1  # 转为下跌
                    supertrend[i] = upper
                else:
                    direction[i] = 1
                    supertrend[i] = lower

        return {
            'supertrend': pd.Series(supertrend, index=df.index),
            'supertrend_dir': pd.Series(direction.astype(int), index=df.index)
        }

    def calculate_trix(self, df: pd.DataFrame, period: int = 15) -> pd.Series:
        """
        计算TRIX三重指数平滑指标

        Formula:
            EMA1 = EMA(Close, N)
            EMA2 = EMA(EMA1, N)
            EMA3 = EMA(EMA2, N)
            TRIX = (EMA3 - EMA3[1]) / EMA3[1] × 100
        """
        if df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=float)

        ema1 = df['Close'].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()

        trix = ((ema3 - ema3.shift(1)) / ema3.shift(1)) * 100
        trix = trix.replace([np.inf, -np.inf], np.nan)

        return trix

    def calculate_dpo(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算DPO去趋势价格振荡器

        Formula:
            DPO = Close - MA(Close, N)向前位移(N/2 + 1)日
        """
        if df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=float)

        shift = period // 2 + 1
        ma = df['Close'].rolling(window=period).mean()
        dpo = df['Close'] - ma.shift(shift)

        return dpo

    # ==================== 综合计算 ====================

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标并添加到DataFrame

        Args:
            df: DataFrame with OHLCV data, index must be DatetimeIndex

        Returns:
            DataFrame with all indicator columns added
        """
        if df.empty:
            logger.warning("Empty DataFrame provided, skipping indicator calculation")
            return df

        # 创建副本避免修改原始数据
        df_result = df.copy()

        try:
            # RSI
            df_result['rsi_14'] = self.calculate_rsi(df, period=14)

            # MACD
            macd_result = self.calculate_macd(df)
            df_result['macd'] = macd_result['macd']
            df_result['macd_signal'] = macd_result['signal']
            df_result['macd_histogram'] = macd_result['histogram']

            # Bollinger Bands
            bb_result = self.calculate_bollinger_bands(df)
            df_result['bb_upper'] = bb_result['upper']
            df_result['bb_middle'] = bb_result['middle']
            df_result['bb_lower'] = bb_result['lower']

            # BB Width (波动率压缩/扩张指标)
            # BB Width = (上轨 - 下轨) / 中轨 × 100
            bb_width = (bb_result['upper'] - bb_result['lower']) / bb_result['middle'] * 100
            df_result['bb_width'] = bb_width.replace([np.inf, -np.inf], np.nan)

            # BB %B (价格在布林带中的相对位置)
            # %B = (Close - 下轨) / (上轨 - 下轨)
            # %B > 1: 价格在上轨之上; %B < 0: 价格在下轨之下; %B = 0.5: 价格在中轨
            if 'Close' in df.columns:
                bb_percent_b = (df['Close'] - bb_result['lower']) / (bb_result['upper'] - bb_result['lower'])
                df_result['bb_percent_b'] = bb_percent_b.replace([np.inf, -np.inf], np.nan)

            # ATR
            df_result['atr_14'] = self.calculate_atr(df, period=14)

            # EMA系列
            ema_result = self.calculate_ema(df, periods=[12, 26])
            df_result['ema_12'] = ema_result['ema_12']
            df_result['ema_26'] = ema_result['ema_26']

            # ADX和方向性指标
            adx_result = self.calculate_adx(df, period=14)
            df_result['adx'] = adx_result['adx']
            df_result['plus_di'] = adx_result['plus_di']
            df_result['minus_di'] = adx_result['minus_di']

            # Stochastic随机指标
            stoch_result = self.calculate_stochastic(df, k_period=14, d_period=3, smooth_k=3)
            df_result['stoch_k'] = stoch_result['stoch_k']
            df_result['stoch_d'] = stoch_result['stoch_d']

            # MA系列
            ma_result = self.calculate_ma(df, periods=[5, 10, 20, 50, 200])
            for key, value in ma_result.items():
                df_result[key] = value

            # Volume SMA (成交量20日均线)
            if 'Volume' in df.columns:
                df_result['volume_sma_20'] = df['Volume'].rolling(window=20).mean()

            # ==================== 新增成交量指标 ====================
            # OBV
            df_result['obv'] = self.calculate_obv(df)

            # VWAP
            df_result['vwap'] = self.calculate_vwap(df)

            # MFI
            df_result['mfi_14'] = self.calculate_mfi(df, period=14)

            # A/D Line
            df_result['ad_line'] = self.calculate_ad_line(df)

            # CMF
            df_result['cmf_20'] = self.calculate_cmf(df, period=20)

            # Volume Ratio
            df_result['volume_ratio'] = self.calculate_volume_ratio(df, period=20)

            # ==================== 新增动量指标 ====================
            # CCI
            df_result['cci_20'] = self.calculate_cci(df, period=20)

            # Williams %R
            df_result['willr_14'] = self.calculate_williams_r(df, period=14)

            # ROC
            df_result['roc_12'] = self.calculate_roc(df, period=12)

            # Momentum
            df_result['mom_10'] = self.calculate_momentum(df, period=10)

            # Ultimate Oscillator
            df_result['uo'] = self.calculate_ultimate_oscillator(df)

            # ==================== 新增波动率指标 ====================
            # Keltner Channel
            kc_result = self.calculate_keltner_channel(df)
            df_result['kc_upper'] = kc_result['kc_upper']
            df_result['kc_middle'] = kc_result['kc_middle']
            df_result['kc_lower'] = kc_result['kc_lower']

            # Donchian Channel
            dc_result = self.calculate_donchian_channel(df, period=20)
            df_result['dc_upper'] = dc_result['dc_upper']
            df_result['dc_lower'] = dc_result['dc_lower']

            # Historical Volatility
            df_result['hvol_20'] = self.calculate_historical_volatility(df, period=20)

            # ATR Percentage
            if 'Close' in df.columns:
                atr_pct = (df_result['atr_14'] / df['Close']) * 100
                df_result['atr_pct'] = atr_pct.replace([np.inf, -np.inf], np.nan)

            # BB Squeeze
            df_result['bb_squeeze'] = self.calculate_bb_squeeze(df)

            # Volatility Rank (基于20日历史波动率的百分位排名)
            if 'hvol_20' in df_result.columns:
                df_result['vol_rank'] = df_result['hvol_20'].rolling(window=252).apply(
                    lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100 if len(x) > 0 else np.nan,
                    raw=False
                )

            # ==================== 新增趋势指标 ====================
            # Ichimoku Cloud
            ichi_result = self.calculate_ichimoku(df)
            df_result['ichi_tenkan'] = ichi_result['ichi_tenkan']
            df_result['ichi_kijun'] = ichi_result['ichi_kijun']
            df_result['ichi_senkou_a'] = ichi_result['ichi_senkou_a']
            df_result['ichi_senkou_b'] = ichi_result['ichi_senkou_b']
            df_result['ichi_chikou'] = ichi_result['ichi_chikou']

            # Parabolic SAR
            psar_result = self.calculate_parabolic_sar(df)
            df_result['psar'] = psar_result['psar']
            df_result['psar_dir'] = psar_result['psar_dir']

            # SuperTrend
            st_result = self.calculate_supertrend(df)
            df_result['supertrend'] = st_result['supertrend']
            df_result['supertrend_dir'] = st_result['supertrend_dir']

            # TRIX
            df_result['trix'] = self.calculate_trix(df, period=15)

            # DPO
            df_result['dpo'] = self.calculate_dpo(df, period=20)

            logger.info(f"Calculated all indicators (including new ones) for {len(df)} records")

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            raise

        return df_result

    # ==================== 数据库更新 ====================

    def update_market_data_indicators(
        self,
        session: Session,
        symbol: str,
        df_with_indicators: pd.DataFrame
    ) -> int:
        """
        更新market_data表的指标字段

        Args:
            session: Database session
            symbol: Stock symbol
            df_with_indicators: DataFrame with calculated indicators

        Returns:
            int: Number of records updated
        """
        if df_with_indicators.empty:
            logger.warning(f"No data to update for {symbol}")
            return 0

        updated_count = 0

        try:
            for timestamp, row in df_with_indicators.iterrows():
                # 查找对应的market_data记录
                record = session.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timestamp == timestamp
                ).first()

                if record:
                    # 更新指标字段
                    record.rsi_14 = float(row['rsi_14']) if pd.notna(row['rsi_14']) else None
                    record.macd = float(row['macd']) if pd.notna(row['macd']) else None
                    record.macd_signal = float(row['macd_signal']) if pd.notna(row['macd_signal']) else None
                    record.macd_hist = float(row['macd_histogram']) if pd.notna(row['macd_histogram']) else None
                    record.bb_upper = float(row['bb_upper']) if pd.notna(row['bb_upper']) else None
                    record.bb_middle = float(row['bb_middle']) if pd.notna(row['bb_middle']) else None
                    record.bb_lower = float(row['bb_lower']) if pd.notna(row['bb_lower']) else None

                    # BB Width 和 BB %B
                    if 'bb_width' in row and pd.notna(row['bb_width']):
                        record.bb_width = float(row['bb_width'])

                    record.atr_14 = float(row['atr_14']) if pd.notna(row['atr_14']) else None

                    # EMA
                    if 'ema_12' in row and pd.notna(row['ema_12']):
                        record.ema_12 = float(row['ema_12'])
                    if 'ema_26' in row and pd.notna(row['ema_26']):
                        record.ema_26 = float(row['ema_26'])

                    # ADX和方向性指标
                    if 'adx' in row and pd.notna(row['adx']):
                        record.adx = float(row['adx'])
                    if 'plus_di' in row and pd.notna(row['plus_di']):
                        record.plus_di = float(row['plus_di'])
                    if 'minus_di' in row and pd.notna(row['minus_di']):
                        record.minus_di = float(row['minus_di'])

                    # Stochastic
                    if 'stoch_k' in row and pd.notna(row['stoch_k']):
                        record.stoch_k = float(row['stoch_k'])
                    if 'stoch_d' in row and pd.notna(row['stoch_d']):
                        record.stoch_d = float(row['stoch_d'])

                    record.ma_5 = float(row['ma_5']) if pd.notna(row['ma_5']) else None
                    record.ma_10 = float(row['ma_10']) if pd.notna(row['ma_10']) else None
                    record.ma_20 = float(row['ma_20']) if pd.notna(row['ma_20']) else None
                    record.ma_50 = float(row['ma_50']) if pd.notna(row['ma_50']) else None
                    record.ma_200 = float(row['ma_200']) if pd.notna(row['ma_200']) else None

                    # Volume SMA
                    if 'volume_sma_20' in row and pd.notna(row['volume_sma_20']):
                        record.volume_sma_20 = float(row['volume_sma_20'])

                    # ==================== 新增成交量指标 ====================
                    if 'obv' in row and pd.notna(row['obv']):
                        record.obv = float(row['obv'])
                    if 'vwap' in row and pd.notna(row['vwap']):
                        record.vwap = float(row['vwap'])
                    if 'mfi_14' in row and pd.notna(row['mfi_14']):
                        record.mfi_14 = float(row['mfi_14'])
                    if 'ad_line' in row and pd.notna(row['ad_line']):
                        record.ad_line = float(row['ad_line'])
                    if 'cmf_20' in row and pd.notna(row['cmf_20']):
                        record.cmf_20 = float(row['cmf_20'])
                    if 'volume_ratio' in row and pd.notna(row['volume_ratio']):
                        record.volume_ratio = float(row['volume_ratio'])

                    # ==================== 新增动量指标 ====================
                    if 'cci_20' in row and pd.notna(row['cci_20']):
                        record.cci_20 = float(row['cci_20'])
                    if 'willr_14' in row and pd.notna(row['willr_14']):
                        record.willr_14 = float(row['willr_14'])
                    if 'roc_12' in row and pd.notna(row['roc_12']):
                        record.roc_12 = float(row['roc_12'])
                    if 'mom_10' in row and pd.notna(row['mom_10']):
                        record.mom_10 = float(row['mom_10'])
                    if 'uo' in row and pd.notna(row['uo']):
                        record.uo = float(row['uo'])

                    # ==================== 新增波动率指标 ====================
                    if 'kc_upper' in row and pd.notna(row['kc_upper']):
                        record.kc_upper = float(row['kc_upper'])
                    if 'kc_middle' in row and pd.notna(row['kc_middle']):
                        record.kc_middle = float(row['kc_middle'])
                    if 'kc_lower' in row and pd.notna(row['kc_lower']):
                        record.kc_lower = float(row['kc_lower'])
                    if 'dc_upper' in row and pd.notna(row['dc_upper']):
                        record.dc_upper = float(row['dc_upper'])
                    if 'dc_lower' in row and pd.notna(row['dc_lower']):
                        record.dc_lower = float(row['dc_lower'])
                    if 'hvol_20' in row and pd.notna(row['hvol_20']):
                        record.hvol_20 = float(row['hvol_20'])
                    if 'atr_pct' in row and pd.notna(row['atr_pct']):
                        record.atr_pct = float(row['atr_pct'])
                    if 'bb_squeeze' in row and pd.notna(row['bb_squeeze']):
                        record.bb_squeeze = int(row['bb_squeeze'])
                    if 'vol_rank' in row and pd.notna(row['vol_rank']):
                        record.vol_rank = float(row['vol_rank'])

                    # ==================== 新增趋势指标 ====================
                    if 'ichi_tenkan' in row and pd.notna(row['ichi_tenkan']):
                        record.ichi_tenkan = float(row['ichi_tenkan'])
                    if 'ichi_kijun' in row and pd.notna(row['ichi_kijun']):
                        record.ichi_kijun = float(row['ichi_kijun'])
                    if 'ichi_senkou_a' in row and pd.notna(row['ichi_senkou_a']):
                        record.ichi_senkou_a = float(row['ichi_senkou_a'])
                    if 'ichi_senkou_b' in row and pd.notna(row['ichi_senkou_b']):
                        record.ichi_senkou_b = float(row['ichi_senkou_b'])
                    if 'ichi_chikou' in row and pd.notna(row['ichi_chikou']):
                        record.ichi_chikou = float(row['ichi_chikou'])
                    if 'psar' in row and pd.notna(row['psar']):
                        record.psar = float(row['psar'])
                    if 'psar_dir' in row and pd.notna(row['psar_dir']):
                        record.psar_dir = int(row['psar_dir'])
                    if 'supertrend' in row and pd.notna(row['supertrend']):
                        record.supertrend = float(row['supertrend'])
                    if 'supertrend_dir' in row and pd.notna(row['supertrend_dir']):
                        record.supertrend_dir = int(row['supertrend_dir'])
                    if 'trix' in row and pd.notna(row['trix']):
                        record.trix = float(row['trix'])
                    if 'dpo' in row and pd.notna(row['dpo']):
                        record.dpo = float(row['dpo'])

                    record.updated_at = datetime.now()
                    updated_count += 1

            session.commit()
            logger.info(f"Updated {updated_count} records (with new indicators) for {symbol}")

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update indicators for {symbol}: {e}")
            raise

        return updated_count

    # ==================== 批量处理 ====================

    def batch_calculate_and_update(
        self,
        session: Session,
        symbols: List[str],
        from_cache_func: callable
    ) -> Dict[str, int]:
        """
        批量计算并更新多个symbol的技术指标

        Args:
            session: Database session
            symbols: List of stock symbols
            from_cache_func: Function to get OHLCV data from cache
                           Signature: func(symbol) -> pd.DataFrame

        Returns:
            dict: {symbol: updated_count}
        """
        results = {}

        for symbol in symbols:
            try:
                # 从缓存获取OHLCV数据
                df = from_cache_func(symbol)

                if df is None or df.empty:
                    logger.warning(f"No data found for {symbol}, skipping")
                    results[symbol] = 0
                    continue

                # 计算指标
                df_with_indicators = self.calculate_all_indicators(df)

                # 更新数据库
                updated_count = self.update_market_data_indicators(
                    session, symbol, df_with_indicators
                )

                results[symbol] = updated_count

            except Exception as e:
                logger.error(f"Failed to process {symbol}: {e}")
                results[symbol] = 0

        total_updated = sum(results.values())
        logger.info(
            f"Batch calculation completed: "
            f"{len([v for v in results.values() if v > 0])}/{len(symbols)} symbols, "
            f"{total_updated} total records updated"
        )

        return results

    def __repr__(self) -> str:
        """字符串表示"""
        return "IndicatorCalculator(RSI, MACD, BB, ATR, MA)"
