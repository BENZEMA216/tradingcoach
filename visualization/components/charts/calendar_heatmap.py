"""
Calendar Heatmap - 日历热力图

按日期显示每日盈亏的热力图
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Optional
from datetime import datetime, timedelta
import calendar
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from visualization.styles import COLORS, FONTS


def create_calendar_heatmap(
    df: pd.DataFrame,
    date_col: str = 'close_date',
    pnl_col: str = 'net_pnl',
    year: Optional[int] = None,
    month: Optional[int] = None,
    title: Optional[str] = None,
    height: int = 200,
) -> go.Figure:
    """
    创建日历热力图

    Args:
        df: 交易数据 DataFrame
        date_col: 日期列名
        pnl_col: 盈亏列名
        year: 年份 (默认当前年)
        month: 月份 (如果指定则只显示该月)
        title: 图表标题
        height: 图表高度

    Returns:
        Plotly Figure
    """
    if df is None or df.empty:
        return _create_empty_heatmap(title, height)

    # 数据准备
    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col])

    # 按日期聚合
    daily_pnl = data.groupby(data[date_col].dt.date)[pnl_col].sum().reset_index()
    daily_pnl.columns = ['date', 'pnl']
    daily_pnl['date'] = pd.to_datetime(daily_pnl['date'])

    # 确定时间范围
    if year is None:
        year = daily_pnl['date'].max().year

    if month is not None:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

    # 创建完整日期范围
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    full_calendar = pd.DataFrame({'date': date_range})
    full_calendar = full_calendar.merge(daily_pnl, on='date', how='left')
    full_calendar['pnl'] = full_calendar['pnl'].fillna(0)

    # 添加日历信息
    full_calendar['weekday'] = full_calendar['date'].dt.weekday  # 0=Monday
    full_calendar['week'] = full_calendar['date'].dt.isocalendar().week
    full_calendar['month'] = full_calendar['date'].dt.month
    full_calendar['day'] = full_calendar['date'].dt.day

    # 调整周数（确保连续）
    if month is None:
        # 年度视图: 计算从年初开始的周数
        full_calendar['week_of_year'] = ((full_calendar['date'] - start_date).dt.days // 7)
    else:
        # 月度视图
        full_calendar['week_of_year'] = ((full_calendar['date'] - start_date).dt.days // 7)

    # 颜色映射
    max_pnl = max(abs(full_calendar['pnl'].max()), abs(full_calendar['pnl'].min()), 1)

    def get_color(pnl):
        if pnl == 0:
            return COLORS['bg_tertiary']
        elif pnl > 0:
            intensity = min(pnl / max_pnl, 1)
            return f"rgba(0, 255, 136, {0.2 + intensity * 0.8})"
        else:
            intensity = min(abs(pnl) / max_pnl, 1)
            return f"rgba(255, 59, 92, {0.2 + intensity * 0.8})"

    full_calendar['color'] = full_calendar['pnl'].apply(get_color)

    # 创建热力图
    fig = go.Figure()

    # 添加每个日期的方块
    for _, row in full_calendar.iterrows():
        pnl = row['pnl']
        hover_text = (
            f"<b>{row['date'].strftime('%Y-%m-%d')}</b><br>"
            f"P&L: {'+'if pnl >= 0 else ''}${pnl:,.2f}"
        )

        fig.add_trace(
            go.Scatter(
                x=[row['week_of_year']],
                y=[6 - row['weekday']],  # 反转，周一在顶部
                mode='markers',
                marker=dict(
                    size=15 if month else 10,
                    color=row['color'],
                    symbol='square',
                    line=dict(width=1, color=COLORS['bg_primary']),
                ),
                hovertemplate=hover_text + '<extra></extra>',
                showlegend=False,
            )
        )

    # 星期标签
    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    fig.update_layout(
        title=dict(
            text=title or f"Daily P&L - {year}" + (f"-{month:02d}" if month else ""),
            font=dict(family=FONTS['heading'], size=14, color=COLORS['text_primary']),
            x=0,
        ) if title or True else None,
        height=height,
        margin=dict(l=40, r=10, t=30, b=10),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_primary'],
        xaxis=dict(
            showgrid=False,
            showticklabels=False if month else True,
            zeroline=False,
            tickmode='array' if not month else None,
            ticktext=[f"W{i+1}" for i in range(53)] if not month else None,
            tickvals=list(range(53)) if not month else None,
            tickfont=dict(size=8, color=COLORS['text_muted']),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            tickmode='array',
            ticktext=weekday_labels[::-1],  # 反转
            tickvals=list(range(7)),
            tickfont=dict(size=9, color=COLORS['text_muted']),
        ),
        showlegend=False,
        hovermode='closest',
    )

    return fig


def create_month_calendar(
    df: pd.DataFrame,
    year: int,
    month: int,
    date_col: str = 'close_date',
    pnl_col: str = 'net_pnl',
    height: int = 180,
) -> go.Figure:
    """
    创建单月日历视图 (更紧凑的月度热力图)

    Args:
        df: 交易数据
        year: 年份
        month: 月份
        date_col: 日期列
        pnl_col: 盈亏列
        height: 高度

    Returns:
        Plotly Figure
    """
    return create_calendar_heatmap(
        df=df,
        date_col=date_col,
        pnl_col=pnl_col,
        year=year,
        month=month,
        title=f"{calendar.month_name[month]} {year}",
        height=height,
    )


def _create_empty_heatmap(title: Optional[str], height: int) -> go.Figure:
    """创建空热力图"""
    fig = go.Figure()

    fig.add_annotation(
        text="No trading data",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=12, color=COLORS['text_muted']),
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family=FONTS['heading'], size=14, color=COLORS['text_primary']),
        ) if title else None,
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_primary'],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig
