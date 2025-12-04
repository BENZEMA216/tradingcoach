"""
Core - 核心UI组件
"""

from .metric_card import metric_card, render_metric_row, render_kpi_cards, METRIC_CARD_CSS
from .pnl_display import pnl_display, pnl_badge_html
from .data_table import (
    render_trade_table,
    render_compact_trade_list,
    inject_table_css,
    STRATEGY_NAMES,
    STRATEGY_COLORS,
    GRADE_COLORS,
)

__all__ = [
    # metric_card
    'metric_card',
    'render_metric_row',
    'render_kpi_cards',
    'METRIC_CARD_CSS',
    # pnl_display
    'pnl_display',
    'pnl_badge_html',
    # data_table
    'render_trade_table',
    'render_compact_trade_list',
    'inject_table_css',
    'STRATEGY_NAMES',
    'STRATEGY_COLORS',
    'GRADE_COLORS',
]
