"""
Enhanced Candlestick Chart - TradingView风格K线图

增强特性:
- 入场/出场标记 (三角形 + 价格标注)
- MAE线 (持仓期间最低点)
- MFE线 (持仓期间最高点)
- 离场后区域降低透明度
- 成交量柱状图
- 均线叠加
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from visualization.styles import COLORS, FONTS


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """将 hex 颜色转换为 rgba 格式"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def create_enhanced_candlestick(
    df: pd.DataFrame,
    entry_date: Optional[datetime] = None,
    exit_date: Optional[datetime] = None,
    entry_price: Optional[float] = None,
    exit_price: Optional[float] = None,
    mae_price: Optional[float] = None,
    mfe_price: Optional[float] = None,
    is_long: bool = True,
    title: str = "",
    show_volume: bool = True,
    show_ma: bool = False,
    show_post_exit_fade: bool = True,
    height: int = 500,
) -> go.Figure:
    """
    创建增强版K线图 (TradingView风格)

    Args:
        df: DataFrame with columns: date, open, high, low, close, volume
        entry_date: 入场日期
        exit_date: 出场日期
        entry_price: 入场价格
        exit_price: 出场价格
        mae_price: MAE对应价格 (持仓期间最不利价格)
        mfe_price: MFE对应价格 (持仓期间最有利价格)
        is_long: 是否做多
        title: 图表标题
        show_volume: 是否显示成交量
        show_ma: 是否显示均线
        show_post_exit_fade: 是否淡化出场后区域
        height: 图表高度

    Returns:
        Plotly Figure
    """
    if df is None or df.empty:
        return _create_empty_chart(title, height)

    # 创建子图
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.75, 0.25],
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # 处理日期转换
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # 确定持仓区间
    if entry_date and exit_date:
        # 持仓期间的K线
        holding_mask = (df['date'] >= pd.Timestamp(entry_date)) & (df['date'] <= pd.Timestamp(exit_date))
        before_mask = df['date'] < pd.Timestamp(entry_date)
        after_mask = df['date'] > pd.Timestamp(exit_date)
    else:
        holding_mask = pd.Series([True] * len(df))
        before_mask = pd.Series([False] * len(df))
        after_mask = pd.Series([False] * len(df))

    # ================================================================
    # 主K线图
    # ================================================================

    # 入场前K线 (正常显示)
    if before_mask.any():
        before_df = df[before_mask]
        fig.add_trace(
            go.Candlestick(
                x=before_df['date'],
                open=before_df['open'],
                high=before_df['high'],
                low=before_df['low'],
                close=before_df['close'],
                name='',
                increasing=dict(
                    line=dict(color=COLORS['chart_up'], width=1),
                    fillcolor=COLORS['chart_up'],
                ),
                decreasing=dict(
                    line=dict(color=COLORS['chart_down'], width=1),
                    fillcolor=COLORS['chart_down'],
                ),
                showlegend=False,
                opacity=0.6,  # 入场前稍微淡化
            ),
            row=1, col=1
        )

    # 持仓期间K线 (高亮显示)
    if holding_mask.any():
        holding_df = df[holding_mask]
        fig.add_trace(
            go.Candlestick(
                x=holding_df['date'],
                open=holding_df['open'],
                high=holding_df['high'],
                low=holding_df['low'],
                close=holding_df['close'],
                name='持仓期间',
                increasing=dict(
                    line=dict(color=COLORS['chart_up'], width=1),
                    fillcolor=COLORS['chart_up'],
                ),
                decreasing=dict(
                    line=dict(color=COLORS['chart_down'], width=1),
                    fillcolor=COLORS['chart_down'],
                ),
                showlegend=False,
            ),
            row=1, col=1
        )

    # 出场后K线 (淡化显示)
    if show_post_exit_fade and after_mask.any():
        after_df = df[after_mask]
        fig.add_trace(
            go.Candlestick(
                x=after_df['date'],
                open=after_df['open'],
                high=after_df['high'],
                low=after_df['low'],
                close=after_df['close'],
                name='',
                increasing=dict(
                    line=dict(color=COLORS['chart_up'], width=1),
                    fillcolor=COLORS['chart_up'],
                ),
                decreasing=dict(
                    line=dict(color=COLORS['chart_down'], width=1),
                    fillcolor=COLORS['chart_down'],
                ),
                showlegend=False,
                opacity=0.3,  # 出场后显著淡化
            ),
            row=1, col=1
        )

    # ================================================================
    # 入场/出场标记
    # ================================================================

    # 入场标记
    if entry_date and entry_price:
        entry_color = COLORS['profit'] if is_long else COLORS['loss']
        entry_symbol = 'triangle-up' if is_long else 'triangle-down'
        entry_label = '买入' if is_long else '卖空'

        fig.add_trace(
            go.Scatter(
                x=[entry_date],
                y=[entry_price],
                mode='markers+text',
                name=entry_label,
                marker=dict(
                    symbol=entry_symbol,
                    size=16,
                    color=entry_color,
                    line=dict(width=2, color='white'),
                ),
                text=[f'${entry_price:.2f}'],
                textposition='top center' if is_long else 'bottom center',
                textfont=dict(
                    size=10,
                    color=entry_color,
                    family=FONTS['mono'],
                ),
                hovertemplate=(
                    f'<b>{entry_label}</b><br>'
                    f'日期: %{{x|%Y-%m-%d}}<br>'
                    f'价格: ${entry_price:.2f}<br>'
                    '<extra></extra>'
                ),
            ),
            row=1, col=1
        )

    # 出场标记
    if exit_date and exit_price:
        exit_color = COLORS['loss'] if is_long else COLORS['profit']
        exit_symbol = 'triangle-down' if is_long else 'triangle-up'
        exit_label = '卖出' if is_long else '买回'

        fig.add_trace(
            go.Scatter(
                x=[exit_date],
                y=[exit_price],
                mode='markers+text',
                name=exit_label,
                marker=dict(
                    symbol=exit_symbol,
                    size=16,
                    color=exit_color,
                    line=dict(width=2, color='white'),
                ),
                text=[f'${exit_price:.2f}'],
                textposition='bottom center' if is_long else 'top center',
                textfont=dict(
                    size=10,
                    color=exit_color,
                    family=FONTS['mono'],
                ),
                hovertemplate=(
                    f'<b>{exit_label}</b><br>'
                    f'日期: %{{x|%Y-%m-%d}}<br>'
                    f'价格: ${exit_price:.2f}<br>'
                    '<extra></extra>'
                ),
            ),
            row=1, col=1
        )

    # ================================================================
    # MAE/MFE 水平线
    # ================================================================

    if entry_date and exit_date:
        x_range = [entry_date, exit_date]

        # MAE线 (最大不利偏移 - 对做多来说是最低价)
        if mae_price:
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=[mae_price, mae_price],
                    mode='lines',
                    name='MAE',
                    line=dict(
                        color=COLORS['loss'],
                        width=1.5,
                        dash='dash',
                    ),
                    hovertemplate=(
                        '<b>MAE (最大不利)</b><br>'
                        f'价格: ${mae_price:.2f}<br>'
                        '<extra></extra>'
                    ),
                ),
                row=1, col=1
            )

            # MAE标注
            fig.add_annotation(
                x=exit_date,
                y=mae_price,
                text=f'MAE ${mae_price:.2f}',
                showarrow=False,
                xanchor='left',
                yanchor='middle',
                font=dict(size=9, color=COLORS['loss'], family=FONTS['mono']),
                bgcolor=hex_to_rgba(COLORS['loss'], 0.12),
                bordercolor=COLORS['loss'],
                borderwidth=1,
                borderpad=2,
                row=1, col=1
            )

        # MFE线 (最大有利偏移 - 对做多来说是最高价)
        if mfe_price:
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=[mfe_price, mfe_price],
                    mode='lines',
                    name='MFE',
                    line=dict(
                        color=COLORS['profit'],
                        width=1.5,
                        dash='dash',
                    ),
                    hovertemplate=(
                        '<b>MFE (最大有利)</b><br>'
                        f'价格: ${mfe_price:.2f}<br>'
                        '<extra></extra>'
                    ),
                ),
                row=1, col=1
            )

            # MFE标注
            fig.add_annotation(
                x=exit_date,
                y=mfe_price,
                text=f'MFE ${mfe_price:.2f}',
                showarrow=False,
                xanchor='left',
                yanchor='middle',
                font=dict(size=9, color=COLORS['profit'], family=FONTS['mono']),
                bgcolor=hex_to_rgba(COLORS['profit'], 0.12),
                bordercolor=COLORS['profit'],
                borderwidth=1,
                borderpad=2,
                row=1, col=1
            )

    # ================================================================
    # 均线
    # ================================================================

    if show_ma:
        ma_configs = [
            ('ma_5', 'MA5', '#FFB800'),
            ('ma_20', 'MA20', '#00D9FF'),
            ('ma_50', 'MA50', '#A855F7'),
        ]

        for ma_col, ma_name, ma_color in ma_configs:
            if ma_col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df[ma_col],
                        name=ma_name,
                        line=dict(color=ma_color, width=1.5),
                        opacity=0.7,
                        hoverinfo='skip',
                    ),
                    row=1, col=1
                )

    # ================================================================
    # 成交量
    # ================================================================

    if show_volume and 'volume' in df.columns:
        # 计算成交量颜色
        colors = []
        for _, row in df.iterrows():
            if row['close'] >= row['open']:
                colors.append(COLORS['chart_up'])
            else:
                colors.append(COLORS['chart_down'])

        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name='成交量',
                marker_color=colors,
                opacity=0.5,
                showlegend=False,
                hovertemplate='成交量: %{y:,.0f}<extra></extra>',
            ),
            row=2, col=1
        )

    # ================================================================
    # 持仓区间高亮背景
    # ================================================================

    if entry_date and exit_date:
        fig.add_vrect(
            x0=entry_date,
            x1=exit_date,
            fillcolor=COLORS['accent_cyan'],
            opacity=0.05,
            layer='below',
            line_width=0,
            row=1, col=1
        )

    # ================================================================
    # 布局设置
    # ================================================================

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family=FONTS['heading'], size=16, color=COLORS['text_primary']),
            x=0,
            xanchor='left',
        ) if title else None,
        height=height,
        margin=dict(l=10, r=80, t=50 if title else 20, b=40),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_secondary'],
        font=dict(
            family=FONTS['body'].split(',')[0].strip('"'),
            color=COLORS['text_secondary'],
        ),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            bordercolor=COLORS['border'],
            borderwidth=0,
            font=dict(color=COLORS['text_secondary'], size=10),
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        dragmode='pan',
    )

    # X轴设置
    fig.update_xaxes(
        gridcolor=COLORS['chart_grid'],
        linecolor=COLORS['border'],
        tickfont=dict(color=COLORS['chart_text'], size=10),
        showgrid=True,
        gridwidth=1,
    )

    # Y轴设置
    fig.update_yaxes(
        gridcolor=COLORS['chart_grid'],
        linecolor=COLORS['border'],
        tickfont=dict(color=COLORS['chart_text'], size=10),
        showgrid=True,
        gridwidth=1,
        side='right',
        tickprefix='$',
        row=1, col=1
    )

    if show_volume:
        fig.update_yaxes(
            showgrid=False,
            tickfont=dict(color=COLORS['chart_text'], size=9),
            side='right',
            row=2, col=1
        )

    return fig


def create_mini_candlestick(
    df: pd.DataFrame,
    entry_date: Optional[datetime] = None,
    exit_date: Optional[datetime] = None,
    height: int = 80,
    width: int = 200,
) -> go.Figure:
    """
    创建迷你K线图 (用于表格内嵌)

    Args:
        df: K线数据
        entry_date: 入场日期
        exit_date: 出场日期
        height: 高度
        width: 宽度

    Returns:
        Plotly Figure
    """
    if df is None or df.empty:
        return _create_empty_mini_chart(height, width)

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    fig = go.Figure()

    # 简化K线 (只用收盘价折线)
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['close'],
            mode='lines',
            line=dict(color=COLORS['accent_cyan'], width=1.5),
            fill='tozeroy',
            fillcolor=f"{COLORS['accent_cyan']}10",
            hoverinfo='skip',
        )
    )

    # 入场出场标记
    if entry_date:
        entry_row = df[df['date'] == pd.Timestamp(entry_date)]
        if not entry_row.empty:
            fig.add_trace(
                go.Scatter(
                    x=[entry_date],
                    y=[entry_row.iloc[0]['close']],
                    mode='markers',
                    marker=dict(color=COLORS['profit'], size=6, symbol='circle'),
                    hoverinfo='skip',
                )
            )

    if exit_date:
        exit_row = df[df['date'] == pd.Timestamp(exit_date)]
        if not exit_row.empty:
            fig.add_trace(
                go.Scatter(
                    x=[exit_date],
                    y=[exit_row.iloc[0]['close']],
                    mode='markers',
                    marker=dict(color=COLORS['loss'], size=6, symbol='circle'),
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


def _create_empty_chart(title: str, height: int) -> go.Figure:
    """创建空图表"""
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
        margin=dict(l=10, r=10, t=50 if title else 10, b=10),
        paper_bgcolor=COLORS['bg_primary'],
        plot_bgcolor=COLORS['bg_secondary'],
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
