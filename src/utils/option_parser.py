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

    # 富途垂直价差代码（vertical spread）— 两条腿合并为一个 symbol：
    #   单 leg:        NVDA260618C205000
    #   长短同月:      NVDA260618C205/210            （两个 C，缩写后腿 strike）
    #   长短跨月:      BIDU260320P105/260618P105
    #   不带千位:      HIMS260618C45/50
    # 这条规则在 OCC 正则匹配失败后兜底，避免 spread 被当成股票处理
    # （导致 is_option=False、multiplier=1、PnL% 算出 -220% 这种异常）
    SPREAD_PATTERN = re.compile(
        r'^([A-Z]+)\d{4,6}[CP][\d.]+/(\d{4,6}[CP])?[\d.]+$'
    )

    # 特殊符号映射（数据库中的格式 → yfinance格式）
    SYMBOL_MAPPINGS = {
        'BRKB': 'BRK.B',   # Berkshire Hathaway B类股
        'BRK_B': 'BRK.B',
        'BF_B': 'BF.B',    # Brown-Forman B类股
    }

    @classmethod
    def is_option_symbol(cls, symbol: str) -> bool:
        """
        判断是否为期权代码（含单 leg 与价差单两种）

        Args:
            symbol: 股票/期权代码

        Returns:
            True if option symbol or option spread, False otherwise
        """
        if not symbol:
            return False
        # 单 leg OCC 格式（15+ 字符）
        if len(symbol) >= 15 and cls.OPTION_PATTERN.match(symbol) is not None:
            return True
        # 价差单（含 "/" 分隔）—— spread 长度通常 >= 14 字符
        if "/" in symbol and cls.SPREAD_PATTERN.match(symbol) is not None:
            return True
        return False

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
        提取标的股票代码（无论是股票、单 leg 期权、还是价差）

        Args:
            symbol: 股票/期权代码

        Returns:
            underlying stock symbol
        """
        parsed = cls.parse(symbol)
        if parsed:
            return parsed['underlying']

        # spread 没法走 parse，但可以从前缀抽 underlying
        if symbol and "/" in symbol:
            m = cls.SPREAD_PATTERN.match(symbol)
            if m:
                return m.group(1)

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
