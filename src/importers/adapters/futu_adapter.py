"""
Futu Adapter - 富途证券 CSV 适配器

input: 富途证券导出的 CSV 文件 (中文/英文)
output: 标准化 DataFrame
pos: 适配器层 - 处理富途特有的格式和字段

支持格式:
- 历史订单 (中文): 方向, 代码, 名称, 成交价格...
- 历史订单 (英文): Side, Symbol, Name, Fill Price...
- 持仓快照 (中文/英文)

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import re
from typing import Tuple, Optional
from datetime import datetime
import pandas as pd
import logging

from ..core.base_adapter import BaseCSVAdapter
from ..configs.schema import BrokerConfig

logger = logging.getLogger(__name__)


class FutuAdapter(BaseCSVAdapter):
    """
    富途证券 CSV 适配器

    处理富途特有的功能:
    - 期权符号解析 (NVDA260618C205000)
    - 时区标记解析 ((美东), (香港))
    - 市场类型检测 (美股/港股/沪深)
    - 费用字段合并
    """

    # 富途中文版特征列
    CN_MARKER_COLUMNS = {'方向', '代码', '名称', '成交时间', '市场', '交易状态'}

    # 富途英文版特征列
    EN_MARKER_COLUMNS = {'Side', 'Symbol', 'Name', 'Fill Time', 'Markets', 'Status'}

    # 富途特有列 (用于加分)
    FUTU_UNIQUE_COLUMNS = {
        '平台使用费', 'Platform Fees',
        '对手经纪', 'Counterparty',
        '证监会征费', 'SFC Levy',
        '财汇局征费', 'FRC Levy',
    }

    def __init__(self, config: BrokerConfig):
        super().__init__(config)
        self.is_chinese = None  # 自动检测

    @classmethod
    def get_broker_id(cls) -> str:
        return "futu"

    @classmethod
    def can_parse(cls, file_path: str, sample_df: pd.DataFrame, config: BrokerConfig) -> Tuple[bool, float]:
        """
        检测是否为富途证券 CSV

        富途特征:
        - 中文版: 包含 "方向", "代码", "成交时间", "市场" 列
        - 英文版: 包含 "Side", "Symbol", "Fill Time", "Markets" 列
        - 费用列包含 "平台使用费"/"Platform Fees"

        重要：因为 FutuAdapter 同时被注册给 futu_cn 和 futu_en，必须根据
        config.broker_id 只对相应语言版本打高分，否则 detect_and_get_adapter
        会因为字典遍历顺序而把中文配置套到英文 CSV 上（导致 _map_fields
        全部找不到字段、所有 trade 静默丢失）。
        """
        columns = set(sample_df.columns)

        # 中文版检测
        cn_matched = cls.CN_MARKER_COLUMNS & columns
        cn_score = len(cn_matched) / len(cls.CN_MARKER_COLUMNS)

        # 英文版检测
        en_matched = cls.EN_MARKER_COLUMNS & columns
        en_score = len(en_matched) / len(cls.EN_MARKER_COLUMNS)

        # 富途特有列加分
        unique_matched = cls.FUTU_UNIQUE_COLUMNS & columns
        bonus = 0.15 if unique_matched else 0

        # 根据 config 限制只看相应语言
        if config.broker_id == "futu_cn":
            score = cn_score
        elif config.broker_id == "futu_en":
            score = en_score
        else:
            # 历史兼容：未指定语言的 futu 配置取较高者
            score = max(cn_score, en_score)

        confidence = score + bonus
        can_parse = confidence >= 0.7

        logger.debug(f"Futu detection ({config.broker_id}): cn={cn_score:.2f}, "
                     f"en={en_score:.2f}, bonus={bonus:.2f}, total={confidence:.2f}")

        return can_parse, min(confidence, 1.0)

    def parse(self, file_path: str) -> pd.DataFrame:
        """解析富途 CSV，自动检测中英文版本"""
        # 先读取样本检测语言
        sample = pd.read_csv(file_path, encoding='utf-8-sig', nrows=1)
        self.is_chinese = '方向' in sample.columns

        logger.info(f"Detected Futu format: {'Chinese' if self.is_chinese else 'English'}")

        # 调用基类解析
        return super().parse(file_path)

    def _transform_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """富途特有的字段转换"""
        df = super()._transform_fields(df)

        # 期权价差单 (spread orders) 的填充信息补全 — 富途对 spread 单
        # 的 Fill Qty/Fill Price/Fill Time 列是空的，只在 "Filled@Avg Price"
        # 里塞了 "2unit(s)@3.39" 这种汇总。如果不还原，spread 行会被
        # _row_to_trade_adapter 当成 "missing required field" 静默丢掉。
        df = self._fill_spread_orders(df)

        # 解析期权符号
        if 'symbol' in df.columns:
            df = self._parse_option_symbols(df)

        # 解析市场类型
        if 'market' in df.columns:
            df['market'] = df['market'].apply(self._normalize_market)

        return df

    # ------------------------------------------------------------------ #
    # 价差单 (spread) 填充补全
    # ------------------------------------------------------------------ #
    _SPREAD_FILL_RE = re.compile(
        r'^\s*(\d+(?:\.\d+)?)\s*unit\(s\)\s*@\s*([\-\d\.]+)\s*$'
    )

    def _fill_spread_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """从 raw CSV 的 "Filled@Avg Price" 列推算 spread 单的填充。"""
        if self.raw_df is None:
            return df

        raw_col = 'Filled@Avg Price' if not self.is_chinese else '已成交@均价'
        if raw_col not in self.raw_df.columns:
            return df

        # symbol contains "/" → spread
        is_spread = df['symbol'].astype(str).str.contains('/', na=False)
        if not is_spread.any():
            return df

        # filled_quantity 仍是 NaN 的 spread 行才需要补
        needs_fill = is_spread & df['filled_quantity'].isna()
        n_targets = int(needs_fill.sum())
        if n_targets == 0:
            return df

        filled_count = 0
        for idx in df.index[needs_fill]:
            raw_val = self.raw_df.loc[idx, raw_col] if idx in self.raw_df.index else None
            if pd.isna(raw_val) or not raw_val:
                continue
            m = self._SPREAD_FILL_RE.match(str(raw_val))
            if not m:
                continue
            qty = float(m.group(1))
            price = float(m.group(2))
            df.at[idx, 'filled_quantity'] = qty
            df.at[idx, 'filled_price'] = price
            # spread 用 Order Time 作 Fill Time（合理近似 — 全部成交时刻 ≈ 下单时刻）
            if 'order_time' in df.columns and pd.notna(df.at[idx, 'order_time']):
                df.at[idx, 'filled_time'] = df.at[idx, 'order_time']
            # filled_amount: 期权乘数 100/张
            df.at[idx, 'filled_amount'] = qty * price * 100
            filled_count += 1

        if filled_count:
            logger.info(
                f"Synthesized fill info for {filled_count}/{n_targets} spread orders "
                f"(from '{raw_col}' field)"
            )
        return df

    # 富途垂直价差代码 — 两个 strike 在同一行
    #   NVDA260717C195/200             单月双 strike
    #   BIDU260320P105/260618P105      双月同 strike
    #   HIMS260618C45/50               不带千位
    _SPREAD_PATTERN = re.compile(
        r'^([A-Z]+)\d{4,6}[CP][\d.]+/(\d{4,6}[CP])?[\d.]+$'
    )

    def _parse_option_symbols(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        解析期权符号

        格式: NVDA260618C205000
        - NVDA: 底层标的
        - 260618: 到期日 (YYMMDD)
        - C/P: Call/Put
        - 205000: 行权价 (需除以1000)

        Vertical spread:
        - NVDA260717C195/200 等 — 标记为期权（is_option=True）
        - underlying 从前缀提取
        - strike / expiry 不可单值表示，留空
        """
        spread_re = self._SPREAD_PATTERN

        def parse_option(symbol):
            if pd.isna(symbol):
                return {}

            symbol = str(symbol).strip()

            # 1) 单 leg OCC 格式
            pattern = r'^([A-Z]+)(\d{6})([CP])(\d+)$'
            match = re.match(pattern, symbol)
            if match:
                underlying, date_str, option_type, strike_raw = match.groups()
                try:
                    expiry = datetime.strptime(date_str, '%y%m%d').date()
                    strike = int(strike_raw) / 1000.0
                    return {
                        'is_option': True,
                        'underlying_symbol': underlying,
                        'option_type': 'CALL' if option_type == 'C' else 'PUT',
                        'strike_price': strike,
                        'expiration_date': expiry,
                    }
                except Exception:
                    pass

            # 2) Vertical spread —— 用 / 隔开两条 leg
            if '/' in symbol:
                sp = spread_re.match(symbol)
                if sp:
                    return {
                        'is_option': True,
                        'underlying_symbol': sp.group(1),
                        # 价差不能用单一 strike / expiry / type 表示
                        'option_type': None,
                        'strike_price': None,
                        'expiration_date': None,
                    }

            return {'is_option': False}

        # 应用解析
        option_info = df['symbol'].apply(parse_option)

        # 展开到各列
        df['is_option'] = option_info.apply(lambda x: x.get('is_option', False))
        df['underlying_symbol'] = option_info.apply(lambda x: x.get('underlying_symbol'))
        df['option_type'] = option_info.apply(lambda x: x.get('option_type'))
        df['strike_price'] = option_info.apply(lambda x: x.get('strike_price'))
        df['expiration_date'] = option_info.apply(lambda x: x.get('expiration_date'))

        return df

    def _normalize_market(self, market: str) -> str:
        """标准化市场类型"""
        if pd.isna(market):
            return 'us'  # 默认美股

        market = str(market).strip().lower()

        market_mapping = {
            '美股': 'us',
            'us': 'us',
            'us stock': 'us',
            '港股': 'hk',
            'hk': 'hk',
            'hk stock': 'hk',
            '沪深': 'cn',
            'cn': 'cn',
            'a股': 'cn',
        }

        return market_mapping.get(market, 'us')
