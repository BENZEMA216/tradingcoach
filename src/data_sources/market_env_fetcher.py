"""
MarketEnvironmentFetcher - 市场环境数据获取服务

获取并填充 MarketEnvironment 表的数据，包括：
- 大盘指数（SPY, QQQ, DIA, VIX）
- 行业 ETF 表现
- 市场趋势判断
"""

import logging
from datetime import date, timedelta
from typing import Optional, List, Dict, Set
from decimal import Decimal

from sqlalchemy.orm import Session

from src.data_sources.yfinance_client import YFinanceClient
from src.models.market_environment import MarketEnvironment

logger = logging.getLogger(__name__)


# 行业 ETF 列表（SPDR Sector ETFs）
SECTOR_ETFS = {
    'XLK': 'Technology',
    'XLF': 'Financials',
    'XLE': 'Energy',
    'XLV': 'Healthcare',
    'XLY': 'Consumer Discretionary',
    'XLP': 'Consumer Staples',
    'XLI': 'Industrials',
    'XLB': 'Materials',
    'XLU': 'Utilities',
    'XLRE': 'Real Estate',
    'XLC': 'Communication Services',
}


class MarketEnvironmentFetcher:
    """
    市场环境数据获取器

    使用 YFinanceClient 获取市场数据并填充到 MarketEnvironment 表
    """

    def __init__(self, db: Session):
        """
        初始化

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.client = YFinanceClient()

    def fetch_daily_environment(self, target_date: date) -> Optional[MarketEnvironment]:
        """
        获取单日市场环境数据

        Args:
            target_date: 目标日期

        Returns:
            MarketEnvironment 对象，如果获取失败返回 None
        """
        logger.info(f"Fetching market environment for {target_date}")

        # 检查是否已存在
        existing = self.db.query(MarketEnvironment).filter(
            MarketEnvironment.date == target_date
        ).first()

        if existing:
            logger.info(f"Market environment for {target_date} already exists, updating...")
            env = existing
        else:
            env = MarketEnvironment(date=target_date)

        # 获取数据的日期范围（需要前一天数据来计算涨跌幅）
        start_date = target_date - timedelta(days=5)  # 多取几天以防节假日
        end_date = target_date

        try:
            # 1. 获取主要指数 ETF 数据
            self._fetch_index_data(env, start_date, end_date, target_date)

            # 2. 获取 VIX 数据
            self._fetch_vix_data(env, start_date, end_date, target_date)

            # 3. 获取行业 ETF 数据
            self._fetch_sector_data(env, start_date, end_date, target_date)

            # 4. 计算趋势和 VIX 水平
            env.determine_vix_level()
            env.determine_market_trend()

            # 5. 计算数据完整度
            env.data_completeness = self._calculate_completeness(env)
            env.data_source = 'yfinance'

            # 保存
            if not existing:
                self.db.add(env)
            self.db.commit()

            logger.info(f"Successfully fetched market environment for {target_date}, completeness: {env.data_completeness}%")
            return env

        except Exception as e:
            logger.error(f"Failed to fetch market environment for {target_date}: {e}")
            self.db.rollback()
            return None

    def _fetch_index_data(
        self,
        env: MarketEnvironment,
        start_date: date,
        end_date: date,
        target_date: date
    ):
        """获取主要指数 ETF 数据"""
        indices = {
            'SPY': ('spy_close', 'spy_change_pct'),
            'QQQ': ('qqq_close', 'qqq_change_pct'),
            'DIA': ('dia_close', 'dia_change_pct'),
        }

        for symbol, (close_field, change_field) in indices.items():
            try:
                df = self.client.get_ohlcv(symbol, start_date, end_date)

                if df is not None and not df.empty:
                    # 找到目标日期或之前最近的交易日
                    df.index = df.index.date if hasattr(df.index, 'date') else df.index

                    if target_date in df.index:
                        row = df.loc[target_date]
                        close_price = float(row['close'])
                        setattr(env, close_field, Decimal(str(round(close_price, 2))))

                        # 计算涨跌幅
                        if len(df) >= 2:
                            prev_close = df['close'].iloc[-2] if target_date == df.index[-1] else None
                            if prev_close:
                                change_pct = (close_price - prev_close) / prev_close * 100
                                setattr(env, change_field, Decimal(str(round(change_pct, 2))))

                        logger.debug(f"Fetched {symbol}: close={close_price}")
                    else:
                        # 使用最近的交易日数据
                        available_dates = [d for d in df.index if d <= target_date]
                        if available_dates:
                            latest_date = max(available_dates)
                            row = df.loc[latest_date]
                            close_price = float(row['close'])
                            setattr(env, close_field, Decimal(str(round(close_price, 2))))
                            logger.debug(f"Used {symbol} data from {latest_date} for {target_date}")

            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")

    def _fetch_vix_data(
        self,
        env: MarketEnvironment,
        start_date: date,
        end_date: date,
        target_date: date
    ):
        """获取 VIX 数据"""
        try:
            # VIX 使用特殊代码
            vix_symbol = self.client.convert_symbol_for_yfinance('VIX')
            df = self.client.get_ohlcv(vix_symbol, start_date, end_date)

            if df is not None and not df.empty:
                df.index = df.index.date if hasattr(df.index, 'date') else df.index

                # 找到目标日期或最近的交易日
                available_dates = [d for d in df.index if d <= target_date]
                if available_dates:
                    latest_date = max(available_dates)
                    row = df.loc[latest_date]
                    vix_value = float(row['close'])
                    env.vix = Decimal(str(round(vix_value, 2)))
                    logger.debug(f"Fetched VIX: {vix_value}")

        except Exception as e:
            logger.warning(f"Failed to fetch VIX: {e}")

    def _fetch_sector_data(
        self,
        env: MarketEnvironment,
        start_date: date,
        end_date: date,
        target_date: date
    ):
        """获取行业 ETF 数据"""
        sector_performance = {}

        for symbol, sector_name in SECTOR_ETFS.items():
            try:
                df = self.client.get_ohlcv(symbol, start_date, end_date)

                if df is not None and not df.empty and len(df) >= 2:
                    df.index = df.index.date if hasattr(df.index, 'date') else df.index

                    available_dates = [d for d in df.index if d <= target_date]
                    if len(available_dates) >= 2:
                        # 取最近两天计算涨跌幅
                        sorted_dates = sorted(available_dates)
                        latest_date = sorted_dates[-1]
                        prev_date = sorted_dates[-2]

                        close_price = float(df.loc[latest_date]['close'])
                        prev_close = float(df.loc[prev_date]['close'])

                        change_pct = (close_price - prev_close) / prev_close * 100
                        sector_performance[symbol] = round(change_pct, 2)

            except Exception as e:
                logger.warning(f"Failed to fetch sector ETF {symbol}: {e}")

        if sector_performance:
            env.sector_performance = sector_performance

            # 找出领涨和落后板块
            sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)

            leading = [SECTOR_ETFS[s[0]] for s in sorted_sectors[:3] if s[1] > 0]
            lagging = [SECTOR_ETFS[s[0]] for s in sorted_sectors[-3:] if s[1] < 0]

            env.leading_sectors = ','.join(leading) if leading else None
            env.lagging_sectors = ','.join(lagging) if lagging else None

            logger.debug(f"Fetched {len(sector_performance)} sector ETFs")

    def _calculate_completeness(self, env: MarketEnvironment) -> Decimal:
        """计算数据完整度"""
        total_fields = 0
        filled_fields = 0

        # 关键字段检查
        key_fields = [
            'spy_close', 'spy_change_pct',
            'qqq_close', 'qqq_change_pct',
            'dia_close', 'dia_change_pct',
            'vix', 'vix_level',
            'market_trend',
            'sector_performance',
        ]

        for field in key_fields:
            total_fields += 1
            if getattr(env, field, None) is not None:
                filled_fields += 1

        completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
        return Decimal(str(round(completeness, 2)))

    def backfill_date_range(
        self,
        start_date: date,
        end_date: date,
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        批量回填日期范围内的市场环境数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            skip_existing: 是否跳过已存在的记录

        Returns:
            统计信息 {'success': n, 'failed': n, 'skipped': n}
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0}

        # 获取已存在的日期
        existing_dates: Set[date] = set()
        if skip_existing:
            existing_records = self.db.query(MarketEnvironment.date).filter(
                MarketEnvironment.date >= start_date,
                MarketEnvironment.date <= end_date
            ).all()
            existing_dates = {r.date for r in existing_records}

        # 遍历日期
        current_date = start_date
        while current_date <= end_date:
            # 跳过周末
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            # 跳过已存在
            if current_date in existing_dates:
                stats['skipped'] += 1
                current_date += timedelta(days=1)
                continue

            # 获取数据
            env = self.fetch_daily_environment(current_date)
            if env:
                stats['success'] += 1
            else:
                stats['failed'] += 1

            current_date += timedelta(days=1)

        logger.info(f"Backfill completed: {stats}")
        return stats

    def backfill_for_positions(self, positions: List) -> Dict[str, int]:
        """
        为持仓列表回填市场环境数据

        根据持仓的开仓和平仓日期，获取所需的市场环境数据

        Args:
            positions: Position 对象列表

        Returns:
            统计信息
        """
        # 收集所有需要的日期
        required_dates: Set[date] = set()

        for pos in positions:
            if pos.open_date:
                open_date = pos.open_date.date() if hasattr(pos.open_date, 'date') else pos.open_date
                required_dates.add(open_date)
            if pos.close_date:
                close_date = pos.close_date.date() if hasattr(pos.close_date, 'date') else pos.close_date
                required_dates.add(close_date)

        logger.info(f"Need to fetch market environment for {len(required_dates)} unique dates")

        # 获取已存在的日期
        existing_records = self.db.query(MarketEnvironment).filter(
            MarketEnvironment.date.in_(list(required_dates))
        ).all()
        existing_dates = {r.date: r for r in existing_records}

        stats = {'success': 0, 'failed': 0, 'skipped': 0}

        # 只获取缺失的日期
        missing_dates = required_dates - set(existing_dates.keys())

        for target_date in sorted(missing_dates):
            env = self.fetch_daily_environment(target_date)
            if env:
                stats['success'] += 1
                existing_dates[target_date] = env
            else:
                stats['failed'] += 1

        stats['skipped'] = len(required_dates) - len(missing_dates)

        logger.info(f"Backfill for positions completed: {stats}")
        return stats

    def link_positions_to_environment(self, positions: List) -> int:
        """
        将持仓与市场环境关联

        Args:
            positions: Position 对象列表

        Returns:
            成功关联的数量
        """
        # 获取所有市场环境记录
        all_envs = self.db.query(MarketEnvironment).all()
        env_by_date = {env.date: env for env in all_envs}

        linked_count = 0

        for pos in positions:
            updated = False

            # 关联入场环境
            if pos.open_date and not pos.entry_market_env_id:
                open_date = pos.open_date.date() if hasattr(pos.open_date, 'date') else pos.open_date
                if open_date in env_by_date:
                    pos.entry_market_env_id = env_by_date[open_date].id
                    updated = True

            # 关联出场环境
            if pos.close_date and not pos.exit_market_env_id:
                close_date = pos.close_date.date() if hasattr(pos.close_date, 'date') else pos.close_date
                if close_date in env_by_date:
                    pos.exit_market_env_id = env_by_date[close_date].id
                    updated = True

            if updated:
                linked_count += 1

        self.db.commit()
        logger.info(f"Linked {linked_count} positions to market environment")

        return linked_count
