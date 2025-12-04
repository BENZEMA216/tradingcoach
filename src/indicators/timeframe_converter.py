"""
Timeframe Converter - 多周期数据转换器

支持日线到周线、月线的数据聚合，以及周线技术指标计算
"""

import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TimeframeConverter:
    """
    多周期数据转换器

    支持将日线数据聚合为周线或月线，并计算对应周期的技术指标
    """

    @staticmethod
    def daily_to_weekly(df: pd.DataFrame, week_end: str = 'FRI') -> pd.DataFrame:
        """
        将日线数据聚合为周线数据

        Args:
            df: 日线数据DataFrame，必须包含 date/timestamp, open, high, low, close, volume 列
            week_end: 周结束日，默认周五 ('FRI')

        Returns:
            周线聚合后的DataFrame
        """
        if df is None or df.empty:
            return df

        df_copy = df.copy()

        # 处理日期索引
        if 'date' in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['date'])
            df_copy.set_index('date', inplace=True)
        elif 'timestamp' in df_copy.columns:
            df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
            df_copy.set_index('timestamp', inplace=True)

        # 确保数据按时间排序
        df_copy = df_copy.sort_index()

        # 周线聚合规则
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }

        # 对于其他数值列，使用最后一个值
        for col in df_copy.columns:
            if col not in agg_dict and df_copy[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                agg_dict[col] = 'last'

        # 执行周线聚合
        weekly_df = df_copy.resample(f'W-{week_end}').agg(agg_dict)

        # 去除无效行
        weekly_df = weekly_df.dropna(subset=['close'])

        # 重置索引
        weekly_df = weekly_df.reset_index()
        weekly_df.rename(columns={'index': 'date'}, inplace=True)

        logger.info(f"Converted {len(df_copy)} daily records to {len(weekly_df)} weekly records")

        return weekly_df

    @staticmethod
    def daily_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
        """
        将日线数据聚合为月线数据

        Args:
            df: 日线数据DataFrame

        Returns:
            月线聚合后的DataFrame
        """
        if df is None or df.empty:
            return df

        df_copy = df.copy()

        # 处理日期索引
        if 'date' in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['date'])
            df_copy.set_index('date', inplace=True)
        elif 'timestamp' in df_copy.columns:
            df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
            df_copy.set_index('timestamp', inplace=True)

        # 确保数据按时间排序
        df_copy = df_copy.sort_index()

        # 月线聚合规则
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }

        # 对于其他数值列，使用最后一个值
        for col in df_copy.columns:
            if col not in agg_dict and df_copy[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                agg_dict[col] = 'last'

        # 执行月线聚合（月末）
        monthly_df = df_copy.resample('ME').agg(agg_dict)

        # 去除无效行
        monthly_df = monthly_df.dropna(subset=['close'])

        # 重置索引
        monthly_df = monthly_df.reset_index()
        monthly_df.rename(columns={'index': 'date'}, inplace=True)

        logger.info(f"Converted {len(df_copy)} daily records to {len(monthly_df)} monthly records")

        return monthly_df

    @staticmethod
    def calculate_weekly_indicators(weekly_df: pd.DataFrame) -> pd.DataFrame:
        """
        为周线数据计算技术指标

        Args:
            weekly_df: 周线数据DataFrame

        Returns:
            添加了技术指标的DataFrame
        """
        from src.indicators.calculator import IndicatorCalculator

        calculator = IndicatorCalculator()
        return calculator.calculate_all_indicators(weekly_df)

    @staticmethod
    def get_multi_timeframe_data(daily_df: pd.DataFrame) -> dict:
        """
        获取多周期数据（日线+周线+月线）

        Args:
            daily_df: 日线数据DataFrame

        Returns:
            dict: {'daily': df, 'weekly': df, 'monthly': df}
        """
        converter = TimeframeConverter()

        weekly_df = converter.daily_to_weekly(daily_df)
        monthly_df = converter.daily_to_monthly(daily_df)

        return {
            'daily': daily_df,
            'weekly': weekly_df,
            'monthly': monthly_df
        }

    @staticmethod
    def align_multi_timeframe(daily_df: pd.DataFrame, weekly_df: pd.DataFrame) -> pd.DataFrame:
        """
        将周线数据对齐到日线时间轴

        用于在日线图上显示周线指标

        Args:
            daily_df: 日线数据
            weekly_df: 周线数据

        Returns:
            添加了周线指标的日线DataFrame
        """
        if daily_df is None or daily_df.empty or weekly_df is None or weekly_df.empty:
            return daily_df

        daily_copy = daily_df.copy()

        # 确保有日期列
        if 'date' not in daily_copy.columns and daily_copy.index.name == 'date':
            daily_copy = daily_copy.reset_index()

        if 'date' not in weekly_df.columns and weekly_df.index.name == 'date':
            weekly_df = weekly_df.reset_index()

        # 将日期转为datetime
        daily_copy['date'] = pd.to_datetime(daily_copy['date'])
        weekly_df['date'] = pd.to_datetime(weekly_df['date'])

        # 为每个日线找到对应的周线数据
        weekly_cols = ['rsi', 'macd', 'macd_signal', 'adx', 'ma_20', 'ma_50']

        for col in weekly_cols:
            if col in weekly_df.columns:
                # 创建周线到日线的映射
                weekly_data = weekly_df[['date', col]].dropna()
                if not weekly_data.empty:
                    # 使用merge_asof进行时间对齐（向后查找最近的周线数据）
                    daily_copy = pd.merge_asof(
                        daily_copy.sort_values('date'),
                        weekly_data.sort_values('date'),
                        on='date',
                        direction='backward',
                        suffixes=('', '_weekly')
                    )

        return daily_copy


def resample_ohlcv(df: pd.DataFrame, target_timeframe: str = 'W') -> pd.DataFrame:
    """
    将OHLCV数据重采样到目标时间周期

    Args:
        df: 原始数据DataFrame
        target_timeframe: 目标周期 ('W' for weekly, 'M' for monthly, 'Q' for quarterly)

    Returns:
        重采样后的DataFrame
    """
    converter = TimeframeConverter()

    if target_timeframe == 'W':
        return converter.daily_to_weekly(df)
    elif target_timeframe in ['M', 'ME']:
        return converter.daily_to_monthly(df)
    else:
        raise ValueError(f"Unsupported timeframe: {target_timeframe}")


# 便捷函数
def to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """将日线转换为周线的快捷函数"""
    return TimeframeConverter.daily_to_weekly(df)


def to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """将日线转换为月线的快捷函数"""
    return TimeframeConverter.daily_to_monthly(df)
