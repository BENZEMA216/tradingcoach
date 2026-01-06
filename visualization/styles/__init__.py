"""
Terminal Finance Design System
专业交易终端风格设计系统
"""

from .theme import COLORS, FONTS, SPACING, SHADOWS
from .css import inject_global_css, get_global_css
from .components import (
    glow_card,
    metric_display,
    pnl_badge,
    grade_badge,
    progress_ring,
    indicator_card,
    section_header,
    stat_row,
    strategy_badge,
    direction_badge,
    date_range_display,
    render_html,
    render_progress_rings,
)
from .plotly_theme import (
    get_plotly_theme,
    apply_dark_theme,
    create_dark_candlestick,
)

__all__ = [
    # Theme
    'COLORS', 'FONTS', 'SPACING', 'SHADOWS',
    # CSS
    'inject_global_css', 'get_global_css',
    # Components
    'glow_card', 'metric_display', 'pnl_badge', 'grade_badge',
    'progress_ring', 'indicator_card', 'section_header', 'stat_row',
    'strategy_badge', 'direction_badge', 'date_range_display',
    'render_html', 'render_progress_rings',
    # Plotly
    'get_plotly_theme', 'apply_dark_theme', 'create_dark_candlestick',
]
