"""
Option Symbol Parser
解析期权代码工具

解析美股期权代码（OCC格式）提取标的股票代码、到期日、期权类型、行权价等信息
"""

import re
from typing import Optional, Dict, Tuple
from datetime import datetime
from decimal import Decimal


class OptionParser:
    """
    期权代码解析器

    支持标准OCC期权代码格式：
    {UNDERLYING}{YYMMDD}{C/P}{STRIKE}

    示例:
        AAPL250404C227500 → AAPL, 2025-04-04, Call, 227.50
        TSLA250328P235000 → TSLA, 2025-03-28, Put, 235.00
        BRKB251219C500000 → BRK.B, 2025-12-19, Call, 500.00
    """

    # OCC期权代码正则表达式
    # {UNDERLYING}{YYMMDD}{C/P}{STRIKE_IN_THOUSANDTHS}
    OPTION_PATTERN = re.compile(r'^([A-Z]+?)(\d{6})([CP])(\d{5,8})$')

    # 特殊符号映射（数据库中的格式 → yfinance格式）
    SYMBOL_MAPPINGS = {
        'BRKB': 'BRK.B',   # Berkshire Hathaway B类股
        'BRK_B': 'BRK.B',
        'BF_B': 'BF.B',    # Brown-Forman B类股
    }

    @classmethod
    def is_option_symbol(cls, symbol: str) -> bool:
        """
        判断是否为期权代码

        Args:
            symbol: 股票/期权代码

        Returns:
            True if option symbol, False otherwise
        """
        if not symbol or len(symbol) < 15:
            return False

        return cls.OPTION_PATTERN.match(symbol) is not None

    @classmethod
    def parse(cls, option_symbol: str) -> Optional[Dict]:
        """
        解析期权代码

        Args:
            option_symbol: 期权代码

        Returns:
            dict with parsed info or None if not an option
            {
                'underlying': str,          # 标的股票代码
                'expiry_date': datetime,    # 到期日
                'option_type': str,         # 'call' or 'put'
                'strike': Decimal,          # 行权价
                'raw_symbol': str           # 原始代码
            }
        """
        match = cls.OPTION_PATTERN.match(option_symbol)

        if not match:
            return None

        underlying, date_str, option_type, strike_str = match.groups()

        # 解析到期日 YYMMDD
        try:
            expiry_date = datetime.strptime(date_str, '%y%m%d')
        except ValueError:
            return None

        # 解析行权价（单位：美分 → 美元）
        try:
            strike = Decimal(strike_str) / 1000
        except (ValueError, ArithmeticError):
            return None

        # 应用特殊符号映射
        normalized_underlying = cls.SYMBOL_MAPPINGS.get(underlying, underlying)

        return {
            'underlying': normalized_underlying,
            'expiry_date': expiry_date,
            'option_type': 'call' if option_type == 'C' else 'put',
            'strike': strike,
            'raw_symbol': option_symbol
        }

    @classmethod
    def extract_underlying(cls, symbol: str) -> str:
        """
        提取标的股票代码（无论是股票还是期权）

        Args:
            symbol: 股票/期权代码

        Returns:
            underlying stock symbol
        """
        parsed = cls.parse(symbol)

        if parsed:
            return parsed['underlying']
        else:
            # 不是期权，返回原代码
            return symbol

    @classmethod
    def get_option_info_string(cls, symbol: str) -> str:
        """
        获取期权信息的可读字符串

        Args:
            symbol: 期权代码

        Returns:
            Readable string like "AAPL $227.50 Call (2025-04-04)"
        """
        parsed = cls.parse(symbol)

        if not parsed:
            return symbol

        return (
            f"{parsed['underlying']} "
            f"${parsed['strike']:.2f} "
            f"{parsed['option_type'].capitalize()} "
            f"({parsed['expiry_date'].strftime('%Y-%m-%d')})"
        )


def is_option(symbol: str) -> bool:
    """便捷函数：判断是否为期权"""
    return OptionParser.is_option_symbol(symbol)


def get_underlying(symbol: str) -> str:
    """便捷函数：提取标的股票代码"""
    return OptionParser.extract_underlying(symbol)


def parse_option(symbol: str) -> Optional[Dict]:
    """便捷函数：解析期权代码"""
    return OptionParser.parse(symbol)


if __name__ == '__main__':
    # 测试
    test_symbols = [
        'AAPL',
        'AAPL250404C227500',
        'TSLA250328P235000',
        'BRKB251219C500000',
        'NVDA250207C120000'
    ]

    print("Option Parser Test:\n")

    for symbol in test_symbols:
        print(f"Symbol: {symbol}")
        print(f"  Is option: {is_option(symbol)}")
        print(f"  Underlying: {get_underlying(symbol)}")

        parsed = parse_option(symbol)
        if parsed:
            print(f"  Info: {OptionParser.get_option_info_string(symbol)}")
            print(f"  Details: {parsed}")

        print()
