"""
FilterBar - 统一筛选栏组件

提供页面顶部的统一筛选界面，支持:
- 日期范围选择
- 股票多选
- 盈亏类型切换
- 评分范围滑块
- 策略筛选
- 等级筛选
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Optional, Callable
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from visualization.styles import COLORS, FONTS
from visualization.components.filters.filter_context import FilterContext


def render_filter_bar(
    available_symbols: List[str],
    available_strategies: Optional[List[str]] = None,
    available_grades: Optional[List[str]] = None,
    show_date_range: bool = True,
    show_symbols: bool = True,
    show_pnl_type: bool = True,
    show_score_range: bool = True,
    show_strategies: bool = True,
    show_grades: bool = True,
    on_change: Optional[Callable] = None,
    compact: bool = False,
) -> None:
    """
    渲染统一筛选栏

    Args:
        available_symbols: 可选股票列表
        available_strategies: 可选策略列表
        available_grades: 可选等级列表
        show_date_range: 是否显示日期筛选
        show_symbols: 是否显示股票筛选
        show_pnl_type: 是否显示盈亏类型
        show_score_range: 是否显示评分范围
        show_strategies: 是否显示策略筛选
        show_grades: 是否显示等级筛选
        on_change: 筛选变化时的回调函数
        compact: 是否使用紧凑模式
    """
    # 初始化筛选状态
    FilterContext.initialize()

    # 筛选栏容器样式
    st.markdown(f"""
    <style>
    .filter-bar {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    .filter-label {{
        color: {COLORS['text_muted']};
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }}
    .filter-summary {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid {COLORS['border']};
    }}
    .filter-count {{
        background: {COLORS['accent_cyan']}20;
        color: {COLORS['accent_cyan']};
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    </style>
    """, unsafe_allow_html=True)

    # 筛选状态摘要
    active_count = FilterContext.get_active_filter_count()
    summary_text = FilterContext.get_summary_text()

    col_summary, col_clear = st.columns([5, 1])

    with col_summary:
        if active_count > 0:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="filter-count">{active_count} 个筛选</span>
                <span style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">
                    {summary_text}
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <span style="color: {COLORS['text_muted']}; font-size: 0.85rem;">
                显示全部交易数据
            </span>
            """, unsafe_allow_html=True)

    with col_clear:
        if active_count > 0:
            if st.button("清除筛选", key="clear_filters", type="secondary"):
                FilterContext.clear()
                if on_change:
                    on_change()
                st.rerun()

    # 筛选选项行
    if compact:
        _render_compact_filters(
            available_symbols, available_strategies, available_grades,
            show_date_range, show_symbols, show_pnl_type,
            show_score_range, show_strategies, show_grades, on_change
        )
    else:
        _render_full_filters(
            available_symbols, available_strategies, available_grades,
            show_date_range, show_symbols, show_pnl_type,
            show_score_range, show_strategies, show_grades, on_change
        )


def _render_full_filters(
    available_symbols: List[str],
    available_strategies: Optional[List[str]],
    available_grades: Optional[List[str]],
    show_date_range: bool,
    show_symbols: bool,
    show_pnl_type: bool,
    show_score_range: bool,
    show_strategies: bool,
    show_grades: bool,
    on_change: Optional[Callable],
) -> None:
    """渲染完整筛选栏（两行布局）"""

    # 第一行: 日期 + 股票 + 盈亏类型
    cols_row1 = st.columns([2, 2, 1.5] if show_pnl_type else [2, 2])
    col_idx = 0

    if show_date_range:
        with cols_row1[col_idx]:
            _render_date_range_filter(on_change)
        col_idx += 1

    if show_symbols:
        with cols_row1[col_idx]:
            _render_symbols_filter(available_symbols, on_change)
        col_idx += 1

    if show_pnl_type and col_idx < len(cols_row1):
        with cols_row1[col_idx]:
            _render_pnl_type_filter(on_change)

    # 第二行: 评分 + 策略 + 等级
    show_row2 = show_score_range or show_strategies or show_grades

    if show_row2:
        st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

        cols_row2 = st.columns([2, 2, 1.5])
        col_idx = 0

        if show_score_range:
            with cols_row2[col_idx]:
                _render_score_range_filter(on_change)
            col_idx += 1

        if show_strategies and available_strategies:
            with cols_row2[col_idx]:
                _render_strategies_filter(available_strategies, on_change)
            col_idx += 1

        if show_grades and available_grades and col_idx < len(cols_row2):
            with cols_row2[col_idx]:
                _render_grades_filter(available_grades, on_change)


def _render_compact_filters(
    available_symbols: List[str],
    available_strategies: Optional[List[str]],
    available_grades: Optional[List[str]],
    show_date_range: bool,
    show_symbols: bool,
    show_pnl_type: bool,
    show_score_range: bool,
    show_strategies: bool,
    show_grades: bool,
    on_change: Optional[Callable],
) -> None:
    """渲染紧凑筛选栏（使用expander）"""

    with st.expander("🔍 筛选选项", expanded=False):
        cols = st.columns(3)

        with cols[0]:
            if show_date_range:
                _render_date_range_filter(on_change)
            if show_score_range:
                _render_score_range_filter(on_change)

        with cols[1]:
            if show_symbols:
                _render_symbols_filter(available_symbols, on_change)
            if show_strategies and available_strategies:
                _render_strategies_filter(available_strategies, on_change)

        with cols[2]:
            if show_pnl_type:
                _render_pnl_type_filter(on_change)
            if show_grades and available_grades:
                _render_grades_filter(available_grades, on_change)


def _render_date_range_filter(on_change: Optional[Callable]) -> None:
    """渲染日期范围筛选"""
    st.markdown(f"<div class='filter-label'>📅 日期范围</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "开始日期",
            value=FilterContext.get('date_start'),
            key="filter_date_start_input",
            label_visibility="collapsed",
        )
        if start_date != FilterContext.get('date_start'):
            FilterContext.set('date_start', start_date)
            if on_change:
                on_change()

    with col2:
        end_date = st.date_input(
            "结束日期",
            value=FilterContext.get('date_end'),
            key="filter_date_end_input",
            label_visibility="collapsed",
        )
        if end_date != FilterContext.get('date_end'):
            FilterContext.set('date_end', end_date)
            if on_change:
                on_change()


def _render_symbols_filter(
    available_symbols: List[str],
    on_change: Optional[Callable]
) -> None:
    """渲染股票筛选"""
    st.markdown(f"<div class='filter-label'>📊 股票</div>", unsafe_allow_html=True)

    current_symbols = FilterContext.get('symbols') or []

    selected = st.multiselect(
        "选择股票",
        options=available_symbols,
        default=current_symbols,
        key="filter_symbols_input",
        label_visibility="collapsed",
        placeholder="全部股票",
    )

    if selected != current_symbols:
        FilterContext.set('symbols', selected)
        if on_change:
            on_change()


def _render_pnl_type_filter(on_change: Optional[Callable]) -> None:
    """渲染盈亏类型筛选"""
    st.markdown(f"<div class='filter-label'>💰 盈亏</div>", unsafe_allow_html=True)

    options = {'all': '全部', 'profit': '盈利', 'loss': '亏损'}
    current = FilterContext.get('pnl_type') or 'all'

    # 使用 radio 横向排列
    selected = st.radio(
        "盈亏类型",
        options=list(options.keys()),
        format_func=lambda x: options[x],
        index=list(options.keys()).index(current),
        key="filter_pnl_type_input",
        label_visibility="collapsed",
        horizontal=True,
    )

    if selected != current:
        FilterContext.set('pnl_type', selected)
        if on_change:
            on_change()


def _render_score_range_filter(on_change: Optional[Callable]) -> None:
    """渲染评分范围筛选"""
    st.markdown(f"<div class='filter-label'>⭐ 评分范围</div>", unsafe_allow_html=True)

    current_min = FilterContext.get('score_min') or 0
    current_max = FilterContext.get('score_max') or 100

    score_range = st.slider(
        "评分范围",
        min_value=0,
        max_value=100,
        value=(current_min, current_max),
        key="filter_score_range_input",
        label_visibility="collapsed",
    )

    if score_range[0] != current_min or score_range[1] != current_max:
        FilterContext.set('score_min', score_range[0])
        FilterContext.set('score_max', score_range[1])
        if on_change:
            on_change()


def _render_strategies_filter(
    available_strategies: List[str],
    on_change: Optional[Callable]
) -> None:
    """渲染策略筛选"""
    st.markdown(f"<div class='filter-label'>🎯 策略</div>", unsafe_allow_html=True)

    current_strategies = FilterContext.get('strategies') or []

    # 策略名称映射
    strategy_names = {
        'trend': '趋势跟踪',
        'mean_reversion': '均值回归',
        'breakout': '突破交易',
        'range': '区间交易',
        'momentum': '动量交易',
        'unknown': '未分类',
    }

    display_options = [strategy_names.get(s, s) for s in available_strategies]
    current_display = [strategy_names.get(s, s) for s in current_strategies]

    selected_display = st.multiselect(
        "选择策略",
        options=display_options,
        default=current_display,
        key="filter_strategies_input",
        label_visibility="collapsed",
        placeholder="全部策略",
    )

    # 转换回原始值
    reverse_map = {v: k for k, v in strategy_names.items()}
    selected = [reverse_map.get(s, s) for s in selected_display]

    if selected != current_strategies:
        FilterContext.set('strategies', selected)
        if on_change:
            on_change()


def _render_grades_filter(
    available_grades: List[str],
    on_change: Optional[Callable]
) -> None:
    """渲染等级筛选"""
    st.markdown(f"<div class='filter-label'>🏆 等级</div>", unsafe_allow_html=True)

    current_grades = FilterContext.get('grades') or []

    selected = st.multiselect(
        "选择等级",
        options=available_grades,
        default=current_grades,
        key="filter_grades_input",
        label_visibility="collapsed",
        placeholder="全部等级",
    )

    if selected != current_grades:
        FilterContext.set('grades', selected)
        if on_change:
            on_change()


# 快捷筛选按钮组件
def render_quick_filters(on_change: Optional[Callable] = None) -> None:
    """
    渲染快捷筛选按钮

    提供常用筛选条件的一键设置
    """
    st.markdown(f"""
    <div style="
        color: {COLORS['text_muted']};
        font-size: 0.75rem;
        margin-bottom: 0.5rem;
    ">快捷筛选</div>
    """, unsafe_allow_html=True)

    cols = st.columns(6)

    with cols[0]:
        if st.button("📅 本月", key="quick_this_month", use_container_width=True):
            today = date.today()
            first_day = date(today.year, today.month, 1)
            FilterContext.set('date_start', first_day)
            FilterContext.set('date_end', today)
            if on_change:
                on_change()
            st.rerun()

    with cols[1]:
        if st.button("📅 近30天", key="quick_30days", use_container_width=True):
            today = date.today()
            FilterContext.set('date_start', today - timedelta(days=30))
            FilterContext.set('date_end', today)
            if on_change:
                on_change()
            st.rerun()

    with cols[2]:
        if st.button("💰 盈利", key="quick_profit", use_container_width=True):
            FilterContext.set('pnl_type', 'profit')
            if on_change:
                on_change()
            st.rerun()

    with cols[3]:
        if st.button("📉 亏损", key="quick_loss", use_container_width=True):
            FilterContext.set('pnl_type', 'loss')
            if on_change:
                on_change()
            st.rerun()

    with cols[4]:
        if st.button("⭐ 高分", key="quick_high_score", use_container_width=True):
            FilterContext.set('score_min', 70)
            FilterContext.set('score_max', 100)
            if on_change:
                on_change()
            st.rerun()

    with cols[5]:
        if st.button("⚠️ 低分", key="quick_low_score", use_container_width=True):
            FilterContext.set('score_min', 0)
            FilterContext.set('score_max', 50)
            if on_change:
                on_change()
            st.rerun()
