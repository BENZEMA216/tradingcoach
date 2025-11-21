"""
CacheManager - 三级缓存管理器

L1: 内存缓存 (dict)
L2: 数据库缓存 (market_data表)
L3: 磁盘缓存 (pickle文件)
"""

import pandas as pd
import pickle
import hashlib
import logging
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from src.models.market_data import MarketData

logger = logging.getLogger(__name__)


class CacheManager:
    """
    三级缓存管理器

    缓存优先级：L1 (内存) → L2 (数据库) → L3 (磁盘)
    查找时按优先级查找，命中后写入更高级缓存
    写入时同时写入所有三级缓存
    """

    def __init__(
        self,
        db_session: Session,
        cache_dir: str = 'cache/market_data',
        expiry_days: int = 1,
        l1_max_size: int = 100
    ):
        """
        初始化缓存管理器

        Args:
            db_session: 数据库会话
            cache_dir: L3磁盘缓存目录
            expiry_days: 数据过期天数（仅适用于当日数据）
            l1_max_size: L1缓存最大条目数（LRU淘汰）
        """
        self.session = db_session
        self.cache_dir = Path(cache_dir)
        self.expiry_days = expiry_days
        self.l1_max_size = l1_max_size

        # L1: 内存缓存
        self.l1_cache = {}  # {cache_key: (DataFrame, timestamp)}
        self.l1_access_order = []  # LRU队列

        # 确保L3目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"CacheManager initialized: "
            f"cache_dir={cache_dir}, expiry_days={expiry_days}, l1_max_size={l1_max_size}"
        )

    def get(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        从缓存获取数据

        按优先级查找：L1 → L2 → L3

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间粒度

        Returns:
            DataFrame if found, None if not found
        """
        cache_key = self._make_cache_key(symbol, start_date, end_date, interval)

        # L1: 内存缓存
        df = self._get_from_l1(cache_key)
        if df is not None:
            logger.debug(f"L1 cache hit: {symbol} {start_date}-{end_date}")
            return df

        # L2: 数据库缓存
        df = self._get_from_l2(symbol, start_date, end_date, interval)
        if df is not None:
            logger.debug(f"L2 cache hit: {symbol} {start_date}-{end_date}")
            # 写入L1
            self._set_to_l1(cache_key, df)
            return df

        # L3: 磁盘缓存
        df = self._get_from_l3(cache_key)
        if df is not None:
            logger.debug(f"L3 cache hit: {symbol} {start_date}-{end_date}")
            # 写入L1
            self._set_to_l1(cache_key, df)
            return df

        logger.debug(f"Cache miss: {symbol} {start_date}-{end_date}")
        return None

    def set(
        self,
        symbol: str,
        df: pd.DataFrame,
        interval: str = '1d',
        data_source: str = 'yfinance'
    ):
        """
        写入所有缓存层

        Args:
            symbol: 股票代码
            df: 数据DataFrame
            interval: 时间粒度
            data_source: 数据来源
        """
        if df is None or df.empty:
            logger.warning(f"Attempted to cache empty DataFrame for {symbol}")
            return

        start_date = df.index.min().date()
        end_date = df.index.max().date()

        cache_key = self._make_cache_key(symbol, start_date, end_date, interval)

        # L1: 内存
        self._set_to_l1(cache_key, df)

        # L2: 数据库
        self._set_to_l2(symbol, df, interval, data_source)

        # L3: 磁盘
        self._set_to_l3(cache_key, df)

        logger.info(
            f"Cached {len(df)} records for {symbol} "
            f"({start_date} to {end_date}) in all 3 levels"
        )

    def clear_all(self):
        """清空所有缓存"""
        # L1
        self.l1_cache.clear()
        self.l1_access_order.clear()

        # L3
        for cache_file in self.cache_dir.glob('*.pkl'):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to delete cache file {cache_file}: {e}")

        logger.info("All caches cleared")

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        # L1统计
        l1_size = len(self.l1_cache)

        # L2统计（数据库）
        try:
            l2_count = self.session.query(MarketData).count()
            l2_symbols = self.session.query(MarketData.symbol).distinct().count()
        except:
            l2_count = 0
            l2_symbols = 0

        # L3统计（磁盘）
        l3_files = list(self.cache_dir.glob('*.pkl'))
        l3_size = sum(f.stat().st_size for f in l3_files)

        return {
            'l1_entries': l1_size,
            'l1_max_size': self.l1_max_size,
            'l2_records': l2_count,
            'l2_symbols': l2_symbols,
            'l3_files': len(l3_files),
            'l3_size_mb': l3_size / (1024 * 1024),
        }

    # ==================== L1 缓存（内存） ====================

    def _get_from_l1(self, cache_key: str) -> Optional[pd.DataFrame]:
        """从L1内存缓存获取"""
        if cache_key in self.l1_cache:
            df, cached_time = self.l1_cache[cache_key]

            # 更新访问顺序（LRU）
            if cache_key in self.l1_access_order:
                self.l1_access_order.remove(cache_key)
            self.l1_access_order.append(cache_key)

            return df.copy()  # 返回副本，避免修改缓存

        return None

    def _set_to_l1(self, cache_key: str, df: pd.DataFrame):
        """写入L1内存缓存"""
        # LRU淘汰：如果超过最大大小，移除最久未访问的
        if len(self.l1_cache) >= self.l1_max_size and cache_key not in self.l1_cache:
            if self.l1_access_order:
                oldest_key = self.l1_access_order.pop(0)
                if oldest_key in self.l1_cache:
                    del self.l1_cache[oldest_key]
                    logger.debug(f"L1 cache evicted: {oldest_key}")

        self.l1_cache[cache_key] = (df.copy(), datetime.now())

        # 更新访问顺序
        if cache_key in self.l1_access_order:
            self.l1_access_order.remove(cache_key)
        self.l1_access_order.append(cache_key)

    # ==================== L2 缓存（数据库） ====================

    def _get_from_l2(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """从L2数据库缓存获取"""
        try:
            query = self.session.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.date >= start_date,
                MarketData.date <= end_date,
                MarketData.interval == interval
            ).order_by(MarketData.timestamp)

            records = query.all()

            if not records:
                return None

            # 检查是否覆盖完整日期范围
            db_dates = {r.date for r in records}
            expected_dates = self._get_expected_trading_days(start_date, end_date)

            # 如果缺少数据，返回None（需要重新获取完整数据）
            if len(db_dates) < len(expected_dates) * 0.9:  # 允许10%的缺失（如节假日）
                logger.debug(
                    f"L2 incomplete data: {symbol} has {len(db_dates)}/{len(expected_dates)} days"
                )
                return None

            # 转换为DataFrame
            data = []
            for r in records:
                data.append({
                    'Date': r.timestamp,
                    'Open': float(r.open) if r.open else None,
                    'High': float(r.high) if r.high else None,
                    'Low': float(r.low) if r.low else None,
                    'Close': float(r.close),
                    'Volume': r.volume if r.volume else 0
                })

            df = pd.DataFrame(data)
            df.set_index('Date', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Failed to get from L2 cache: {e}")
            return None

    def _set_to_l2(
        self,
        symbol: str,
        df: pd.DataFrame,
        interval: str,
        data_source: str
    ):
        """写入L2数据库缓存"""
        try:
            records = []

            for timestamp, row in df.iterrows():
                # 检查是否已存在
                existing = self.session.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timestamp == timestamp,
                    MarketData.interval == interval
                ).first()

                if existing:
                    # 更新现有记录
                    existing.open = row.get('Open')
                    existing.high = row.get('High')
                    existing.low = row.get('Low')
                    existing.close = row.get('Close')
                    existing.volume = row.get('Volume')
                    existing.data_source = data_source
                    existing.updated_at = datetime.now()
                else:
                    # 创建新记录
                    record = MarketData(
                        symbol=symbol,
                        timestamp=timestamp,
                        date=timestamp.date(),
                        interval=interval,
                        open=row.get('Open'),
                        high=row.get('High'),
                        low=row.get('Low'),
                        close=row.get('Close'),
                        volume=row.get('Volume'),
                        data_source=data_source
                    )
                    records.append(record)

            # 批量插入新记录
            if records:
                self.session.bulk_save_objects(records)
                self.session.commit()

                logger.debug(f"L2 cached {len(records)} new records for {symbol}")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to set L2 cache for {symbol}: {e}")

    # ==================== L3 缓存（磁盘） ====================

    def _get_from_l3(self, cache_key: str) -> Optional[pd.DataFrame]:
        """从L3磁盘缓存获取"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if not cache_file.exists():
            return None

        try:
            # 检查文件年龄
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)

            # 如果文件过旧，不使用（仅对当日数据生效）
            if file_age.days > self.expiry_days:
                logger.debug(f"L3 cache expired: {cache_key}")
                return None

            with open(cache_file, 'rb') as f:
                df = pickle.load(f)

            return df

        except Exception as e:
            logger.error(f"Failed to load from L3 cache {cache_file}: {e}")
            return None

    def _set_to_l3(self, cache_key: str, df: pd.DataFrame):
        """写入L3磁盘缓存"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f, protocol=pickle.HIGHEST_PROTOCOL)

            logger.debug(f"L3 cached: {cache_file.name}")

        except Exception as e:
            logger.error(f"Failed to write L3 cache {cache_file}: {e}")

    # ==================== 辅助方法 ====================

    def _make_cache_key(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str
    ) -> str:
        """生成缓存键"""
        key_str = f"{symbol}_{start_date}_{end_date}_{interval}"
        # 使用MD5哈希缩短键长度
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_expected_trading_days(self, start_date: date, end_date: date) -> List[date]:
        """
        估算交易日数量（简化版）

        实际交易日需要考虑节假日，这里用简化估算
        """
        days = []
        current = start_date

        while current <= end_date:
            # 排除周末
            if current.weekday() < 5:  # 0-4 是周一到周五
                days.append(current)
            current += timedelta(days=1)

        return days

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return (
            f"CacheManager(L1={stats['l1_entries']}/{stats['l1_max_size']}, "
            f"L2={stats['l2_records']} records, "
            f"L3={stats['l3_files']} files)"
        )
