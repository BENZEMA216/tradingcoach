#!/usr/bin/env python3
"""
Trade Explorer - 交易浏览器
一站式交易列表，支持全局筛选、多视图、快速定位

核心功能:
- 统一筛选栏 (日期/股票/盈亏/评分/策略)
- 可展开交易表格，显示详细信息
- 多种视图模式 (时间/股票/策略/等级)
- 快捷筛选按钮
- 导出功能
- 点击进入深度分析
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 页面配置
st.set_page_config(
    page_title="交易浏览 - Trading Coach",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入样式
from visualization.styles import inject_global_css, COLORS, FONTS
inject_global_css()

# 导入组件
from visualization.components.filters import FilterContext, render_filter_bar, render_quick_filters
from visualization.components.core import (
    render_trade_table,
    render_kpi_cards,
    inject_table_css,
    STRATEGY_NAMES,
)
from visualization.utils.data_loader import get_data_loader


def main():
    """主函数"""
    try:
        loader = get_data_loader()
    except Exception as e:
        st.error(f"无法连接数据库: {e}")
        return

    # ================================================================
    # Header
    # ================================================================
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    ">
        <div>
            <div style="
                font-size: 1.75rem;
                font-weight: 700;
                font-family: {FONTS['heading']};
                color: {COLORS['text_primary']};
            ">📋 交易浏览</div>
            <div style="
                color: {COLORS['text_secondary']};
                font-size: 0.85rem;
            ">筛选、浏览、分析所有交易记录</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ================================================================
    # 获取基础数据
    # ================================================================
    all_symbols = loader.get_all_symbols()
    all_strategies = loader.get_all_strategies()
    all_grades = loader.get_all_grades()

    # ================================================================
    # 快捷筛选
    # ================================================================
    render_quick_filters()

    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    # ================================================================
    # 统一筛选栏
    # ================================================================
    with st.container():
        render_filter_bar(
            available_symbols=all_symbols,
            available_strategies=all_strategies,
            available_grades=all_grades,
            show_date_range=True,
            show_symbols=True,
            show_pnl_type=True,
            show_score_range=True,
            show_strategies=True,
            show_grades=True,
            compact=False,
        )

    # ================================================================
    # 加载和筛选数据
    # ================================================================
    df = loader.get_positions_with_scores()

    if df is None or df.empty:
        st.warning("暂无交易数据")
        return

    # 应用全局筛选
    filtered_df = FilterContext.apply_to_dataframe(df)

    # ================================================================
    # 统计汇总卡片
    # ================================================================
    if not filtered_df.empty:
        total_pnl = filtered_df['net_pnl'].sum()
        win_count = (filtered_df['net_pnl'] > 0).sum()
        win_rate = win_count / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
        avg_score = filtered_df['overall_score'].mean() if 'overall_score' in filtered_df.columns else 0
        trade_count = len(filtered_df)

        # 简化的KPI展示
        cols = st.columns(4)

        with cols[0]:
            pnl_color = COLORS['profit'] if total_pnl >= 0 else COLORS['loss']
            pnl_sign = "+" if total_pnl >= 0 else ""
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_secondary']};
                padding: 1rem;
                border-radius: 8px;
                border-left: 3px solid {pnl_color};
            ">
                <div style="color: {COLORS['text_muted']}; font-size: 0.75rem; text-transform: uppercase;">总盈亏</div>
                <div style="color: {pnl_color}; font-size: 1.5rem; font-weight: 700; font-family: {FONTS['mono']};">
                    {pnl_sign}${abs(total_pnl):,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_secondary']};
                padding: 1rem;
                border-radius: 8px;
                border-left: 3px solid {COLORS['accent_cyan']};
            ">
                <div style="color: {COLORS['text_muted']}; font-size: 0.75rem; text-transform: uppercase;">胜率</div>
                <div style="color: {COLORS['text_primary']}; font-size: 1.5rem; font-weight: 700; font-family: {FONTS['mono']};">
                    {win_rate:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_secondary']};
                padding: 1rem;
                border-radius: 8px;
                border-left: 3px solid {COLORS['accent_purple']};
            ">
                <div style="color: {COLORS['text_muted']}; font-size: 0.75rem; text-transform: uppercase;">平均评分</div>
                <div style="color: {COLORS['text_primary']}; font-size: 1.5rem; font-weight: 700; font-family: {FONTS['mono']};">
                    {avg_score:.1f}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with cols[3]:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_secondary']};
                padding: 1rem;
                border-radius: 8px;
                border-left: 3px solid {COLORS['text_secondary']};
            ">
                <div style="color: {COLORS['text_muted']}; font-size: 0.75rem; text-transform: uppercase;">交易数量</div>
                <div style="color: {COLORS['text_primary']}; font-size: 1.5rem; font-weight: 700; font-family: {FONTS['mono']};">
                    {trade_count}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # ================================================================
    # 视图模式切换
    # ================================================================
    col_view, col_sort, col_export = st.columns([3, 2, 1])

    with col_view:
        view_mode = st.radio(
            "视图模式",
            ["按时间", "按股票", "按策略", "按等级"],
            horizontal=True,
            label_visibility="collapsed",
        )

    with col_sort:
        sort_by = st.selectbox(
            "排序方式",
            ["时间 (最新)", "时间 (最早)", "盈亏 (高→低)", "盈亏 (低→高)", "评分 (高→低)"],
            label_visibility="collapsed",
        )

    with col_export:
        if st.button("📥 导出", use_container_width=True):
            csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="下载 CSV",
                data=csv_data,
                file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    # ================================================================
    # 应用排序
    # ================================================================
    sort_column = 'close_date' if 'close_date' in filtered_df.columns else 'close_time'

    if sort_by == "时间 (最新)":
        sorted_df = filtered_df.sort_values(sort_column, ascending=False)
    elif sort_by == "时间 (最早)":
        sorted_df = filtered_df.sort_values(sort_column, ascending=True)
    elif sort_by == "盈亏 (高→低)":
        sorted_df = filtered_df.sort_values('net_pnl', ascending=False)
    elif sort_by == "盈亏 (低→高)":
        sorted_df = filtered_df.sort_values('net_pnl', ascending=True)
    elif sort_by == "评分 (高→低)":
        sorted_df = filtered_df.sort_values('overall_score', ascending=False, na_position='last')
    else:
        sorted_df = filtered_df

    # ================================================================
    # 渲染表格
    # ================================================================
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    # 初始化分页状态
    if 'table_current_page' not in st.session_state:
        st.session_state['table_current_page'] = 1

    if view_mode == "按时间":
        # 时间视图 - 直接显示表格
        selected_id = render_trade_table(
            sorted_df,
            show_strategy=True,
            show_score=True,
            show_grade=True,
            show_expand=True,
            page_size=20,
            current_page=st.session_state.get('table_current_page', 1),
        )

        if selected_id:
            st.session_state['selected_position_id'] = selected_id
            st.switch_page("pages/2_🔍_持仓分析.py")

    elif view_mode == "按股票":
        # 按股票分组
        symbols = sorted(sorted_df['symbol'].unique())

        for symbol in symbols:
            symbol_df = sorted_df[sorted_df['symbol'] == symbol]
            symbol_pnl = symbol_df['net_pnl'].sum()
            symbol_count = len(symbol_df)
            pnl_color = COLORS['profit'] if symbol_pnl >= 0 else COLORS['loss']
            pnl_sign = "+" if symbol_pnl >= 0 else ""

            with st.expander(
                f"📊 {symbol} ({symbol_count}笔) | {pnl_sign}${abs(symbol_pnl):,.2f}",
                expanded=False
            ):
                render_trade_table(
                    symbol_df,
                    show_strategy=True,
                    show_score=True,
                    show_expand=False,
                    page_size=50,
                    current_page=1,
                )

    elif view_mode == "按策略":
        # 按策略分组
        strategies = sorted_df['strategy_type'].unique() if 'strategy_type' in sorted_df.columns else []

        for strategy in strategies:
            if pd.isna(strategy):
                continue

            strategy_df = sorted_df[sorted_df['strategy_type'] == strategy]
            strategy_pnl = strategy_df['net_pnl'].sum()
            strategy_count = len(strategy_df)
            strategy_name = STRATEGY_NAMES.get(strategy, strategy)
            pnl_color = COLORS['profit'] if strategy_pnl >= 0 else COLORS['loss']
            pnl_sign = "+" if strategy_pnl >= 0 else ""

            win_count = (strategy_df['net_pnl'] > 0).sum()
            win_rate = win_count / strategy_count * 100 if strategy_count > 0 else 0

            with st.expander(
                f"🎯 {strategy_name} ({strategy_count}笔) | 胜率 {win_rate:.0f}% | {pnl_sign}${abs(strategy_pnl):,.2f}",
                expanded=False
            ):
                render_trade_table(
                    strategy_df,
                    show_strategy=False,
                    show_score=True,
                    show_expand=False,
                    page_size=50,
                    current_page=1,
                )

    elif view_mode == "按等级":
        # 按等级分组
        grade_order = ['A', 'B', 'C', 'D', 'F']
        grade_col = 'score_grade' if 'score_grade' in sorted_df.columns else 'grade'

        for grade in grade_order:
            grade_df = sorted_df[sorted_df[grade_col].str.startswith(grade, na=False)]

            if len(grade_df) == 0:
                continue

            grade_pnl = grade_df['net_pnl'].sum()
            grade_count = len(grade_df)
            pnl_color = COLORS['profit'] if grade_pnl >= 0 else COLORS['loss']
            pnl_sign = "+" if grade_pnl >= 0 else ""

            win_count = (grade_df['net_pnl'] > 0).sum()
            win_rate = win_count / grade_count * 100 if grade_count > 0 else 0

            grade_emoji = {'A': '🏆', 'B': '👍', 'C': '👌', 'D': '⚠️', 'F': '❌'}.get(grade, '📊')

            with st.expander(
                f"{grade_emoji} {grade}级 ({grade_count}笔) | 胜率 {win_rate:.0f}% | {pnl_sign}${abs(grade_pnl):,.2f}",
                expanded=False
            ):
                render_trade_table(
                    grade_df,
                    show_strategy=True,
                    show_score=True,
                    show_expand=False,
                    page_size=50,
                    current_page=1,
                )

    # ================================================================
    # Footer
    # ================================================================
    st.markdown(f"""
    <div style="
        text-align: center;
        color: {COLORS['text_muted']};
        padding: 2rem 0 1rem 0;
        font-size: 0.8rem;
        border-top: 1px solid {COLORS['border']};
        margin-top: 2rem;
    ">
        点击交易行的 → 按钮进入深度分析
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
