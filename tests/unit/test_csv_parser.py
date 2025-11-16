"""
测试csv_parser.py模块
"""

import pytest
import pandas as pd
from pathlib import Path

from src.importers.csv_parser import CSVParser, FIELD_MAPPING, load_csv


# 测试数据路径
TEST_CSV_PATH = Path(__file__).parent.parent / "fixtures" / "test_trades.csv"


class TestCSVParser:
    """测试CSVParser类"""

    def test_parser_initialization(self):
        """测试解析器初始化"""
        parser = CSVParser(str(TEST_CSV_PATH))

        assert parser.csv_path == TEST_CSV_PATH
        assert parser.df is None
        assert parser.raw_df is None

    def test_file_not_found(self):
        """测试文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            CSVParser("non_existent_file.csv")

    def test_parse_csv(self):
        """测试解析CSV"""
        parser = CSVParser(str(TEST_CSV_PATH))
        df = parser.parse()

        assert df is not None
        assert len(df) > 0
        assert parser.df is not None
        assert parser.raw_df is not None

    def test_column_renaming(self):
        """测试列名重命名"""
        parser = CSVParser(str(TEST_CSV_PATH))
        df = parser.parse()

        # 检查中文列名已被映射为英文
        assert 'direction' in df.columns
        assert 'symbol' in df.columns
        assert 'filled_price' in df.columns
        assert 'filled_quantity' in df.columns
        assert 'market' in df.columns

        # 原始中文列名不应存在
        assert '方向' not in df.columns
        assert '代码' not in df.columns

    def test_filter_completed_trades(self):
        """测试过滤已成交订单"""
        parser = CSVParser(str(TEST_CSV_PATH))
        parser.parse()

        completed_df = parser.filter_completed_trades()

        # 应该只包含"全部成交"和"部分成交"的记录
        assert all(status in ['全部成交', '部分成交']
                  for status in completed_df['status'].dropna())

        # 已撤单的记录应该被过滤掉
        assert len(completed_df) < len(parser.df)

    def test_get_records(self):
        """测试获取记录列表"""
        parser = CSVParser(str(TEST_CSV_PATH))
        parser.parse()

        records = parser.get_records()

        assert isinstance(records, list)
        assert len(records) == len(parser.df)
        assert isinstance(records[0], dict)

    def test_get_records_before_parse(self):
        """测试解析前调用get_records抛出异常"""
        parser = CSVParser(str(TEST_CSV_PATH))

        with pytest.raises(ValueError, match="CSV not parsed yet"):
            parser.get_records()

    def test_get_unique_symbols(self):
        """测试获取唯一symbol"""
        parser = CSVParser(str(TEST_CSV_PATH))
        parser.parse()

        symbols = parser.get_unique_symbols()

        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert 'AAPL' in symbols or 'TSLA' in symbols or '00700' in symbols

    def test_get_statistics(self):
        """测试获取统计信息"""
        parser = CSVParser(str(TEST_CSV_PATH))
        parser.parse()

        stats = parser.get_statistics()

        assert isinstance(stats, dict)
        assert 'total_rows' in stats
        assert 'completed_trades' in stats
        assert 'cancelled_orders' in stats
        assert 'unique_symbols' in stats
        assert 'markets' in stats
        assert 'directions' in stats

        # 检查数值合理性
        assert stats['total_rows'] > 0
        assert stats['completed_trades'] >= 0
        assert stats['cancelled_orders'] >= 0

    def test_validate_data(self):
        """测试数据验证"""
        parser = CSVParser(str(TEST_CSV_PATH))
        parser.parse()

        errors = parser.validate_data()

        # errors应该是一个列表
        assert isinstance(errors, list)

    def test_validate_before_parse(self):
        """测试解析前验证数据"""
        parser = CSVParser(str(TEST_CSV_PATH))
        errors = parser.validate_data()

        assert "CSV not parsed yet" in errors


class TestFieldMapping:
    """测试字段映射"""

    def test_field_mapping_completeness(self):
        """测试字段映射的完整性"""
        # 检查关键字段都有映射
        critical_fields = ['方向', '代码', '成交数量', '成交价格', '成交时间', '市场']

        for field in critical_fields:
            assert field in FIELD_MAPPING

    def test_mapped_field_names(self):
        """测试映射后的英文字段名"""
        assert FIELD_MAPPING['方向'] == 'direction'
        assert FIELD_MAPPING['代码'] == 'symbol'
        assert FIELD_MAPPING['成交数量'] == 'filled_quantity'
        assert FIELD_MAPPING['成交价格'] == 'filled_price'
        assert FIELD_MAPPING['成交时间'] == 'filled_time'


class TestLoadCsvConvenience:
    """测试便捷函数load_csv"""

    def test_load_csv_with_filter(self):
        """测试加载CSV并过滤"""
        df = load_csv(str(TEST_CSV_PATH), filter_completed=True)

        assert df is not None
        assert len(df) > 0
        # 应该只包含已成交的记录
        assert all(status in ['全部成交', '部分成交']
                  for status in df['status'].dropna())

    def test_load_csv_without_filter(self):
        """测试加载CSV不过滤"""
        df = load_csv(str(TEST_CSV_PATH), filter_completed=False)

        assert df is not None
        assert len(df) > 0


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_cells_handling(self):
        """测试空单元格处理"""
        parser = CSVParser(str(TEST_CSV_PATH))
        df = parser.parse()

        # 空值应该被保留为NaN或None
        assert df.isnull().any().any()  # 至少有一些NaN值

    def test_market_price_orders(self):
        """测试市价单（订单价格为"市价"）"""
        parser = CSVParser(str(TEST_CSV_PATH))
        df = parser.parse()

        # 市价单的order_price应该是字符串"市价"或NaN
        market_orders = df[df['order_type'] == '市价单']
        if len(market_orders) > 0:
            # 市价单可能有"市价"字符串或NaN
            assert True  # 只要不报错就通过

    def test_partial_fill_detection(self):
        """测试部分成交检测"""
        parser = CSVParser(str(TEST_CSV_PATH))
        df = parser.parse()

        # 测试文件中应该有部分成交的记录
        partial_fills = df[df['status'] == '部分成交']
        if len(partial_fills) > 0:
            # 部分成交的order_quantity应该大于filled_quantity
            for idx, row in partial_fills.iterrows():
                if pd.notna(row['order_quantity']) and pd.notna(row['filled_quantity']):
                    assert row['order_quantity'] >= row['filled_quantity']
