"""
AKShareClient - A股数据源客户端

input: A股股票代码（如 000001, 600000, 300750）
output: OHLCV 数据、股票信息
pos: 为 A 股提供免费数据源，与 yfinance 并行使用

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import time
import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import deque
import pandas as pd

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    ak = None

from .base_client import (
    BaseDataClient,
    DataSourceError,
    RateLimitError,
    DataNotFoundError,
    InvalidSymbolError
)

logger = logging.getLogger(__name__)


class AKShareClient(BaseDataClient):
    """
    AKShare 数据客户端

    专门用于获取中国 A 股数据，免费无需 API Key

    支持的代码格式:
    - 纯数字: 000001, 600000, 300750
    - 带后缀: 000001.SZ, 600000.SH
    """

    # A股市场前缀规则
    SH_PREFIXES = ('600', '601', '603', '605', '688', '689', '900')  # 上海
    SZ_PREFIXES = ('000', '001', '002', '003', '300', '301', '200')  # 深圳
    BJ_PREFIXES = ('8', '4')  # 北交所

    # 速率限制配置
    RATE_LIMIT_REQUESTS = 30   # 每分钟最大请求数
    RATE_LIMIT_WINDOW = 60     # 时间窗口（秒）

    def __init__(self, rate_limit: bool = True):
        """
        初始化 AKShare 客户端

        Args:
            rate_limit: 是否启用速率限制
        """
        self._rate_limit_enabled = rate_limit
        self._request_times: deque = deque(maxlen=self.RATE_LIMIT_REQUESTS)

        if not AKSHARE_AVAILABLE:
            logger.warning("akshare 未安装，请运行: pip install akshare")

    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化 A 股代码为纯6位数字格式

        Args:
            symbol: 输入代码 (000001, 000001.SZ, SZ000001)

        Returns:
            str: 6位数字代码 (000001)
        """
        if not symbol:
            raise InvalidSymbolError("股票代码不能为空")

        symbol = symbol.strip().upper()

        # 移除常见后缀
        for suffix in ['.SZ', '.SH', '.BJ', '.SS']:
            if symbol.endswith(suffix):
                symbol = symbol[:-len(suffix)]
                break

        # 移除常见前缀
        for prefix in ['SZ', 'SH', 'BJ', 'SS']:
            if symbol.startswith(prefix) and len(symbol) > 2:
                symbol = symbol[len(prefix):]
                break

        # 验证是否为纯数字
        if not symbol.isdigit():
            raise InvalidSymbolError(f"无效的A股代码格式: {symbol}")

        # 补齐到6位
        if len(symbol) < 6:
            symbol = symbol.zfill(6)

        return symbol

    def _get_market_suffix(self, symbol: str) -> str:
        """
        根据代码获取市场后缀

        Args:
            symbol: 6位数字代码

        Returns:
            str: 市场后缀 (SH/SZ/BJ)
        """
        if symbol.startswith(self.SH_PREFIXES):
            return 'SH'
        elif symbol.startswith(self.SZ_PREFIXES):
            return 'SZ'
        elif symbol.startswith(self.BJ_PREFIXES):
            return 'BJ'
        else:
            # 默认深圳
            return 'SZ'

    def _wait_for_rate_limit(self) -> None:
        """等待直到可以发送请求（速率限制）"""
        if not self._rate_limit_enabled:
            return

        now = time.time()

        # 清理过期的请求记录
        while self._request_times and self._request_times[0] < now - self.RATE_LIMIT_WINDOW:
            self._request_times.popleft()

        # 如果达到限制，等待
        if len(self._request_times) >= self.RATE_LIMIT_REQUESTS:
            wait_time = self._request_times[0] + self.RATE_LIMIT_WINDOW - now + 0.1
            if wait_time > 0:
                logger.debug(f"速率限制：等待 {wait_time:.1f} 秒")
                time.sleep(wait_time)

        # 记录这次请求
        self._request_times.append(time.time())

    def is_a_stock(self, symbol: str) -> bool:
        """
        判断是否为 A 股代码

        Args:
            symbol: 股票代码

        Returns:
            bool: True 表示是 A 股
        """
        try:
            normalized = self._normalize_symbol(symbol)
            # A股代码是6位数字
            if not normalized.isdigit() or len(normalized) != 6:
                return False

            # 检查前缀是否属于已知A股
            return (normalized.startswith(self.SH_PREFIXES) or
                    normalized.startswith(self.SZ_PREFIXES) or
                    normalized.startswith(self.BJ_PREFIXES))
        except (InvalidSymbolError, ValueError):
            return False

    def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        获取 A 股 OHLCV 数据

        Args:
            symbol: 股票代码（如 000001, 600000）
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间粒度（仅支持 '1d'）

        Returns:
            DataFrame with columns: ['Open', 'High', 'Low', 'Close', 'Volume']
        """
        if not AKSHARE_AVAILABLE:
            raise DataSourceError("akshare 未安装")

        # 标准化代码
        normalized_symbol = self._normalize_symbol(symbol)

        # 目前只支持日线
        if interval != '1d':
            logger.warning(f"AKShare 目前仅支持日线数据，忽略 interval={interval}")

        # 格式化日期
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')

        # 速率限制
        self._wait_for_rate_limit()

        try:
            logger.debug(f"从 AKShare 获取 {normalized_symbol} 数据: {start_str} - {end_str}")

            # 使用东方财富数据源
            df = ak.stock_zh_a_hist(
                symbol=normalized_symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq"  # 前复权
            )

            if df is None or df.empty:
                raise DataNotFoundError(f"未找到 {symbol} 的数据")

            # 重命名列
            column_mapping = {
                '日期': 'Date',
                '开盘': 'Open',
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume',
                '成交额': 'Amount',
                '振幅': 'Amplitude',
                '涨跌幅': 'Change_Pct',
                '涨跌额': 'Change',
                '换手率': 'Turnover'
            }

            df = df.rename(columns=column_mapping)

            # 设置日期索引
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')

            # 使用基类方法标准化
            df = self.standardize_dataframe(df)

            logger.info(f"成功获取 {symbol} 的 {len(df)} 条数据")
            return df

        except Exception as e:
            if "频繁" in str(e) or "limit" in str(e).lower():
                raise RateLimitError(f"AKShare 请求过于频繁: {e}")
            elif "不存在" in str(e) or "not found" in str(e).lower():
                raise DataNotFoundError(f"未找到 {symbol} 的数据: {e}")
            else:
                raise DataSourceError(f"AKShare 获取数据失败: {e}")

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取 A 股基本信息

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票基本信息
        """
        if not AKSHARE_AVAILABLE:
            raise DataSourceError("akshare 未安装")

        normalized_symbol = self._normalize_symbol(symbol)
        market = self._get_market_suffix(normalized_symbol)

        self._wait_for_rate_limit()

        try:
            # 获取个股信息
            df = ak.stock_individual_info_em(symbol=normalized_symbol)

            if df is None or df.empty:
                raise DataNotFoundError(f"未找到 {symbol} 的信息")

            # 转换为字典
            info = {}
            for _, row in df.iterrows():
                item = row.get('item', row.get(0, ''))
                value = row.get('value', row.get(1, ''))
                info[item] = value

            # 标准化返回格式
            result = {
                'symbol': f"{normalized_symbol}.{market}",
                'name': info.get('股票简称', info.get('名称', '')),
                'market': market,
                'industry': info.get('行业', ''),
                'sector': info.get('板块', ''),
                'market_cap': self._parse_market_cap(info.get('总市值', '')),
                'currency': 'CNY',
                'exchange': '上海证券交易所' if market == 'SH' else '深圳证券交易所',
                'raw': info
            }

            return result

        except Exception as e:
            if "不存在" in str(e) or "not found" in str(e).lower():
                raise DataNotFoundError(f"未找到 {symbol} 的信息: {e}")
            else:
                raise DataSourceError(f"获取股票信息失败: {e}")

    def _parse_market_cap(self, value: str) -> Optional[float]:
        """解析市值字符串为数值"""
        if not value:
            return None
        try:
            # 移除非数字字符，转换单位
            value = str(value).strip()
            multiplier = 1
            if '亿' in value:
                multiplier = 1e8
                value = value.replace('亿', '')
            elif '万' in value:
                multiplier = 1e4
                value = value.replace('万', '')

            return float(value) * multiplier
        except (ValueError, TypeError):
            return None

    def is_available(self) -> bool:
        """
        检查 AKShare 是否可用

        Returns:
            bool: True 表示可用
        """
        if not AKSHARE_AVAILABLE:
            return False

        try:
            # 简单测试：获取一个知名股票的最近一天数据
            end_date = date.today()
            start_date = end_date - timedelta(days=7)

            df = ak.stock_zh_a_hist(
                symbol="000001",  # 平安银行
                period="daily",
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="qfq"
            )
            return df is not None and not df.empty
        except Exception as e:
            logger.warning(f"AKShare 可用性检查失败: {e}")
            return False

    def get_source_name(self) -> str:
        """获取数据源名称"""
        return 'akshare'

    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情（额外功能）

        Args:
            symbol: 股票代码

        Returns:
            dict: 实时行情数据
        """
        if not AKSHARE_AVAILABLE:
            raise DataSourceError("akshare 未安装")

        normalized_symbol = self._normalize_symbol(symbol)

        self._wait_for_rate_limit()

        try:
            # 获取全市场实时行情
            df = ak.stock_zh_a_spot_em()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取实时行情")

            # 筛选目标股票
            row = df[df['代码'] == normalized_symbol]

            if row.empty:
                raise DataNotFoundError(f"未找到 {symbol} 的实时行情")

            row = row.iloc[0]

            return {
                'symbol': normalized_symbol,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0)),
                'change': float(row.get('涨跌额', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'volume': int(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'open': float(row.get('今开', 0)),
                'pre_close': float(row.get('昨收', 0)),
            }

        except Exception as e:
            raise DataSourceError(f"获取实时行情失败: {e}")

    def get_multiple_ohlcv(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的 OHLCV 数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间粒度

        Returns:
            dict: {symbol: DataFrame}
        """
        results = {}
        errors = {}

        for symbol in symbols:
            try:
                df = self.get_ohlcv(symbol, start_date, end_date, interval)
                results[symbol] = df
            except Exception as e:
                logger.warning(f"获取 {symbol} 数据失败: {e}")
                errors[symbol] = str(e)

        if errors:
            logger.warning(f"部分股票获取失败: {errors}")

        return results
