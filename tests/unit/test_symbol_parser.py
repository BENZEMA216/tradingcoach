"""
测试symbol_parser.py模块
"""

import pytest
from datetime import datetime, date

from src.utils.symbol_parser import (
    parse_symbol,
    SymbolType,
    format_option_symbol,
    get_underlying_symbol,
    is_option_or_warrant,
    _is_us_option,
    _parse_us_option,
    _is_hk_warrant,
    _parse_hk_warrant,
    _is_us_stock,
    _is_hk_stock,
    _is_cn_stock,
)


class TestParseUsOption:
    """测试美股期权解析"""

    def test_parse_valid_us_option(self):
        """测试解析有效的美股期权代码"""
        symbol = "AAPL250117C00150000"
        result = parse_symbol(symbol)

        assert result['type'] == SymbolType.US_OPTION
        assert result['symbol'] == "AAPL250117C00150000"
        assert result['underlying_symbol'] == "AAPL"
        assert result['option_type'] == "CALL"
        assert result['strike_price'] == 150.0
        assert result['expiration_date'] == date(2025, 1, 17)
        assert result['is_option'] is True

    def test_parse_us_put_option(self):
        """测试解析PUT期权"""
        symbol = "TSLA250328P00235000"
        result = parse_symbol(symbol)

        assert result['type'] == SymbolType.US_OPTION
        assert result['underlying_symbol'] == "TSLA"
        assert result['option_type'] == "PUT"
        assert result['strike_price'] == 235.0

    def test_is_us_option_detection(self):
        """测试美股期权识别"""
        assert _is_us_option("AAPL250117C00150000") is True
        assert _is_us_option("TSLA250328P00235000") is True
        assert _is_us_option("AAPL") is False
        assert _is_us_option("00700") is False

    def test_parse_short_ticker_option(self):
        """测试短ticker的期权（1-2个字母）"""
        symbol = "F250417C00012500"  # Ford
        result = _parse_us_option(symbol)

        assert result['underlying_symbol'] == "F"
        assert result['strike_price'] == 12.5


class TestParseHkWarrant:
    """测试港股窝轮解析"""

    def test_parse_hk_warrant_with_call(self):
        """测试解析认购窝轮"""
        symbol = "18099"
        symbol_name = "小米摩通五乙购B.C"
        result = parse_symbol(symbol, symbol_name, market='港股')

        assert result['type'] == SymbolType.HK_WARRANT
        assert result['symbol'] == "18099"
        assert result['option_type'] == "CALL"
        assert result['is_option'] is True

    def test_parse_hk_warrant_with_put(self):
        """测试解析认沽窝轮"""
        symbol = "12345"
        symbol_name = "腾讯高盛沽轮.P"
        result = _parse_hk_warrant(symbol, symbol_name)

        assert result['option_type'] == "PUT"

    def test_is_hk_warrant_detection(self):
        """测试窝轮识别"""
        assert _is_hk_warrant("18099", "小米摩通五乙购B.C") is True
        assert _is_hk_warrant("12345", "腾讯认购") is True
        assert _is_hk_warrant("18099", None) is False  # 没有名称
        assert _is_hk_warrant("AAPL", "Apple") is False  # 不是5位数字

    def test_extract_underlying_from_name(self):
        """测试从名称中提取标的"""
        symbol = "18099"
        symbol_name = "小米摩通五乙购B.C"
        result = _parse_hk_warrant(symbol, symbol_name)

        # 应该提取出"小米"
        assert result['underlying_symbol'] == "小米"


class TestParseStock:
    """测试股票代码解析"""

    def test_parse_us_stock(self):
        """测试解析美股"""
        result = parse_symbol("AAPL", market='美股')

        assert result['type'] == SymbolType.US_STOCK
        assert result['symbol'] == "AAPL"
        assert result['is_option'] is False
        assert result['underlying_symbol'] is None

    def test_parse_hk_stock(self):
        """测试解析港股"""
        result = parse_symbol("00700", market='港股')

        assert result['type'] == SymbolType.HK_STOCK
        assert result['symbol'] == "00700"
        assert result['is_option'] is False

    def test_parse_cn_stock(self):
        """测试解析A股"""
        result = parse_symbol("600000", market='沪深')

        assert result['type'] == SymbolType.CN_STOCK
        assert result['symbol'] == "600000"
        assert result['is_option'] is False

    def test_is_us_stock_detection(self):
        """测试美股识别"""
        assert _is_us_stock("AAPL") is True
        assert _is_us_stock("TSLA") is True
        assert _is_us_stock("GOOGL") is True
        assert _is_us_stock("00700") is False
        assert _is_us_stock("600000") is False

    def test_is_hk_stock_detection(self):
        """测试港股识别"""
        assert _is_hk_stock("00700") is True
        assert _is_hk_stock("01810") is True
        assert _is_hk_stock("AAPL") is False

    def test_is_cn_stock_detection(self):
        """测试A股识别"""
        assert _is_cn_stock("600000") is True
        assert _is_cn_stock("000001") is True
        assert _is_cn_stock("AAPL") is False


class TestSymbolTypeRecognition:
    """测试symbol类型自动识别（不提供market参数）"""

    def test_auto_recognize_us_option(self):
        """测试自动识别美股期权"""
        result = parse_symbol("AAPL250117C00150000")
        assert result['type'] == SymbolType.US_OPTION

    def test_auto_recognize_us_stock(self):
        """测试自动识别美股"""
        result = parse_symbol("AAPL")
        assert result['type'] == SymbolType.US_STOCK

    def test_auto_recognize_hk_stock(self):
        """测试自动识别港股（无窝轮标记）"""
        result = parse_symbol("00700")
        assert result['type'] == SymbolType.HK_STOCK

    def test_unknown_symbol(self):
        """测试未知类型symbol"""
        result = parse_symbol("UNKNOWN123!@#")
        assert result['type'] == SymbolType.UNKNOWN


class TestFormatOptionSymbol:
    """测试期权代码格式化"""

    def test_format_call_option(self):
        """测试格式化CALL期权"""
        underlying = "AAPL"
        expiry = datetime(2025, 1, 17)
        option_type = "CALL"
        strike = 150.0

        result = format_option_symbol(underlying, expiry, option_type, strike)
        assert result == "AAPL250117C00150000"

    def test_format_put_option(self):
        """测试格式化PUT期权"""
        underlying = "TSLA"
        expiry = datetime(2025, 3, 28)
        option_type = "PUT"
        strike = 235.0

        result = format_option_symbol(underlying, expiry, option_type, strike)
        assert result == "TSLA250328P00235000"

    def test_format_with_decimal_strike(self):
        """测试带小数的行权价"""
        underlying = "SPY"
        expiry = datetime(2025, 3, 21)
        option_type = "CALL"
        strike = 565.5

        result = format_option_symbol(underlying, expiry, option_type, strike)
        assert result == "SPY250321C00565500"


class TestHelperFunctions:
    """测试辅助函数"""

    def test_get_underlying_symbol_from_option(self):
        """测试从期权获取标的"""
        symbol_info = parse_symbol("AAPL250117C00150000")
        underlying = get_underlying_symbol(symbol_info)

        assert underlying == "AAPL"

    def test_get_underlying_symbol_from_stock(self):
        """测试从股票获取标的（应返回None）"""
        symbol_info = parse_symbol("AAPL")
        underlying = get_underlying_symbol(symbol_info)

        assert underlying is None

    def test_is_option_or_warrant_true(self):
        """测试判断是否为期权/窝轮（True）"""
        # 美股期权
        option_info = parse_symbol("AAPL250117C00150000")
        assert is_option_or_warrant(option_info) is True

        # 港股窝轮
        warrant_info = parse_symbol("18099", "小米摩通五乙购B.C", "港股")
        assert is_option_or_warrant(warrant_info) is True

    def test_is_option_or_warrant_false(self):
        """测试判断是否为期权/窝轮（False）"""
        stock_info = parse_symbol("AAPL")
        assert is_option_or_warrant(stock_info) is False


class TestEdgeCases:
    """测试边界情况"""

    def test_parse_empty_symbol(self):
        """测试空symbol"""
        result = parse_symbol("")
        assert result['type'] == SymbolType.UNKNOWN

    def test_parse_none_symbol(self):
        """测试None symbol"""
        result = parse_symbol(None)
        assert result['type'] == SymbolType.UNKNOWN

    def test_parse_with_whitespace(self):
        """测试带空格的symbol"""
        result = parse_symbol("  AAPL  ")
        assert result['type'] == SymbolType.US_STOCK
        assert result['symbol'] == "AAPL"  # 应该被trim

    def test_invalid_option_format(self):
        """测试无效的期权格式"""
        # 格式不对的"期权"代码
        result = _parse_us_option("AAPL123")
        assert result['type'] == SymbolType.UNKNOWN
