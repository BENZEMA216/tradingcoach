#!/usr/bin/env python3
"""
Trading Coach Dashboard
交易教练性能仪表盘 - 一眼看懂盈亏

核心功能:
- KPI 指标展示 (总盈亏/胜率/平均评分/交易数)
- 权益曲线图表
- 最近交易列表
- 待复盘交易列表
- 策略分布饼图
- 本月日历热力图预览
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 页面配置
st.set_page_config(
    page_title="Trading Coach",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入样式
from visualization.styles import inject_global_css, COLORS, FONTS
inject_global_css()

# 导入组件
from visualization.components.core.metric_card import render_kpi_cards, METRIC_CARD_CSS
from visualization.components.charts.equity_curve import create_equity_curve
from visualization.components.charts.calendar_heatmap import create_month_calendar
from visualization.utils.data_loader import get_data_loader

# 注入额外CSS
st.markdown(METRIC_CARD_CSS, unsafe_allow_html=True)


def render_trade_list(df, title: str, icon: str, show_reason: bool = False):
    """渲染交易列表"""
    if df is None or df.empty:
        st.info(f"暂无{title}数据")
        return

    title_style = f"color: {COLORS['text_primary']}; font-size: 1rem; font-weight: 600; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;"
    st.markdown(f'<div style="{title_style}"><span>{icon}</span><span>{title}</span></div>', unsafe_allow_html=True)

    for _, row in df.iterrows():
        pnl = row['net_pnl']
        is_profit = pnl >= 0
        pnl_color = COLORS['profit'] if is_profit else COLORS['loss']
        pnl_icon = "▲" if is_profit else "▼"
        pnl_sign = "+" if is_profit else ""

        grade = row.get('grade', '-') or '-'
        grade_color = {
            'A': COLORS['grade_a'], 'B': COLORS['grade_b'],
            'C': COLORS['grade_c'], 'D': COLORS['grade_d'], 'F': COLORS['grade_f']
        }.get(grade[0] if grade else 'C', COLORS['text_muted'])

        date_str = row['close_date'].strftime('%m/%d') if row.get('close_date') else '-'

        reason_html = ""
        if show_reason and 'reason' in row:
            reason_style = f"font-size: 0.7rem; padding: 0.125rem 0.375rem; background: {COLORS['loss']}20; color: {COLORS['loss']}; border-radius: 4px;"
            reason_html = f'<span style="{reason_style}">{row["reason"]}</span>'

        # 定义所有样式 (单行格式)
        row_style = f"display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.75rem; background: {COLORS['bg_tertiary']}; border-radius: 8px; margin-bottom: 0.5rem;"
        left_container_style = "display: flex; align-items: center; gap: 0.75rem;"
        symbol_style = f"font-family: {FONTS['mono']}; font-weight: 600; color: {COLORS['text_primary']}; min-width: 60px;"
        date_style = f"color: {COLORS['text_muted']}; font-size: 0.8rem;"
        right_container_style = "display: flex; align-items: center; gap: 0.75rem;"
        pnl_style = f"font-family: {FONTS['mono']}; font-weight: 600; color: {pnl_color}; font-size: 0.9rem;"
        grade_style = f"display: inline-flex; align-items: center; justify-content: center; width: 1.5rem; height: 1.5rem; background: {grade_color}20; color: {grade_color}; border-radius: 4px; font-size: 0.75rem; font-weight: 700;"

        st.markdown(f'''<div style="{row_style}"><div style="{left_container_style}"><span style="{symbol_style}">{row['symbol']}</span><span style="{date_style}">{date_str}</span>{reason_html}</div><div style="{right_container_style}"><span style="{pnl_style}">{pnl_icon} {pnl_sign}${abs(pnl):,.0f}</span><span style="{grade_style}">{grade}</span></div></div>''', unsafe_allow_html=True)


def render_strategy_donut(df):
    """渲染策略分布饼图"""
    if df is None or df.empty:
        st.info("暂无策略数据")
        return

    # 颜色映射
    colors = {
        'trend': COLORS['strategy_trend'],
        'mean_reversion': COLORS['strategy_reversion'],
        'breakout': COLORS['strategy_breakout'],
        'range': COLORS['strategy_range'],
        'momentum': COLORS['strategy_momentum'],
        'unknown': COLORS['neutral'],
    }

    fig = go.Figure(data=[
        go.Pie(
            labels=df['strategy_name'],
            values=df['count'],
            hole=0.6,
            marker=dict(
                colors=[colors.get(s, COLORS['neutral']) for s in df['strategy']],
                line=dict(color=COLORS['bg_primary'], width=2)
            ),
            textinfo='percent',
            textfont=dict(size=11, color=COLORS['text_primary']),
            hovertemplate=(
                '<b>%{label}</b><br>'
                '交易数: %{value}<br>'
                '占比: %{percent}<br>'
                '<extra></extra>'
            ),
        )
    ])

    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_primary'],
        font=dict(color=COLORS['text_secondary']),
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='left',
            x=1.05,
            font=dict(size=10),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


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
    header_container_style = "display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;"
    title_style = f"font-size: 2rem; font-weight: 700; font-family: {FONTS['heading']}; color: {COLORS['text_primary']};"
    subtitle_style = f"color: {COLORS['text_secondary']}; font-size: 0.9rem;"
    st.markdown(f'<div style="{header_container_style}"><div><div style="{title_style}">Trading Coach</div><div style="{subtitle_style}">交易复盘与绩效分析</div></div></div>', unsafe_allow_html=True)

    # ================================================================
    # KPI Cards
    # ================================================================
    kpis = loader.get_dashboard_kpis()
    prev_kpis = loader.get_dashboard_kpis(days=60)  # 用于计算变化

    render_kpi_cards(
        total_pnl=kpis['total_pnl'],
        win_rate=kpis['win_rate'],
        avg_score=kpis['avg_score'],
        trade_count=kpis['trade_count'],
        prev_period_pnl=prev_kpis['total_pnl'] if prev_kpis['trade_count'] > 0 else None,
        prev_period_win_rate=prev_kpis['win_rate'] if prev_kpis['trade_count'] > 0 else None,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ================================================================
    # Equity Curve
    # ================================================================
    section_title_style = f"color: {COLORS['text_primary']}; font-size: 1.125rem; font-weight: 600; margin-bottom: 0.75rem;"
    st.markdown(f'<div style="{section_title_style}">📈 权益曲线</div>', unsafe_allow_html=True)

    # 时间范围选择
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 4])

    time_ranges = {'1M': 30, '3M': 90, '6M': 180, '1Y': 365, 'ALL': None}

    if 'equity_range' not in st.session_state:
        st.session_state.equity_range = 'ALL'

    with col1:
        if st.button("1M", use_container_width=True,
                     type="primary" if st.session_state.equity_range == '1M' else "secondary"):
            st.session_state.equity_range = '1M'
    with col2:
        if st.button("3M", use_container_width=True,
                     type="primary" if st.session_state.equity_range == '3M' else "secondary"):
            st.session_state.equity_range = '3M'
    with col3:
        if st.button("6M", use_container_width=True,
                     type="primary" if st.session_state.equity_range == '6M' else "secondary"):
            st.session_state.equity_range = '6M'
    with col4:
        if st.button("ALL", use_container_width=True,
                     type="primary" if st.session_state.equity_range == 'ALL' else "secondary"):
            st.session_state.equity_range = 'ALL'

    days = time_ranges.get(st.session_state.equity_range)
    equity_data = loader.get_equity_curve_data(days=days)

    if not equity_data.empty:
        fig = create_equity_curve(
            equity_data,
            date_col='close_time',
            pnl_col='net_pnl',
            show_drawdown=False,
            show_trades=True,
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无交易数据")

    st.markdown("<br>", unsafe_allow_html=True)

    # ================================================================
    # Trade Lists (Recent + Needs Review)
    # ================================================================
    col1, col2 = st.columns(2)

    with col1:
        recent_trades = loader.get_recent_trades(limit=5)
        render_trade_list(recent_trades, "最近交易", "🕐")

        if not recent_trades.empty:
            st.markdown(f"""
            <div style="text-align: right; margin-top: 0.5rem;">
                <a href="/交易浏览" style="
                    color: {COLORS['accent_cyan']};
                    font-size: 0.8rem;
                    text-decoration: none;
                ">查看全部 →</a>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        needs_review = loader.get_needs_review_trades(limit=5)
        render_trade_list(needs_review, "待复盘", "⚠️", show_reason=True)

        if not needs_review.empty:
            st.markdown(f"""
            <div style="text-align: right; margin-top: 0.5rem;">
                <a href="/持仓分析" style="
                    color: {COLORS['accent_cyan']};
                    font-size: 0.8rem;
                    text-decoration: none;
                ">开始复盘 →</a>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ================================================================
    # Strategy Distribution + Calendar Preview
    # ================================================================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="
            color: {COLORS['text_primary']};
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        ">📊 策略分布</div>
        """, unsafe_allow_html=True)

        strategy_data = loader.get_strategy_breakdown()
        render_strategy_donut(strategy_data)

    with col2:
        st.markdown(f"""
        <div style="
            color: {COLORS['text_primary']};
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        ">📅 本月盈亏日历</div>
        """, unsafe_allow_html=True)

        now = datetime.now()
        daily_pnl = loader.get_daily_pnl(year=now.year, month=now.month)

        if not daily_pnl.empty:
            fig = create_month_calendar(
                daily_pnl,
                year=now.year,
                month=now.month,
                date_col='date',
                pnl_col='pnl',
                height=200,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("本月暂无交易数据")

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
        Trading Coach v2.0 · 使用左侧导航访问更多功能
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
