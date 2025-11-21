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

            # ATR
            df_result['atr_14'] = self.calculate_atr(df, period=14)

            # MA系列
            ma_result = self.calculate_ma(df, periods=[5, 10, 20, 50, 200])
            for key, value in ma_result.items():
                df_result[key] = value

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
                    record.macd_histogram = float(row['macd_histogram']) if pd.notna(row['macd_histogram']) else None
                    record.bb_upper = float(row['bb_upper']) if pd.notna(row['bb_upper']) else None
                    record.bb_middle = float(row['bb_middle']) if pd.notna(row['bb_middle']) else None
                    record.bb_lower = float(row['bb_lower']) if pd.notna(row['bb_lower']) else None
                    record.atr_14 = float(row['atr_14']) if pd.notna(row['atr_14']) else None
                    record.ma_5 = float(row['ma_5']) if pd.notna(row['ma_5']) else None
                    record.ma_10 = float(row['ma_10']) if pd.notna(row['ma_10']) else None
                    record.ma_20 = float(row['ma_20']) if pd.notna(row['ma_20']) else None
                    record.ma_50 = float(row['ma_50']) if pd.notna(row['ma_50']) else None
                    record.ma_200 = float(row['ma_200']) if pd.notna(row['ma_200']) else None

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
