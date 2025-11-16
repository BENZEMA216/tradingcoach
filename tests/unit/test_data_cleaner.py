"""
测试data_cleaner.py模块
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.importers.data_cleaner import (
    DataCleaner,
    DIRECTION_MAPPING,
    INVALID_STATUSES,
    clean_csv_data
)
from src.importers.csv_parser import CSVParser


# 测试数据路径
TEST_CSV_PATH = Path(__file__).parent.parent / "fixtures" / "test_trades.csv"


@pytest.fixture
def sample_df():
    """创建测试用DataFrame"""
    parser = CSVParser(str(TEST_CSV_PATH))
    return parser.parse()


class TestDataCleaner:
    """测试DataCleaner类"""

    def test_cleaner_initialization(self, sample_df):
        """测试清洗器初始化"""
        cleaner = DataCleaner(sample_df)

        assert cleaner.df is not None
        assert len(cleaner.df) > 0
        assert cleaner.cleaned_df is None
        assert cleaner.stats['total_input'] == len(sample_df)

    def test_full_cleaning_process(self, sample_df):
        """测试完整清洗流程"""
        cleaner = DataCleaner(sample_df)
        cleaned_df = cleaner.clean()

        assert cleaned_df is not None
        assert len(cleaned_df) > 0
        assert cleaner.stats['total_output'] > 0

    def test_filter_invalid_orders(self, sample_df):
        """测试过滤无效订单"""
        cleaner = DataCleaner(sample_df)
        initial_count = len(cleaner.df)

        cleaner._filter_invalid_orders()

        # 应该过滤掉一些无效订单
        assert len(cleaner.df) <= initial_count

        # 已撤单的记录应该被过滤
        if 'status' in cleaner.df.columns:
            assert not any(cleaner.df['status'].isin(INVALID_STATUSES))

    def test_clean_numeric_fields(self, sample_df):
        """测试清理数字字段"""
        cleaner = DataCleaner(sample_df)
        cleaner._clean_numeric_fields()

        # 检查数字字段是否被正确清理
        numeric_fields = ['filled_price', 'filled_quantity', 'commission']
        for field in numeric_fields:
            if field in cleaner.df.columns:
                # 非空值应该是数字类型
                non_null_values = cleaner.df[field].dropna()
                if len(non_null_values) > 0:
                    assert all(isinstance(v, (int, float)) for v in non_null_values)

    def test_clean_number_function(self, sample_df):
        """测试_clean_number函数"""
        cleaner = DataCleaner(sample_df)

        # 测试各种输入
        assert cleaner._clean_number(None) is None
        assert cleaner._clean_number(np.nan) is None
        assert cleaner._clean_number("") is None
        assert cleaner._clean_number("-") is None

        assert cleaner._clean_number(123) == 123.0
        assert cleaner._clean_number(123.45) == 123.45
        assert cleaner._clean_number("123.45") == 123.45
        assert cleaner._clean_number("1,234.56") == 1234.56
        assert cleaner._clean_number("$100.00") == 100.0

    def test_normalize_directions(self, sample_df):
        """测试标准化交易方向"""
        cleaner = DataCleaner(sample_df)
        cleaner._normalize_directions()

        # 检查方向是否被映射
        if 'direction' in cleaner.df.columns:
            directions = cleaner.df['direction'].dropna().unique()
            valid_directions = list(DIRECTION_MAPPING.values())

            for direction in directions:
                assert direction in valid_directions or direction in DIRECTION_MAPPING.keys()

    def test_parse_timestamps(self, sample_df):
        """测试解析时间戳"""
        cleaner = DataCleaner(sample_df)
        cleaner._parse_timestamps()

        # 检查是否生成了UTC时间列
        assert 'filled_time_utc' in cleaner.df.columns or 'order_time_utc' in cleaner.df.columns

        # 检查时间是否被正确解析
        if 'filled_time_utc' in cleaner.df.columns:
            utc_times = cleaner.df['filled_time_utc'].dropna()
            if len(utc_times) > 0:
                # 应该是datetime对象且带时区信息
                assert all(pd.api.types.is_datetime64_any_dtype(utc_times.dtype)
                          or hasattr(utc_times.iloc[0], 'tzinfo'))

    def test_parse_symbols(self, sample_df):
        """测试解析Symbol"""
        cleaner = DataCleaner(sample_df)
        cleaner._parse_symbols()

        # 检查是否添加了解析后的列
        expected_columns = ['parsed_type', 'parsed_symbol', 'parsed_is_option']

        for col in expected_columns:
            assert col in cleaner.df.columns

        # 检查解析结果
        assert cleaner.stats['symbols_parsed'] > 0

    def test_handle_partial_fills(self, sample_df):
        """测试处理部分成交"""
        cleaner = DataCleaner(sample_df)

        # 先清理数字字段
        cleaner._clean_numeric_fields()

        cleaner._handle_partial_fills()

        # 检查是否添加了部分成交标记
        assert 'is_partial_fill' in cleaner.df.columns

        # 检查统计信息
        if cleaner.stats['partial_fills_split'] > 0:
            # 应该有标记为True的记录
            assert cleaner.df['is_partial_fill'].sum() > 0

    def test_validate_cleaned_data(self, sample_df):
        """测试验证清洗后的数据"""
        cleaner = DataCleaner(sample_df)
        cleaner.clean()

        errors = cleaner.stats['errors']

        # errors应该是一个列表
        assert isinstance(errors, list)

    def test_get_statistics(self, sample_df):
        """测试获取统计信息"""
        cleaner = DataCleaner(sample_df)
        cleaner.clean()

        stats = cleaner.get_statistics()

        assert isinstance(stats, dict)
        assert 'total_input' in stats
        assert 'total_output' in stats
        assert 'filtered_invalid' in stats
        assert 'partial_fills_split' in stats
        assert 'direction_normalized' in stats
        assert 'symbols_parsed' in stats


class TestDirectionMapping:
    """测试交易方向映射"""

    def test_direction_mapping_completeness(self):
        """测试方向映射的完整性"""
        assert '买入' in DIRECTION_MAPPING
        assert '卖出' in DIRECTION_MAPPING
        assert '卖空' in DIRECTION_MAPPING

    def test_mapped_directions(self):
        """测试映射后的方向"""
        assert DIRECTION_MAPPING['买入'] == 'buy'
        assert DIRECTION_MAPPING['卖出'] == 'sell'
        assert DIRECTION_MAPPING['卖空'] == 'sell_short'
        assert DIRECTION_MAPPING['买券还券'] == 'buy_to_cover'


class TestInvalidStatuses:
    """测试无效状态常量"""

    def test_invalid_statuses_list(self):
        """测试无效状态列表"""
        assert '已撤单' in INVALID_STATUSES
        assert '下单失败' in INVALID_STATUSES


class TestCleanCsvDataConvenience:
    """测试便捷函数clean_csv_data"""

    def test_clean_csv_data(self, sample_df):
        """测试便捷清洗函数"""
        cleaned_df, stats = clean_csv_data(sample_df)

        assert cleaned_df is not None
        assert len(cleaned_df) > 0
        assert isinstance(stats, dict)
        assert stats['total_output'] > 0


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_dataframe(self):
        """测试空DataFrame"""
        empty_df = pd.DataFrame()
        cleaner = DataCleaner(empty_df)

        # 应该能处理空DataFrame而不报错
        result = cleaner.clean()
        assert len(result) == 0

    def test_missing_required_columns(self):
        """测试缺少必需列"""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'TSLA'],
            'filled_price': [150.0, 250.0]
            # 缺少direction, filled_quantity等必需列
        })

        cleaner = DataCleaner(df)
        result = cleaner.clean()

        # 验证应该报告错误
        errors = cleaner.stats['errors']
        assert len(errors) > 0

    def test_all_null_values(self):
        """测试全部为空值的列"""
        df = pd.DataFrame({
            'symbol': [None, None, None],
            'direction': [None, None, None],
            'filled_quantity': [None, None, None],
            'filled_price': [None, None, None]
        })

        cleaner = DataCleaner(df)
        result = cleaner.clean()

        # 应该过滤掉所有记录
        assert len(result) == 0 or cleaner.stats['errors']

    def test_mixed_data_types(self):
        """测试混合数据类型"""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'TSLA', None],
            'direction': ['买入', '卖出', '买入'],
            'filled_quantity': [10, '20', None],  # 混合类型
            'filled_price': ['150.0', 250, None],  # 混合类型
            'filled_time': ['2025/01/15 09:30:00 (美东)', '2025/01/16 10:00:00 (美东)', None],
            'market': ['美股', '美股', '美股']
        })

        cleaner = DataCleaner(df)

        # 应该能处理混合类型而不报错
        result = cleaner.clean()
        assert result is not None

    def test_partial_fill_edge_case(self):
        """测试部分成交边界情况"""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'TSLA', 'GOOGL'],
            'direction': ['buy', 'buy', 'buy'],
            'order_quantity': [20, 10, 15],
            'filled_quantity': [15, 10, 0],  # 部分成交, 全部成交, 未成交
            'filled_price': [150.0, 250.0, 160.0],
            'filled_time': ['2025/01/15 09:30:00 (美东)'] * 3,
            'market': ['美股'] * 3
        })

        cleaner = DataCleaner(df)
        cleaner._clean_numeric_fields()
        cleaner._handle_partial_fills()

        # 第一个应该是部分成交
        assert cleaner.df.iloc[0]['is_partial_fill'] == 1

        # 第二个是全部成交
        assert cleaner.df.iloc[1]['is_partial_fill'] == 0

        # 第三个未成交（filled_quantity=0）
        # 应该不算部分成交
        assert cleaner.df.iloc[2]['is_partial_fill'] == 0
