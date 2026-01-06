"""
BatchFetcher - 批量数据获取器

分析数据库中的交易记录，批量获取所需的市场数据
"""

import time
import logging
import re
from datetime import date, datetime, timedelta
from typing import List, Dict, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from tqdm import tqdm

from src.models.trade import Trade
from src.data_sources.base_client import BaseDataClient, DataNotFoundError, InvalidSymbolError
from src.data_sources.cache_manager import CacheManager
from typing import Optional, Union

logger = logging.getLogger(__name__)

# 延迟导入避免循环依赖
def _get_data_router():
    from src.data_sources.data_router import DataRouter, get_data_router
    return get_data_router()


class BatchFetcher:
    """
    批量数据获取器

    功能：
    1. 分析数据库中的交易记录，确定需要获取的 symbols 和日期范围
    2. 检查缓存，过滤已有数据
    3. 批量获取缺失数据
    4. 支持进度显示
    5. 处理期权 symbol，同时获取标的股票数据
    """

    def __init__(
        self,
        client: Optional[BaseDataClient] = None,
        cache_manager: Optional[CacheManager] = None,
        batch_size: int = 50,
        request_delay: float = 0.2,
        extra_days: int = 200,  # 为技术指标计算额外获取的天数
        use_router: bool = True  # 使用智能路由器（自动选择 AKShare/YFinance）
    ):
        """
        初始化批量获取器

        Args:
            client: 数据源客户端（如果 use_router=True 则忽略）
            cache_manager: 缓存管理器
            batch_size: 批次大小
            request_delay: 请求间隔（秒）
            extra_days: 额外获取天数（用于技术指标计算）
            use_router: 是否使用智能路由器（自动为A股使用AKShare）
        """
        self.use_router = use_router
        self._router = None

        if use_router:
            self._router = _get_data_router()
            self.client = None
            source_name = "DataRouter (AKShare + YFinance)"
        else:
            self.client = client
            source_name = client.get_source_name() if client else "None"

        self.cache = cache_manager
        self.batch_size = batch_size
        self.request_delay = request_delay
        self.extra_days = extra_days

        logger.info(
            f"BatchFetcher initialized: "
            f"source={source_name}, batch_size={batch_size}, use_router={use_router}"
        )

    def fetch_required_data(self, session: Session) -> Dict[str, any]:
        """
        分析数据库并批量获取所需数据

        Args:
            session: 数据库会话

        Returns:
            dict with statistics:
                - symbols_analyzed: 分析的标的数
                - symbols_fetched: 获取的标的数
                - records_fetched: 获取的记录数
                - cached_symbols: 已缓存的标的数
                - failed_symbols: 失败的标的
        """
        logger.info("=" * 60)
        logger.info("Starting batch data fetch")
        logger.info("=" * 60)

        # Step 1: 分析需求
        logger.info("Step 1: Analyzing database requirements...")
        requirements = self._analyze_requirements(session)

        logger.info(f"Found {len(requirements)} symbols to process")

        # Step 2: 过滤已缓存
        logger.info("Step 2: Checking cache...")
        missing = self._filter_missing(requirements)

        logger.info(f"Need to fetch {len(missing)} symbols (cache hit: {len(requirements) - len(missing)})")

        # Step 3: 批量获取
        logger.info("Step 3: Batch fetching data...")
        result = self._batch_fetch(missing)

        # Step 4: 统计
        stats = {
            'symbols_analyzed': len(requirements),
            'symbols_fetched': result['success_count'],
            'records_fetched': result['total_records'],
            'cached_symbols': len(requirements) - len(missing),
            'failed_symbols': result['failed'],
            'duration_seconds': result['duration']
        }

        logger.info("=" * 60)
        logger.info("Batch fetch completed")
        logger.info(f"Success: {stats['symbols_fetched']}/{stats['symbols_analyzed']}")
        logger.info(f"Records: {stats['records_fetched']}")
        logger.info(f"Duration: {stats['duration_seconds']:.1f}s")
        logger.info("=" * 60)

        return stats

    def _analyze_requirements(self, session: Session) -> List[Dict]:
        """
        分析数据库，确定需要获取的数据

        Returns:
            List of dicts with:
                - symbol: 股票代码
                - start_date: 开始日期（包含extra_days）
                - end_date: 结束日期（今天）
                - trade_count: 交易次数（用于排序优先级）
        """
        # 查询所有交易标的及其日期范围
        query = session.query(
            Trade.symbol,
            func.min(Trade.trade_date).label('min_date'),
            func.max(Trade.trade_date).label('max_date'),
            func.count().label('trade_count')
        ).group_by(Trade.symbol).order_by(func.count().desc())

        requirements = []

        for row in query:
            symbol = row.symbol

            # 解析期权 symbol
            option_info = self._parse_option_symbol(symbol)

            if option_info:
                # 期权：同时获取标的股票数据
                underlying = option_info['underlying']

                # 标的股票
                requirements.append({
                    'symbol': underlying,
                    'original_symbol': symbol,  # 记录原始期权代码
                    'start_date': row.min_date - timedelta(days=self.extra_days),
                    'end_date': date.today(),
                    'trade_count': row.trade_count,
                    'is_underlying': True
                })

                # 期权本身（可能无数据）
                requirements.append({
                    'symbol': symbol,
                    'original_symbol': symbol,
                    'start_date': row.min_date - timedelta(days=self.extra_days),
                    'end_date': date.today(),
                    'trade_count': row.trade_count,
                    'is_underlying': False
                })
            else:
                # 普通股票
                requirements.append({
                    'symbol': symbol,
                    'original_symbol': symbol,
                    'start_date': row.min_date - timedelta(days=self.extra_days),
                    'end_date': date.today(),
                    'trade_count': row.trade_count,
                    'is_underlying': False
                })

        # 去重（同一个标的可能被多次添加）
        seen = set()
        unique_reqs = []

        for req in requirements:
            key = (req['symbol'], req['start_date'], req['end_date'])
            if key not in seen:
                seen.add(key)
                unique_reqs.append(req)

        return unique_reqs

    def _filter_missing(self, requirements: List[Dict]) -> List[Dict]:
        """
        过滤已缓存的数据

        Args:
            requirements: 需求列表

        Returns:
            缺失的需求列表
        """
        missing = []

        for req in requirements:
            # 检查缓存
            cached = self.cache.get(
                req['symbol'],
                req['start_date'],
                req['end_date']
            )

            if cached is None or cached.empty:
                missing.append(req)

        return missing

    def _batch_fetch(self, requirements: List[Dict]) -> Dict:
        """
        批量获取数据

        Args:
            requirements: 需求列表

        Returns:
            dict with statistics
        """
        start_time = time.time()

        success_count = 0
        failed = []
        total_records = 0

        # 使用 tqdm 显示进度
        pbar = tqdm(requirements, desc="Fetching market data", unit="symbol")

        for req in pbar:
            symbol = req['symbol']
            start_date = req['start_date']
            end_date = req['end_date']

            try:
                # 使用路由器或单个客户端
                if self.use_router and self._router:
                    # 使用智能路由器（自动选择 AKShare 或 YFinance）
                    df = self._router.get_ohlcv(symbol, start_date, end_date)
                    source_name = self._router.detect_market(symbol)
                else:
                    # 使用传统单客户端
                    # 转换为 yfinance 格式（如需要）
                    if hasattr(self.client, 'convert_symbol_for_yfinance'):
                        symbol_converted = self.client.convert_symbol_for_yfinance(symbol)
                    else:
                        symbol_converted = symbol

                    df = self.client.get_ohlcv(symbol_converted, start_date, end_date)
                    source_name = self.client.get_source_name()

                if df is not None and not df.empty:
                    # 缓存数据
                    if self.cache:
                        self.cache.set(
                            symbol,  # 使用原始 symbol 缓存
                            df,
                            data_source=source_name
                        )

                    success_count += 1
                    total_records += len(df)

                    pbar.set_postfix({
                        'success': success_count,
                        'records': total_records
                    })

                # 限流：等待
                time.sleep(self.request_delay)

            except (DataNotFoundError, InvalidSymbolError) as e:
                logger.warning(f"Skipped {symbol}: {e}")
                failed.append({
                    'symbol': symbol,
                    'reason': str(e)
                })

            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                failed.append({
                    'symbol': symbol,
                    'reason': str(e)
                })

        pbar.close()

        duration = time.time() - start_time

        return {
            'success_count': success_count,
            'failed': failed,
            'total_records': total_records,
            'duration': duration
        }

    def _parse_option_symbol(self, symbol: str) -> Dict:
        """
        解析期权代码

        格式: {UNDERLYING}{YYMMDD}[CP]{STRIKE}
        示例: AAPL250117C150000 → AAPL call, exp 2025-01-17, strike 150.0

        Args:
            symbol: 期权代码

        Returns:
            dict or None if not an option
        """
        # 期权正则模式
        pattern = r'^([A-Z]+)(\d{6})([CP])(\d{8})$'
        match = re.match(pattern, symbol)

        if not match:
            return None

        underlying, date_str, opt_type, strike_str = match.groups()

        # 解析日期
        year = 2000 + int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])

        # 解析行权价
        strike = int(strike_str) / 1000.0

        return {
            'underlying': underlying,
            'expiry': date(year, month, day),
            'option_type': 'call' if opt_type == 'C' else 'put',
            'strike': strike
        }

    def warmup_cache(self, session: Session, top_n: int = 20):
        """
        缓存预热：预加载最常交易的标的

        Args:
            session: 数据库会话
            top_n: 预加载的标的数量
        """
        logger.info(f"Cache warmup: preloading top {top_n} symbols...")

        # 获取Top N交易标的
        top_symbols = session.query(
            Trade.symbol,
            func.count().label('count')
        ).group_by(Trade.symbol)\
         .order_by(func.count().desc())\
         .limit(top_n)

        symbols_to_warmup = [row.symbol for row in top_symbols]

        logger.info(f"Warmup symbols: {', '.join(symbols_to_warmup[:10])}...")

        # 分析这些标的的需求
        all_reqs = self._analyze_requirements(session)
        warmup_reqs = [r for r in all_reqs if r['symbol'] in symbols_to_warmup]

        # 批量获取
        result = self._batch_fetch(warmup_reqs)

        logger.info(
            f"Warmup completed: {result['success_count']}/{len(warmup_reqs)} symbols, "
            f"{result['total_records']} records"
        )

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"BatchFetcher(client={self.client.get_source_name()}, "
            f"batch_size={self.batch_size}, "
            f"delay={self.request_delay}s)"
        )
