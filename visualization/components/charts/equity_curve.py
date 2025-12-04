"""
Equity Curve - 权益曲线图表

展示累计盈亏趋势，支持回撤叠加显示
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from visualization.styles import COLORS, FONTS


def create_equity_curve(
    df: pd.DataFrame,
    date_col: str = 'close_date',
    pnl_col: str = 'net_pnl',
    title: Optional[str] = None,
    show_drawdown: bool = False,
    show_trades: bool = True,
    height: int = 400,
) -> go.Figure:
    """
    创建权益曲线图

    Args:
        df: 包含交易数据的 DataFrame
        date_col: 日期列名
        pnl_col: 盈亏列名
        title: 图表标题
        show_drawdown: 是否显示回撤
        show_trades: 是否显示交易点
        height: 图表高度

    Returns:
        Plotly Figure 对象
    """
    if df is None or df.empty:
        return _create_empty_chart(title, height)

    # 复制数据并排序
    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col])
    data = data.sort_values(date_col)

    # 计算累计盈亏
    data['cumulative_pnl'] = data[pnl_col].cumsum()

    # 计算回撤
    data['peak'] = data['cumulative_pnl'].cummax()
    data['drawdown'] = data['cumulative_pnl'] - data['peak']
    data['drawdown_pct'] = (data['drawdown'] / data['peak'].abs().replace(0, 1)) * 100

    # 确定盈亏区域颜色
    final_pnl = data['cumulative_pnl'].iloc[-1]
    is_profit = final_pnl >= 0
    main_color = COLORS['profit'] if is_profit else COLORS['loss']
    fill_color = f"rgba({int(main_color[1:3], 16)}, {int(main_color[3:5], 16)}, {int(main_color[5:7], 16)}, 0.2)"

    # 创建图表
    if show_drawdown:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.05,
        )
    else:
        fig = go.Figure()

    # 主曲线 - 权益曲线
    fig.add_trace(
        go.Scatter(
            x=data[date_col],
            y=data['cumulative_pnl'],
            mode='lines',
            name='Cumulative P&L',
            line=dict(color=main_color, width=2),
            fill='tozeroy',
            fillcolor=fill_color,
            hovertemplate=(
                '<b>%{x|%Y-%m-%d}</b><br>'
                'Cumulative P&L: $%{y:,.2f}<br>'
                '<extra></extra>'
            ),
        ),
        row=1 if show_drawdown else None,
        col=1 if show_drawdown else None,
    )

    # 零线
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=COLORS['text_muted'],
        line_width=1,
        row=1 if show_drawdown else None,
    )

    # 交易点标记
    if show_trades:
        # 盈利交易
        profit_trades = data[data[pnl_col] > 0]
        if not profit_trades.empty:
            fig.add_trace(
                go.Scatter(
                    x=profit_trades[date_col],
                    y=profit_trades['cumulative_pnl'],
                    mode='markers',
                    name='Profit',
                    marker=dict(
                        color=COLORS['profit'],
                        size=6,
                        symbol='circle',
                    ),
                    hovertemplate=(
                        '<b>%{x|%Y-%m-%d}</b><br>'
                        'Trade P&L: +$%{customdata:,.2f}<br>'
                        '<extra></extra>'
                    ),
                    customdata=profit_trades[pnl_col],
                    showlegend=False,
                ),
                row=1 if show_drawdown else None,
                col=1 if show_drawdown else None,
            )

        # 亏损交易
        loss_trades = data[data[pnl_col] < 0]
        if not loss_trades.empty:
            fig.add_trace(
                go.Scatter(
                    x=loss_trades[date_col],
                    y=loss_trades['cumulative_pnl'],
                    mode='markers',
                    name='Loss',
                    marker=dict(
                        color=COLORS['loss'],
                        size=6,
                        symbol='circle',
                    ),
                    hovertemplate=(
                        '<b>%{x|%Y-%m-%d}</b><br>'
                        'Trade P&L: -$%{customdata:,.2f}<br>'
                        '<extra></extra>'
                    ),
                    customdata=loss_trades[pnl_col].abs(),
                    showlegend=False,
                ),
                row=1 if show_drawdown else None,
                col=1 if show_drawdown else None,
            )

    # 回撤子图
    if show_drawdown:
        fig.add_trace(
            go.Scatter(
                x=data[date_col],
                y=data['drawdown'],
                mode='lines',
                name='Drawdown',
                line=dict(color=COLORS['loss'], width=1),
                fill='tozeroy',
                fillcolor=f"rgba({int(COLORS['loss'][1:3], 16)}, {int(COLORS['loss'][3:5], 16)}, {int(COLORS['loss'][5:7], 16)}, 0.3)",
                hovertemplate=(
                    '<b>%{x|%Y-%m-%d}</b><br>'
                    'Drawdown: $%{y:,.2f}<br>'
                    '<extra></extra>'
                ),
            ),
            row=2,
            col=1,
        )

    # 样式设置
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family=FONTS['heading'], size=16, color=COLORS['text_primary']),
            x=0,
            xanchor='left',
        ) if title else None,
        height=height,
        margin=dict(l=0, r=0, t=40 if title else 10, b=0),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_primary'],
        font=dict(family=FONTS['body'], color=COLORS['text_secondary']),
        showlegend=False,
        hovermode='x unified',
        xaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=False,
            tickfont=dict(size=10),
            tickformat='%b %Y',
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS['border'],
            gridwidth=1,
            showline=False,
            zeroline=False,
            tickfont=dict(size=10),
            tickprefix='$',
            tickformat=',.0f',
            title=None,
        ),
    )

    if show_drawdown:
        fig.update_yaxes(
            title=None,
            tickprefix='$',
            tickformat=',.0f',
            row=2,
        )
        fig.update_xaxes(
            tickformat='%b %Y',
            row=2,
        )

    return fig


def create_mini_equity_curve(
    df: pd.DataFrame,
    date_col: str = 'close_date',
    pnl_col: str = 'net_pnl',
    height: int = 60,
    width: int = 120,
) -> go.Figure:
    """
    创建迷你权益曲线 (用于表格内嵌)

    Args:
        df: 交易数据
        date_col: 日期列
        pnl_col: 盈亏列
        height: 高度
        width: 宽度

    Returns:
        Plotly Figure
    """
    if df is None or df.empty:
        return _create_empty_mini_chart(height, width)

    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col])
    data = data.sort_values(date_col)
    data['cumulative_pnl'] = data[pnl_col].cumsum()

    final_pnl = data['cumulative_pnl'].iloc[-1]
    is_profit = final_pnl >= 0
    color = COLORS['profit'] if is_profit else COLORS['loss']

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data[date_col],
            y=data['cumulative_pnl'],
            mode='lines',
            line=dict(color=color, width=1.5),
            fill='tozeroy',
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2)",
            hoverinfo='skip',
        )
    )

    fig.update_layout(
        height=height,
        width=width,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig


def _create_empty_chart(title: Optional[str], height: int) -> go.Figure:
    """创建空图表（无数据时显示）"""
    fig = go.Figure()

    fig.add_annotation(
        text="No data available",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color=COLORS['text_muted']),
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family=FONTS['heading'], size=16, color=COLORS['text_primary']),
        ) if title else None,
        height=height,
        margin=dict(l=0, r=0, t=40 if title else 10, b=0),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_primary'],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig


def _create_empty_mini_chart(height: int, width: int) -> go.Figure:
    """创建空迷你图表"""
    fig = go.Figure()

    fig.update_layout(
        height=height,
        width=width,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig
