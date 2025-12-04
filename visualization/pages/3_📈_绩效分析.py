#!/usr/bin/env python3
"""
Performance Analytics - 绩效分析
发现交易模式和改进方向

核心功能:
- 日历热力图 (每日盈亏颜色网格)
- 策略分析 (按策略对比胜率、盈亏、评分)
- 模式发现 (自动洞察交易规律)
- 时间分析 (按月/周/日的表现趋势)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path
import calendar

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 页面配置
st.set_page_config(
    page_title="绩效分析 - Trading Coach",
    page_icon="📈",
    layout="wide"
)

# 导入样式系统
from visualization.styles import inject_global_css, COLORS, FONTS
inject_global_css()

# 导入组件
from visualization.components.charts import create_calendar_heatmap
from visualization.components.core import STRATEGY_NAMES, GRADE_COLORS
from visualization.utils.data_loader import get_data_loader


def render_yearly_calendar(df: pd.DataFrame, year: int):
    """渲染年度日历热力图"""
    if df is None or df.empty:
        st.info("暂无交易数据")
        return

    # 按月份分组显示
    months = list(range(1, 13))

    # 三行四列布局
    for row in range(3):
        cols = st.columns(4)
        for col_idx, month in enumerate(months[row*4:(row+1)*4]):
            with cols[col_idx]:
                month_name = calendar.month_abbr[month]

                # 获取该月数据
                month_df = df[df['date'].dt.month == month]

                if month_df.empty:
                    st.markdown(f"""
                    <div style="text-align: center; color: {COLORS['text_muted']}; font-size: 0.8rem; padding: 1rem;">
                        {month_name}<br>无数据
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    total_pnl = month_df['pnl'].sum()
                    pnl_color = COLORS['profit'] if total_pnl >= 0 else COLORS['loss']
                    pnl_sign = "+" if total_pnl >= 0 else ""

                    st.markdown(f"""
                    <div style="
                        background: {COLORS['bg_secondary']};
                        border-radius: 8px;
                        padding: 0.5rem;
                        text-align: center;
                    ">
                        <div style="color: {COLORS['text_secondary']}; font-weight: 600; font-size: 0.85rem;">{month_name}</div>
                        <div style="color: {pnl_color}; font-family: {FONTS['mono']}; font-size: 1rem; font-weight: 600;">
                            {pnl_sign}${abs(total_pnl):,.0f}
                        </div>
                        <div style="color: {COLORS['text_muted']}; font-size: 0.7rem;">{len(month_df)} 交易日</div>
                    </div>
                    """, unsafe_allow_html=True)


def render_strategy_analysis(df: pd.DataFrame):
    """渲染策略分析"""
    if df is None or df.empty or 'strategy_type' not in df.columns:
        st.info("暂无策略数据")
        return

    # 按策略分组统计
    strategy_stats = df.groupby('strategy_type').agg({
        'net_pnl': ['sum', 'mean', 'count'],
        'overall_score': 'mean',
    }).round(2)

    strategy_stats.columns = ['total_pnl', 'avg_pnl', 'trade_count', 'avg_score']
    strategy_stats['win_count'] = df.groupby('strategy_type').apply(lambda x: (x['net_pnl'] > 0).sum())
    strategy_stats['win_rate'] = (strategy_stats['win_count'] / strategy_stats['trade_count'] * 100).round(1)
    strategy_stats = strategy_stats.reset_index()
    strategy_stats['strategy_name'] = strategy_stats['strategy_type'].map(STRATEGY_NAMES)

    # 策略颜色
    strategy_colors = {
        'trend': COLORS.get('strategy_trend', '#4CAF50'),
        'mean_reversion': COLORS.get('strategy_reversion', '#2196F3'),
        'breakout': COLORS.get('strategy_breakout', '#FF9800'),
        'range': COLORS.get('strategy_range', '#9C27B0'),
        'momentum': COLORS.get('strategy_momentum', '#E91E63'),
        'unknown': COLORS.get('neutral', '#9E9E9E'),
    }

    # 创建对比柱状图
    fig = go.Figure()

    # 总盈亏柱状图
    colors = [strategy_colors.get(s, COLORS['neutral']) for s in strategy_stats['strategy_type']]

    fig.add_trace(go.Bar(
        x=strategy_stats['strategy_name'],
        y=strategy_stats['total_pnl'],
        name='总盈亏',
        marker_color=colors,
        text=[f"${v:,.0f}" for v in strategy_stats['total_pnl']],
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary']),
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_secondary'],
        font=dict(color=COLORS['text_secondary']),
        xaxis=dict(
            gridcolor=COLORS['border'],
            tickfont=dict(color=COLORS['text_secondary']),
        ),
        yaxis=dict(
            gridcolor=COLORS['border'],
            tickfont=dict(color=COLORS['text_secondary']),
            tickprefix='$',
        ),
        showlegend=False,
        bargap=0.3,
    )

    st.plotly_chart(fig, use_container_width=True)

    # 策略详细统计表
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    for _, row in strategy_stats.iterrows():
        strategy_color = strategy_colors.get(row['strategy_type'], COLORS['neutral'])
        pnl_color = COLORS['profit'] if row['total_pnl'] >= 0 else COLORS['loss']

        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: {COLORS['bg_secondary']};
            border-left: 3px solid {strategy_color};
            border-radius: 0 8px 8px 0;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
        ">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="color: {strategy_color}; font-weight: 600;">{row['strategy_name']}</span>
                <span style="color: {COLORS['text_muted']}; font-size: 0.8rem;">{int(row['trade_count'])} 笔</span>
            </div>
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <div style="text-align: center;">
                    <div style="color: {COLORS['text_muted']}; font-size: 0.7rem;">胜率</div>
                    <div style="font-family: {FONTS['mono']}; color: {COLORS['text_primary']};">{row['win_rate']:.0f}%</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: {COLORS['text_muted']}; font-size: 0.7rem;">平均评分</div>
                    <div style="font-family: {FONTS['mono']}; color: {COLORS['text_primary']};">{row['avg_score']:.0f}</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: {COLORS['text_muted']}; font-size: 0.7rem;">总盈亏</div>
                    <div style="font-family: {FONTS['mono']}; color: {pnl_color}; font-weight: 600;">${row['total_pnl']:,.0f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_pattern_insights(df: pd.DataFrame):
    """渲染模式发现 (自动洞察)"""
    if df is None or df.empty:
        st.info("暂无足够数据进行模式分析")
        return

    insights = []

    # 1. 持仓天数与胜率关系
    if 'holding_days' in df.columns:
        short_hold = df[df['holding_days'] <= 3]
        long_hold = df[df['holding_days'] > 5]

        if len(short_hold) >= 10 and len(long_hold) >= 10:
            short_win_rate = (short_hold['net_pnl'] > 0).mean() * 100
            long_win_rate = (long_hold['net_pnl'] > 0).mean() * 100

            if abs(short_win_rate - long_win_rate) > 10:
                if short_win_rate > long_win_rate:
                    insights.append({
                        'type': 'success',
                        'title': '短线优势',
                        'content': f'持仓≤3天胜率 {short_win_rate:.0f}%，而>5天胜率仅 {long_win_rate:.0f}%',
                    })
                else:
                    insights.append({
                        'type': 'info',
                        'title': '中长线优势',
                        'content': f'持仓>5天胜率 {long_win_rate:.0f}%，短线(≤3天)胜率 {short_win_rate:.0f}%',
                    })

    # 2. 评分与盈亏关系
    if 'overall_score' in df.columns:
        high_score = df[df['overall_score'] >= 70]
        low_score = df[df['overall_score'] < 50]

        if len(high_score) >= 5 and len(low_score) >= 5:
            high_win_rate = (high_score['net_pnl'] > 0).mean() * 100
            low_win_rate = (low_score['net_pnl'] > 0).mean() * 100

            if high_win_rate > low_win_rate + 15:
                insights.append({
                    'type': 'success',
                    'title': '评分有效',
                    'content': f'高评分(≥70)交易胜率 {high_win_rate:.0f}%，低评分(<50)仅 {low_win_rate:.0f}%',
                })

    # 3. 每周表现
    if 'close_date' in df.columns:
        df_copy = df.copy()
        df_copy['weekday'] = pd.to_datetime(df_copy['close_date']).dt.dayofweek
        weekday_stats = df_copy.groupby('weekday').agg({
            'net_pnl': ['sum', 'count'],
        })
        weekday_stats.columns = ['total_pnl', 'count']
        weekday_stats = weekday_stats[weekday_stats['count'] >= 5]

        if not weekday_stats.empty:
            best_day = weekday_stats['total_pnl'].idxmax()
            worst_day = weekday_stats['total_pnl'].idxmin()
            day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

            if weekday_stats.loc[best_day, 'total_pnl'] > 0 and weekday_stats.loc[worst_day, 'total_pnl'] < 0:
                insights.append({
                    'type': 'info',
                    'title': '周内规律',
                    'content': f'{day_names[best_day]}表现最佳 (+${weekday_stats.loc[best_day, "total_pnl"]:,.0f})，{day_names[worst_day]}表现最差 (${weekday_stats.loc[worst_day, "total_pnl"]:,.0f})',
                })

    # 4. 连续盈亏
    df_sorted = df.sort_values('close_date')
    wins = df_sorted['net_pnl'] > 0
    max_win_streak = 0
    max_loss_streak = 0
    current_streak = 0
    last_win = None

    for is_win in wins:
        if last_win is None or is_win == last_win:
            current_streak += 1
        else:
            if last_win and current_streak > max_win_streak:
                max_win_streak = current_streak
            elif not last_win and current_streak > max_loss_streak:
                max_loss_streak = current_streak
            current_streak = 1
        last_win = is_win

    if max_win_streak >= 5:
        insights.append({
            'type': 'success',
            'title': '连胜纪录',
            'content': f'最长连胜 {max_win_streak} 笔',
        })

    if max_loss_streak >= 4:
        insights.append({
            'type': 'warning',
            'title': '连亏警示',
            'content': f'最长连亏 {max_loss_streak} 笔，注意风险控制',
        })

    # 5. 大额亏损占比
    total_loss = df[df['net_pnl'] < 0]['net_pnl'].sum()
    big_losses = df[df['net_pnl'] < -1000]['net_pnl'].sum()

    if total_loss < 0 and big_losses / total_loss > 0.5:
        insights.append({
            'type': 'warning',
            'title': '大额亏损集中',
            'content': f'超过 50% 的亏损来自单笔亏损 > $1000 的交易',
        })

    # 渲染洞察
    if not insights:
        st.info("暂无显著交易模式发现")
        return

    for insight in insights:
        color_map = {
            'success': COLORS['profit'],
            'info': COLORS['accent_cyan'],
            'warning': COLORS['warning'],
        }
        icon_map = {
            'success': '✅',
            'info': 'ℹ️',
            'warning': '⚠️',
        }

        color = color_map.get(insight['type'], COLORS['text_secondary'])
        icon = icon_map.get(insight['type'], '•')

        st.markdown(f"""
        <div style="
            background: {color}15;
            border-left: 3px solid {color};
            border-radius: 0 8px 8px 0;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span>{icon}</span>
                <span style="color: {color}; font-weight: 600;">{insight['title']}</span>
            </div>
            <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin-top: 0.25rem;">
                {insight['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_time_analysis(df: pd.DataFrame):
    """渲染时间维度分析"""
    if df is None or df.empty:
        st.info("暂无交易数据")
        return

    df_copy = df.copy()
    df_copy['close_date'] = pd.to_datetime(df_copy['close_date'])
    df_copy['month'] = df_copy['close_date'].dt.to_period('M')

    # 按月汇总
    monthly = df_copy.groupby('month').agg({
        'net_pnl': 'sum',
        'id': 'count',
    }).reset_index()
    monthly.columns = ['month', 'pnl', 'trades']
    monthly['month_str'] = monthly['month'].astype(str)

    # 创建柱状图
    colors = [COLORS['profit'] if pnl >= 0 else COLORS['loss'] for pnl in monthly['pnl']]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=monthly['month_str'],
        y=monthly['pnl'],
        marker_color=colors,
        text=[f"${v:,.0f}" for v in monthly['pnl']],
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary'], size=10),
        hovertemplate=(
            '<b>%{x}</b><br>'
            'P&L: $%{y:,.0f}<br>'
            '<extra></extra>'
        ),
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_secondary'],
        font=dict(color=COLORS['text_secondary']),
        xaxis=dict(
            gridcolor=COLORS['border'],
            tickfont=dict(color=COLORS['text_secondary'], size=9),
            tickangle=-45,
        ),
        yaxis=dict(
            gridcolor=COLORS['border'],
            tickfont=dict(color=COLORS['text_secondary']),
            tickprefix='$',
        ),
        showlegend=False,
        bargap=0.3,
    )

    st.plotly_chart(fig, use_container_width=True)

    # 月度统计表
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    cols = st.columns(len(monthly) if len(monthly) <= 6 else 6)

    for i, (_, row) in enumerate(monthly.tail(6).iterrows()):
        pnl_color = COLORS['profit'] if row['pnl'] >= 0 else COLORS['loss']
        pnl_sign = "+" if row['pnl'] >= 0 else ""

        with cols[i % 6]:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_secondary']};
                border-radius: 6px;
                padding: 0.5rem;
                text-align: center;
            ">
                <div style="color: {COLORS['text_muted']}; font-size: 0.7rem;">{row['month_str']}</div>
                <div style="color: {pnl_color}; font-family: {FONTS['mono']}; font-size: 0.9rem; font-weight: 600;">
                    {pnl_sign}${abs(row['pnl']):,.0f}
                </div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.65rem;">{int(row['trades'])} 笔</div>
            </div>
            """, unsafe_allow_html=True)


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
        margin-bottom: 1.5rem;
    ">
        <div>
            <div style="
                font-size: 1.75rem;
                font-weight: 700;
                font-family: {FONTS['heading']};
                color: {COLORS['text_primary']};
            ">📈 绩效分析</div>
            <div style="
                color: {COLORS['text_secondary']};
                font-size: 0.85rem;
            ">发现交易模式，优化交易策略</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 获取数据
    df = loader.get_positions_with_scores()

    if df is None or df.empty:
        st.warning("暂无交易数据")
        return

    # 确保 close_date 是 datetime 类型
    df['close_date'] = pd.to_datetime(df['close_date'])

    # ================================================================
    # 年度选择
    # ================================================================
    available_years = sorted(df['close_date'].dt.year.unique(), reverse=True)
    selected_year = st.selectbox(
        "选择年份",
        options=available_years,
        index=0,
        label_visibility="collapsed",
    )

    year_df = df[df['close_date'].dt.year == selected_year]

    # ================================================================
    # 年度概览统计
    # ================================================================
    total_pnl = year_df['net_pnl'].sum()
    win_count = (year_df['net_pnl'] > 0).sum()
    win_rate = win_count / len(year_df) * 100 if len(year_df) > 0 else 0
    avg_score = year_df['overall_score'].mean() if 'overall_score' in year_df.columns else 0
    trade_count = len(year_df)

    cols = st.columns(4)

    stats = [
        ("总盈亏", total_pnl, COLORS['profit'] if total_pnl >= 0 else COLORS['loss']),
        ("胜率", win_rate, COLORS['text_primary']),
        ("平均评分", avg_score, COLORS['text_primary']),
        ("交易数", trade_count, COLORS['text_primary']),
    ]

    for col, (label, value, color) in zip(cols, stats):
        with col:
            if label == "总盈亏":
                sign = "+" if value >= 0 else ""
                display_val = f"{sign}${abs(value):,.0f}"
            elif label == "胜率":
                display_val = f"{value:.1f}%"
            elif label == "平均评分":
                display_val = f"{value:.0f}"
            else:
                display_val = f"{value:,}"

            st.markdown(f"""
            <div style="
                background: {COLORS['bg_secondary']};
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            ">
                <div style="color: {COLORS['text_muted']}; font-size: 0.75rem; text-transform: uppercase;">{label}</div>
                <div style="color: {color}; font-size: 1.5rem; font-weight: 700; font-family: {FONTS['mono']};">{display_val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ================================================================
    # 日历热力图
    # ================================================================
    st.markdown(f"""
    <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
        📅 日历热力图 - {selected_year}
    </div>
    """, unsafe_allow_html=True)

    # 准备日历数据
    daily_pnl = year_df.groupby(year_df['close_date'].dt.date)['net_pnl'].sum().reset_index()
    daily_pnl.columns = ['date', 'pnl']
    daily_pnl['date'] = pd.to_datetime(daily_pnl['date'])

    fig = create_calendar_heatmap(
        daily_pnl,
        date_col='date',
        pnl_col='pnl',
        year=selected_year,
        height=180,
    )
    st.plotly_chart(fig, use_container_width=True)

    # 月度概览
    render_yearly_calendar(daily_pnl, selected_year)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ================================================================
    # 策略分析 + 模式发现
    # ================================================================
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown(f"""
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
            🎯 策略分析
        </div>
        """, unsafe_allow_html=True)
        render_strategy_analysis(year_df)

    with col2:
        st.markdown(f"""
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
            💡 模式发现
        </div>
        """, unsafe_allow_html=True)
        render_pattern_insights(year_df)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ================================================================
    # 时间维度分析
    # ================================================================
    st.markdown(f"""
    <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
        📊 月度趋势
    </div>
    """, unsafe_allow_html=True)

    render_time_analysis(year_df)

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
        数据分析基于 {trade_count} 笔交易
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
