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

            logger.info(f"Calculated all indicators for {len(df)} records")

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

                    record.updated_at = datetime.now()
                    updated_count += 1

            session.commit()
            logger.info(f"Updated {updated_count} records for {symbol}")

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
