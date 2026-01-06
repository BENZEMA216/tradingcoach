"""
Symbol解析器

识别和解析不同类型的交易品种：股票、期权、窝轮等
"""

import re
from datetime import datetime
from typing import Dict, Tuple, Optional
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class SymbolType:
    """Symbol类型枚举"""
    US_STOCK = 'us_stock'        # 美股股票
    HK_STOCK = 'hk_stock'        # 港股股票
    CN_STOCK = 'cn_stock'        # A股股票
    US_OPTION = 'us_option'      # 美股期权
    HK_WARRANT = 'hk_warrant'    # 港股窝轮
    ETF = 'etf'                  # ETF
    UNKNOWN = 'unknown'          # 未知类型


def parse_symbol(symbol: str, symbol_name: str = None, market: str = None) -> Dict:
    """
    解析symbol，识别类型并提取信息

    Args:
        symbol: 股票/期权代码
        symbol_name: 名称（可选，辅助判断）
        market: 市场类型（可选）

    Returns:
        dict: {
            'type': 类型,
            'symbol': 原始代码,
            'underlying_symbol': 标的代码（期权/窝轮）,
            'expiration_date': 到期日（期权/窝轮）,
            'option_type': 期权类型 (CALL/PUT),
            'strike_price': 行权价,
            'is_option': 是否为期权/窝轮
        }
    """
    # Handle NaN and None values
    if pd.isna(symbol) or not symbol:
        return _create_symbol_info(SymbolType.UNKNOWN, symbol)

    # Convert to string if needed (e.g., if it's a float or other type)
    if not isinstance(symbol, str):
        symbol = str(symbol)

    symbol = symbol.strip()

    # 1. 尝试解析美股期权
    if _is_us_option(symbol):
        return _parse_us_option(symbol)

    # 2. 尝试解析港股窝轮（只有明确检测到窝轮特征时才归类为窝轮）
    if _is_hk_warrant(symbol, symbol_name):
        return _parse_hk_warrant(symbol, symbol_name)

    # 3. 判断股票类型
    if market == '美股' or _is_us_stock(symbol):
        return _create_symbol_info(SymbolType.US_STOCK, symbol)

    if market == '港股' or _is_hk_stock(symbol):
        return _create_symbol_info(SymbolType.HK_STOCK, symbol)

    if market == '沪深' or _is_cn_stock(symbol):
        return _create_symbol_info(SymbolType.CN_STOCK, symbol)

    # 默认返回未知类型
    return _create_symbol_info(SymbolType.UNKNOWN, symbol)


def _is_us_option(symbol: str) -> bool:
    """判断是否为美股期权"""
    # 美股期权格式: AAPL250117C00150000 或 SPY250321C565000
    # 格式: 标的(1-5字母) + 到期日(6位YYMMDD) + C/P + 行权价(5-8位数字)
    # 行权价可能是5-8位，取决于价格和券商格式
    pattern = r'^[A-Z]{1,5}\d{6}[CP]\d{5,8}$'
    return bool(re.match(pattern, symbol))


def _parse_us_option(symbol: str) -> Dict:
    """
    解析美股期权代码

    格式: AAPL250117C00150000 或 SPY250321C565000
    - AAPL/SPY: 标的
    - 250117: 到期日 (2025-01-17)
    - C: CALL (P: PUT)
    - 00150000/565000: 行权价 (5-8位数字)

    Examples:
        >>> _parse_us_option("AAPL250117C00150000")
        {
            'type': 'us_option',
            'symbol': 'AAPL250117C00150000',
            'underlying_symbol': 'AAPL',
            'expiration_date': datetime(2025, 1, 17),
            'option_type': 'CALL',
            'strike_price': 150.0,
            'is_option': True
        }
    """
    try:
        # 使用正则提取各部分 (行权价5-8位)
        match = re.match(r'^([A-Z]{1,5})(\d{6})([CP])(\d{5,8})$', symbol)
        if not match:
            logger.warning(f"Invalid US option format: {symbol}")
            return _create_symbol_info(SymbolType.UNKNOWN, symbol)

        underlying = match.group(1)
        date_str = match.group(2)
        option_type = 'CALL' if match.group(3) == 'C' else 'PUT'
        strike_str = match.group(4)

        # 解析到期日: YYMMDD -> YYYY-MM-DD
        year = 2000 + int(date_str[0:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
        expiration_date = datetime(year, month, day).date()

        # 解析行权价: 统一除以 1000
        # 格式: 565000 = $565.00, 185000 = $185.00, 50000 = $50.00
        # 不管是 5位还是8位，都是实际价格 * 1000
        strike_int = int(strike_str)
        strike_price = strike_int / 1000.0

        return {
            'type': SymbolType.US_OPTION,
            'symbol': symbol,
            'underlying_symbol': underlying,
            'expiration_date': expiration_date,
            'option_type': option_type,
            'strike_price': strike_price,
            'is_option': True
        }

    except Exception as e:
        logger.error(f"Error parsing US option {symbol}: {e}")
        return _create_symbol_info(SymbolType.UNKNOWN, symbol)


def _is_hk_warrant(symbol: str, symbol_name: str = None) -> bool:
    """判断是否为港股窝轮"""
    # 港股窝轮代码通常是5位数字，且名称包含特定关键词
    if not re.match(r'^\d{5}$', symbol):
        return False

    if symbol_name:
        # 窝轮名称通常包含: 购、沽、认购、认沽、Call、Put、C.C、P.C等
        warrant_keywords = ['购', '沽', '认购', '认沽', 'Call', 'Put', '.C']
        return any(keyword in symbol_name for keyword in warrant_keywords)

    return False


def _parse_hk_warrant(symbol: str, symbol_name: str = None) -> Dict:
    """
    解析港股窝轮

    港股窝轮代码格式: 18099
    名称示例: "小米摩通五乙购B.C"

    从名称中提取信息:
    - 标的: 小米
    - 发行商: 摩通
    - 类型: 购 (CALL) / 沽 (PUT)
    """
    info = {
        'type': SymbolType.HK_WARRANT,
        'symbol': symbol,
        'underlying_symbol': None,
        'expiration_date': None,
        'option_type': None,
        'strike_price': None,
        'is_option': True
    }

    if not symbol_name:
        return info

    try:
        # 尝试提取期权类型
        if '购' in symbol_name or 'Call' in symbol_name or '.C' in symbol_name:
            info['option_type'] = 'CALL'
        elif '沽' in symbol_name or 'Put' in symbol_name or '.P' in symbol_name:
            info['option_type'] = 'PUT'

        # 尝试从名称中提取标的（简化版本）
        # 例如: "小米摩通五乙购B.C" -> 标的可能是"小米"
        # 这里只做简单处理，实际可能需要更复杂的逻辑
        for keyword in ['摩通', '瑞银', '法巴', '高盛', '中银', '汇丰']:
            if keyword in symbol_name:
                underlying_name = symbol_name.split(keyword)[0]
                info['underlying_symbol'] = underlying_name
                break

        logger.debug(f"Parsed HK warrant: {symbol} -> {info}")

    except Exception as e:
        logger.error(f"Error parsing HK warrant {symbol}: {e}")

    return info


def _is_us_stock(symbol: str) -> bool:
    """判断是否为美股股票（简单规则）"""
    # 美股通常是1-5个大写字母
    return bool(re.match(r'^[A-Z]{1,5}$', symbol))


def _is_hk_stock(symbol: str) -> bool:
    """判断是否为港股股票"""
    # 港股代码: 5位数字 (如 00700, 01810)
    return bool(re.match(r'^\d{5}$', symbol))


def _is_cn_stock(symbol: str) -> bool:
    """判断是否为A股股票"""
    # A股代码: 6位数字 (如 600000, 000001)
    return bool(re.match(r'^\d{6}$', symbol))


def _create_symbol_info(symbol_type: str, symbol: str) -> Dict:
    """创建标准的symbol信息字典"""
    return {
        'type': symbol_type,
        'symbol': symbol,
        'underlying_symbol': None,
        'expiration_date': None,
        'option_type': None,
        'strike_price': None,
        'is_option': symbol_type in [SymbolType.US_OPTION, SymbolType.HK_WARRANT]
    }


def format_option_symbol(underlying: str, expiry_date: datetime, option_type: str, strike: float) -> str:
    """
    格式化为标准期权代码

    Args:
        underlying: 标的代码 (e.g., 'AAPL')
        expiry_date: 到期日
        option_type: 'CALL' or 'PUT'
        strike: 行权价

    Returns:
        str: 格式化的期权代码 (e.g., 'AAPL250117C00150000')
    """
    # 日期格式: YYMMDD
    date_str = expiry_date.strftime('%y%m%d')

    # 期权类型: C/P
    type_char = 'C' if option_type.upper() == 'CALL' else 'P'

    # 行权价: 乘以1000并转为8位字符串
    strike_str = f"{int(strike * 1000):08d}"

    return f"{underlying}{date_str}{type_char}{strike_str}"


def get_underlying_symbol(symbol_info: Dict) -> Optional[str]:
    """获取标的股票代码（如果是期权/窝轮）"""
    return symbol_info.get('underlying_symbol')


def is_option_or_warrant(symbol_info: Dict) -> bool:
    """判断是否为期权或窝轮"""
    return symbol_info.get('is_option', False)
