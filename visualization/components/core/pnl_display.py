"""
PnL Display - 盈亏显示组件

提供一致的盈亏金额和百分比显示
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from visualization.styles import COLORS, FONTS


def pnl_display(
    value: float,
    percentage: Optional[float] = None,
    size: str = 'md',  # 'sm', 'md', 'lg', 'xl'
    show_icon: bool = True,
    show_sign: bool = True,
) -> str:
    """
    生成盈亏显示的 HTML

    Args:
        value: 盈亏金额
        percentage: 盈亏百分比 (可选)
        size: 显示大小
        show_icon: 是否显示箭头图标
        show_sign: 是否显示正负号

    Returns:
        HTML 字符串
    """
    is_profit = value >= 0
    color = COLORS['profit'] if is_profit else COLORS['loss']

    # 大小配置
    size_config = {
        'sm': {'value_size': '1rem', 'pct_size': '0.75rem'},
        'md': {'value_size': '1.5rem', 'pct_size': '0.875rem'},
        'lg': {'value_size': '2rem', 'pct_size': '1rem'},
        'xl': {'value_size': '3rem', 'pct_size': '1.25rem'},
    }
    config = size_config.get(size, size_config['md'])

    # 图标
    icon = ""
    if show_icon:
        icon = "▲ " if is_profit else "▼ "

    # 符号
    sign = ""
    if show_sign:
        sign = "+" if is_profit else ""

    # 百分比 HTML
    pct_html = ""
    if percentage is not None:
        pct_sign = "+" if percentage >= 0 else ""
        pct_html = f'''
        <span style="
            font-size: {config['pct_size']};
            margin-left: 0.5rem;
            opacity: 0.8;
        ">({pct_sign}{percentage:.2f}%)</span>
        '''

    return f'''
    <span style="
        display: inline-flex;
        align-items: center;
        font-family: {FONTS['mono']};
        font-size: {config['value_size']};
        font-weight: 700;
        color: {color};
    ">
        {icon}{sign}${abs(value):,.2f}{pct_html}
    </span>
    '''


def pnl_badge_html(
    value: float,
    show_percentage: bool = False,
    percentage: Optional[float] = None,
) -> str:
    """
    生成盈亏徽章的 HTML (适用于表格等紧凑场景)

    Args:
        value: 盈亏金额
        show_percentage: 是否显示百分比
        percentage: 盈亏百分比

    Returns:
        HTML 字符串
    """
    is_profit = value >= 0
    color = COLORS['profit'] if is_profit else COLORS['loss']
    bg_color = f"{color}15"
    icon = "▲" if is_profit else "▼"
    sign = "+" if is_profit else ""

    text = f"{sign}${abs(value):,.2f}"
    if show_percentage and percentage is not None:
        pct_sign = "+" if percentage >= 0 else ""
        text = f"{pct_sign}{percentage:.2f}%"

    return f'''
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.5rem;
        background: {bg_color};
        border-radius: 4px;
        font-family: {FONTS['mono']};
        font-size: 0.875rem;
        font-weight: 600;
        color: {color};
    ">
        {icon} {text}
    </span>
    '''
