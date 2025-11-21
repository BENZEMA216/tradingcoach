"""
Matchers - FIFO交易配对模块

提供FIFO算法的交易配对功能，将买卖交易配对成持仓记录。
"""

from src.matchers.trade_quantity import TradeQuantity
from src.matchers.symbol_matcher import SymbolMatcher
from src.matchers.fifo_matcher import FIFOMatcher, match_trades_from_database

__all__ = [
    'TradeQuantity',
    'SymbolMatcher',
    'FIFOMatcher',
    'match_trades_from_database',
]
