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

        confidence = max(cn_score, en_score) + bonus
        can_parse = confidence >= 0.7

        logger.debug(f"Futu detection: cn={cn_score:.2f}, en={en_score:.2f}, "
                     f"bonus={bonus:.2f}, total={confidence:.2f}")

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

        # 解析期权符号
        if 'symbol' in df.columns:
            df = self._parse_option_symbols(df)

        # 解析市场类型
        if 'market' in df.columns:
            df['market'] = df['market'].apply(self._normalize_market)

        return df

    def _parse_option_symbols(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        解析期权符号

        格式: NVDA260618C205000
        - NVDA: 底层标的
        - 260618: 到期日 (YYMMDD)
        - C/P: Call/Put
        - 205000: 行权价 (需除以1000)
        """
        def parse_option(symbol):
            if pd.isna(symbol):
                return {}

            symbol = str(symbol).strip()

            # 匹配期权格式
            pattern = r'^([A-Z]+)(\d{6})([CP])(\d+)$'
            match = re.match(pattern, symbol)

            if not match:
                return {'is_option': False}

            underlying, date_str, option_type, strike_raw = match.groups()

            try:
                # 解析到期日
                expiry = datetime.strptime(date_str, '%y%m%d').date()
                # 解析行权价
                strike = int(strike_raw) / 1000.0

                return {
                    'is_option': True,
                    'underlying_symbol': underlying,
                    'option_type': 'CALL' if option_type == 'C' else 'PUT',
                    'strike_price': strike,
                    'expiration_date': expiry,
                }
            except Exception:
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
