"""
DataTable - 可展开交易表格组件

提供交易列表的展示，支持:
- 行内展开显示详细信息
- 迷你权益曲线预览
- 快速操作按钮
- 响应式布局
"""

import streamlit as st
import pandas as pd
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from visualization.styles import COLORS, FONTS


# 策略名称映射
STRATEGY_NAMES = {
    'trend': '趋势跟踪',
    'mean_reversion': '均值回归',
    'breakout': '突破交易',
    'range': '区间交易',
    'momentum': '动量交易',
    'unknown': '未分类',
}

# 策略颜色映射
STRATEGY_COLORS = {
    'trend': COLORS.get('strategy_trend', '#4CAF50'),
    'mean_reversion': COLORS.get('strategy_reversion', '#2196F3'),
    'breakout': COLORS.get('strategy_breakout', '#FF9800'),
    'range': COLORS.get('strategy_range', '#9C27B0'),
    'momentum': COLORS.get('strategy_momentum', '#E91E63'),
    'unknown': COLORS.get('neutral', '#9E9E9E'),
}

# 等级颜色映射
GRADE_COLORS = {
    'A': COLORS.get('grade_a', '#00FF88'),
    'B': COLORS.get('grade_b', '#4CAF50'),
    'C': COLORS.get('grade_c', '#FFC107'),
    'D': COLORS.get('grade_d', '#FF9800'),
    'F': COLORS.get('grade_f', '#FF3B5C'),
}


def inject_table_css() -> None:
    """注入表格样式"""
    st.markdown(f"""
    <style>
    .trade-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 0.5rem;
    }}

    .trade-row {{
        background: {COLORS['bg_secondary']};
        border-radius: 8px;
        transition: all 0.2s ease;
        cursor: pointer;
    }}

    .trade-row:hover {{
        background: {COLORS['bg_tertiary']};
        transform: translateX(4px);
    }}

    .trade-row td {{
        padding: 0.75rem 1rem;
        vertical-align: middle;
    }}

    .trade-row td:first-child {{
        border-radius: 8px 0 0 8px;
    }}

    .trade-row td:last-child {{
        border-radius: 0 8px 8px 0;
    }}

    .trade-symbol {{
        font-family: {FONTS['mono']};
        font-weight: 600;
        font-size: 1rem;
        color: {COLORS['text_primary']};
    }}

    .trade-date {{
        color: {COLORS['text_muted']};
        font-size: 0.8rem;
    }}

    .trade-pnl {{
        font-family: {FONTS['mono']};
        font-weight: 600;
        font-size: 0.95rem;
    }}

    .trade-pnl.profit {{
        color: {COLORS['profit']};
    }}

    .trade-pnl.loss {{
        color: {COLORS['loss']};
    }}

    .trade-score {{
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }}

    .trade-grade {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.75rem;
        height: 1.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
    }}

    .trade-strategy {{
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
    }}

    .trade-expand-icon {{
        color: {COLORS['text_muted']};
        transition: transform 0.2s;
    }}

    .trade-expanded {{
        background: {COLORS['bg_tertiary']};
        border-radius: 0 0 8px 8px;
        margin-top: -0.5rem;
        padding: 1rem;
        border-top: 1px solid {COLORS['border']};
    }}

    .trade-detail-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
    }}

    .trade-detail-item {{
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }}

    .trade-detail-label {{
        color: {COLORS['text_muted']};
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .trade-detail-value {{
        color: {COLORS['text_primary']};
        font-family: {FONTS['mono']};
        font-size: 0.9rem;
    }}

    .action-btn {{
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        border: none;
        cursor: pointer;
        transition: all 0.2s;
    }}

    .action-btn-primary {{
        background: {COLORS['accent_cyan']}20;
        color: {COLORS['accent_cyan']};
    }}

    .action-btn-primary:hover {{
        background: {COLORS['accent_cyan']}40;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_trade_table(
    df: pd.DataFrame,
    on_select: Optional[Callable[[int], None]] = None,
    show_strategy: bool = True,
    show_score: bool = True,
    show_grade: bool = True,
    show_expand: bool = True,
    page_size: int = 20,
    current_page: int = 1,
) -> Optional[int]:
    """
    渲染交易表格

    Args:
        df: 交易数据 DataFrame
        on_select: 点击行时的回调函数，参数为 position_id
        show_strategy: 是否显示策略列
        show_score: 是否显示评分
        show_grade: 是否显示等级
        show_expand: 是否允许展开详情
        page_size: 每页显示数量
        current_page: 当前页码

    Returns:
        选中的 position_id (如果有点击)
    """
    inject_table_css()

    if df is None or df.empty:
        st.info("暂无交易数据")
        return None

    # 分页处理
    total_rows = len(df)
    total_pages = (total_rows + page_size - 1) // page_size
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)

    page_df = df.iloc[start_idx:end_idx]

    # 表头
    _render_table_header(show_strategy, show_score)

    # 表格行
    selected_id = None
    for idx, row in page_df.iterrows():
        clicked_id = _render_trade_row(
            row,
            idx=idx,
            show_strategy=show_strategy,
            show_score=show_score,
            show_grade=show_grade,
            show_expand=show_expand,
        )
        if clicked_id is not None:
            selected_id = clicked_id

    # 分页控件
    if total_pages > 1:
        _render_pagination(current_page, total_pages, total_rows)

    return selected_id


def _render_table_header(show_strategy: bool, show_score: bool) -> None:
    """渲染表头"""
    cols = st.columns([1.5, 1, 1.5, 1, 1, 0.5] if show_strategy else [2, 1.5, 1.5, 1, 0.5])

    headers = ["股票", "日期", "盈亏"]
    if show_strategy:
        headers.append("策略")
    if show_score:
        headers.append("评分")
    headers.append("")  # 展开按钮列

    for col, header in zip(cols, headers):
        with col:
            st.markdown(f"""
            <div style="
                color: {COLORS['text_muted']};
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 0.5rem 0;
                border-bottom: 1px solid {COLORS['border']};
            ">{header}</div>
            """, unsafe_allow_html=True)


def _render_trade_row(
    row: pd.Series,
    idx: int,
    show_strategy: bool,
    show_score: bool,
    show_grade: bool,
    show_expand: bool,
) -> Optional[int]:
    """
    渲染单行交易数据

    Returns:
        如果点击了分析按钮，返回 position_id
    """
    position_id = row.get('id', idx)
    symbol = row.get('symbol', '-')
    close_date = row.get('close_date') or row.get('close_time')
    net_pnl = row.get('net_pnl', 0)
    strategy = row.get('strategy_type', 'unknown')
    score = row.get('overall_score', 0)
    grade = row.get('score_grade', row.get('grade', '-'))

    # 格式化日期
    if close_date:
        if isinstance(close_date, datetime):
            date_str = close_date.strftime('%Y-%m-%d')
        else:
            date_str = str(close_date)[:10]
    else:
        date_str = '-'

    # 盈亏样式
    is_profit = net_pnl >= 0
    pnl_class = "profit" if is_profit else "loss"
    pnl_sign = "+" if is_profit else ""
    pnl_color = COLORS['profit'] if is_profit else COLORS['loss']

    # 等级颜色
    grade_char = grade[0] if grade else 'C'
    grade_color = GRADE_COLORS.get(grade_char, COLORS['text_muted'])

    # 策略颜色
    strategy_color = STRATEGY_COLORS.get(strategy, COLORS['neutral'])
    strategy_name = STRATEGY_NAMES.get(strategy, strategy)

    # 列配置
    if show_strategy:
        cols = st.columns([1.5, 1, 1.5, 1, 1, 0.5])
    else:
        cols = st.columns([2, 1.5, 1.5, 1, 0.5])

    col_idx = 0

    # 股票
    with cols[col_idx]:
        st.markdown(f"""
        <div class="trade-symbol">{symbol}</div>
        """, unsafe_allow_html=True)
    col_idx += 1

    # 日期
    with cols[col_idx]:
        st.markdown(f"""
        <div class="trade-date">{date_str}</div>
        """, unsafe_allow_html=True)
    col_idx += 1

    # 盈亏
    with cols[col_idx]:
        st.markdown(f"""
        <div class="trade-pnl {pnl_class}">
            {pnl_sign}${abs(net_pnl):,.2f}
        </div>
        """, unsafe_allow_html=True)
    col_idx += 1

    # 策略
    if show_strategy:
        with cols[col_idx]:
            st.markdown(f"""
            <span class="trade-strategy" style="
                background: {strategy_color}20;
                color: {strategy_color};
            ">{strategy_name}</span>
            """, unsafe_allow_html=True)
        col_idx += 1

    # 评分/等级
    if show_score:
        with cols[col_idx]:
            st.markdown(f"""
            <div class="trade-score">
                <span style="
                    color: {COLORS['text_secondary']};
                    font-family: {FONTS['mono']};
                    font-size: 0.85rem;
                ">{score:.0f}</span>
                <span class="trade-grade" style="
                    background: {grade_color}20;
                    color: {grade_color};
                ">{grade_char}</span>
            </div>
            """, unsafe_allow_html=True)
        col_idx += 1

    # 操作按钮
    clicked = None
    with cols[col_idx]:
        if st.button("→", key=f"analyze_{position_id}", help="深入分析"):
            clicked = position_id

    # 展开详情区域（使用 expander）
    if show_expand:
        expand_key = f"expand_{position_id}"
        with st.expander("", expanded=False):
            _render_expanded_details(row)

    return clicked


def _render_expanded_details(row: pd.Series) -> None:
    """渲染展开的详情区域"""
    cols = st.columns(4)

    # 入场信息
    with cols[0]:
        entry_price = row.get('entry_price', row.get('avg_entry_price', 0))
        entry_date = row.get('open_date') or row.get('open_time')
        entry_date_str = entry_date.strftime('%m/%d %H:%M') if entry_date else '-'

        st.markdown(f"""
        <div class="trade-detail-item">
            <div class="trade-detail-label">入场</div>
            <div class="trade-detail-value">${entry_price:,.2f}</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.75rem;">{entry_date_str}</div>
        </div>
        """, unsafe_allow_html=True)

    # 出场信息
    with cols[1]:
        exit_price = row.get('exit_price', row.get('avg_exit_price', 0))
        exit_date = row.get('close_date') or row.get('close_time')
        exit_date_str = exit_date.strftime('%m/%d %H:%M') if exit_date else '-'

        st.markdown(f"""
        <div class="trade-detail-item">
            <div class="trade-detail-label">出场</div>
            <div class="trade-detail-value">${exit_price:,.2f}</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.75rem;">{exit_date_str}</div>
        </div>
        """, unsafe_allow_html=True)

    # 持仓天数
    with cols[2]:
        holding_days = row.get('holding_days', 0)
        quantity = row.get('quantity', row.get('total_quantity', 0))

        st.markdown(f"""
        <div class="trade-detail-item">
            <div class="trade-detail-label">持仓</div>
            <div class="trade-detail-value">{holding_days} 天</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.75rem;">{quantity:,.0f} 股</div>
        </div>
        """, unsafe_allow_html=True)

    # 收益率
    with cols[3]:
        pnl_pct = row.get('pnl_pct', 0) * 100 if row.get('pnl_pct') else 0
        if pnl_pct == 0 and row.get('entry_price', 0) > 0:
            pnl_pct = (row.get('net_pnl', 0) / (row.get('entry_price', 1) * row.get('quantity', 1))) * 100

        pnl_color = COLORS['profit'] if pnl_pct >= 0 else COLORS['loss']
        pnl_sign = "+" if pnl_pct >= 0 else ""

        st.markdown(f"""
        <div class="trade-detail-item">
            <div class="trade-detail-label">收益率</div>
            <div class="trade-detail-value" style="color: {pnl_color};">
                {pnl_sign}{pnl_pct:.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 评分详情（如果有）
    if any(row.get(f'{dim}_score') for dim in ['entry', 'exit', 'timing', 'risk']):
        st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)

        score_cols = st.columns(4)
        dimensions = [
            ('entry_score', '入场'),
            ('exit_score', '出场'),
            ('timing_score', '时机'),
            ('risk_score', '风控'),
        ]

        for col, (key, label) in zip(score_cols, dimensions):
            score = row.get(key, 0) or 0
            with col:
                # 分数对应的颜色
                if score >= 80:
                    score_color = COLORS['profit']
                elif score >= 60:
                    score_color = COLORS.get('warning', '#FFC107')
                else:
                    score_color = COLORS['loss']

                st.markdown(f"""
                <div style="
                    background: {COLORS['bg_secondary']};
                    padding: 0.5rem;
                    border-radius: 6px;
                    text-align: center;
                ">
                    <div style="
                        color: {COLORS['text_muted']};
                        font-size: 0.7rem;
                        margin-bottom: 0.25rem;
                    ">{label}</div>
                    <div style="
                        color: {score_color};
                        font-family: {FONTS['mono']};
                        font-weight: 600;
                    ">{score:.0f}</div>
                </div>
                """, unsafe_allow_html=True)


def _render_pagination(current_page: int, total_pages: int, total_rows: int) -> None:
    """渲染分页控件"""
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    cols = st.columns([2, 1, 1, 1, 2])

    # 统计信息
    with cols[0]:
        st.markdown(f"""
        <div style="
            color: {COLORS['text_muted']};
            font-size: 0.8rem;
            padding-top: 0.5rem;
        ">共 {total_rows} 条记录</div>
        """, unsafe_allow_html=True)

    # 上一页
    with cols[1]:
        if current_page > 1:
            if st.button("← 上一页", key="prev_page"):
                st.session_state['table_current_page'] = current_page - 1
                st.rerun()

    # 页码显示
    with cols[2]:
        st.markdown(f"""
        <div style="
            color: {COLORS['text_primary']};
            font-size: 0.9rem;
            text-align: center;
            padding-top: 0.5rem;
        ">{current_page} / {total_pages}</div>
        """, unsafe_allow_html=True)

    # 下一页
    with cols[3]:
        if current_page < total_pages:
            if st.button("下一页 →", key="next_page"):
                st.session_state['table_current_page'] = current_page + 1
                st.rerun()


def render_compact_trade_list(
    df: pd.DataFrame,
    limit: int = 5,
    title: str = "最近交易",
    icon: str = "🕐",
    on_click: Optional[Callable[[int], None]] = None,
) -> None:
    """
    渲染紧凑的交易列表（用于仪表盘等）

    Args:
        df: 交易数据
        limit: 显示条数限制
        title: 列表标题
        icon: 标题图标
        on_click: 点击交易时的回调
    """
    if df is None or df.empty:
        st.info(f"暂无{title}数据")
        return

    # 标题
    st.markdown(f"""
    <div style="
        color: {COLORS['text_primary']};
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    ">
        <span>{icon}</span>
        <span>{title}</span>
    </div>
    """, unsafe_allow_html=True)

    # 列表项
    for idx, row in df.head(limit).iterrows():
        symbol = row.get('symbol', '-')
        net_pnl = row.get('net_pnl', 0)
        close_date = row.get('close_date') or row.get('close_time')
        grade = row.get('grade', row.get('score_grade', '-'))

        # 格式化
        is_profit = net_pnl >= 0
        pnl_color = COLORS['profit'] if is_profit else COLORS['loss']
        pnl_sign = "+" if is_profit else ""
        pnl_icon = "▲" if is_profit else "▼"

        date_str = close_date.strftime('%m/%d') if close_date else '-'

        grade_char = grade[0] if grade else '-'
        grade_color = GRADE_COLORS.get(grade_char, COLORS['text_muted'])

        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 0.75rem;
            background: {COLORS['bg_tertiary']};
            border-radius: 8px;
            margin-bottom: 0.5rem;
            transition: background 0.2s;
        ">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="
                    font-family: {FONTS['mono']};
                    font-weight: 600;
                    color: {COLORS['text_primary']};
                    min-width: 60px;
                ">{symbol}</span>
                <span style="
                    color: {COLORS['text_muted']};
                    font-size: 0.8rem;
                ">{date_str}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="
                    font-family: {FONTS['mono']};
                    font-weight: 600;
                    color: {pnl_color};
                    font-size: 0.9rem;
                ">{pnl_icon} {pnl_sign}${abs(net_pnl):,.0f}</span>
                <span style="
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 1.5rem;
                    height: 1.5rem;
                    background: {grade_color}20;
                    color: {grade_color};
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 700;
                ">{grade_char}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
