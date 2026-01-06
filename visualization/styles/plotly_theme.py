"""
Plotly 深色主题
为所有图表提供一致的深色主题样式
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, Any, List
from .theme import COLORS, FONTS


def get_plotly_theme() -> Dict[str, Any]:
    """
    获取 Plotly 深色主题配置

    Returns:
        Plotly layout 配置字典
    """
    return {
        # 背景
        'paper_bgcolor': COLORS['bg_primary'],
        'plot_bgcolor': COLORS['bg_secondary'],

        # 字体
        'font': {
            'family': FONTS['body'].split(',')[0].strip('"'),
            'size': 12,
            'color': COLORS['text_secondary'],
        },

        # 标题
        'title': {
            'font': {
                'family': FONTS['heading'].split(',')[0].strip('"'),
                'size': 18,
                'color': COLORS['text_primary'],
            },
            'x': 0,
            'xanchor': 'left',
        },

        # 图例
        'legend': {
            'bgcolor': 'rgba(0,0,0,0)',
            'bordercolor': COLORS['border'],
            'borderwidth': 0,
            'font': {
                'color': COLORS['text_secondary'],
                'size': 11,
            },
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1,
        },

        # X轴
        'xaxis': {
            'gridcolor': COLORS['chart_grid'],
            'linecolor': COLORS['border'],
            'tickfont': {
                'color': COLORS['chart_text'],
                'size': 10,
            },
            'title_font': {
                'color': COLORS['text_secondary'],
            },
            'zerolinecolor': COLORS['border'],
            'showgrid': True,
            'gridwidth': 1,
        },

        # Y轴
        'yaxis': {
            'gridcolor': COLORS['chart_grid'],
            'linecolor': COLORS['border'],
            'tickfont': {
                'color': COLORS['chart_text'],
                'size': 10,
            },
            'title_font': {
                'color': COLORS['text_secondary'],
            },
            'zerolinecolor': COLORS['border'],
            'showgrid': True,
            'gridwidth': 1,
            'side': 'right',  # 价格轴在右侧
        },

        # 悬浮提示
        'hoverlabel': {
            'bgcolor': COLORS['bg_tertiary'],
            'bordercolor': COLORS['border'],
            'font': {
                'color': COLORS['text_primary'],
                'family': FONTS['mono'].split(',')[0].strip('"'),
                'size': 12,
            },
        },

        # 边距
        'margin': {
            'l': 10,
            'r': 60,
            't': 50,
            'b': 40,
        },

        # 交互
        'hovermode': 'x unified',
        'dragmode': 'pan',
    }


def apply_dark_theme(fig: go.Figure) -> go.Figure:
    """
    应用深色主题到现有图表

    Args:
        fig: Plotly Figure 对象

    Returns:
        更新后的 Figure
    """
    fig.update_layout(**get_plotly_theme())
    return fig


def create_dark_candlestick(
    df,
    title: str = "",
    show_volume: bool = True,
    show_ma: bool = True,
    show_bb: bool = False,
    buy_points: Optional[List[Dict]] = None,
    sell_points: Optional[List[Dict]] = None,
    height: int = 600,
) -> go.Figure:
    """
    创建深色主题 K 线图

    Args:
        df: DataFrame with columns: date, open, high, low, close, volume
        title: 图表标题
        show_volume: 是否显示成交量
        show_ma: 是否显示均线
        show_bb: 是否显示布林带
        buy_points: 买入点 [{'date': date, 'price': price}]
        sell_points: 卖出点 [{'date': date, 'price': price}]
        height: 图表高度

    Returns:
        Plotly Figure
    """
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

    # K线图
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
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
        ),
        row=1, col=1
    )

    # 均线
    if show_ma and 'ma_5' in df.columns:
        ma_colors = {
            'ma_5': '#FFB800',   # 金色
            'ma_20': '#00D9FF',  # 青色
            'ma_50': '#A855F7',  # 紫色
        }
        ma_names = {
            'ma_5': 'MA5',
            'ma_20': 'MA20',
            'ma_50': 'MA50',
        }
        for ma_col, color in ma_colors.items():
            if ma_col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df[ma_col],
                        name=ma_names[ma_col],
                        line=dict(color=color, width=1.5),
                        opacity=0.8,
                    ),
                    row=1, col=1
                )

    # 布林带
    if show_bb and all(col in df.columns for col in ['bb_upper', 'bb_middle', 'bb_lower']):
        # 上轨
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['bb_upper'],
                name='BB Upper',
                line=dict(color=COLORS['accent_cyan'], width=1, dash='dot'),
                opacity=0.5,
            ),
            row=1, col=1
        )
        # 中轨
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['bb_middle'],
                name='BB Middle',
                line=dict(color=COLORS['accent_cyan'], width=1),
                opacity=0.5,
            ),
            row=1, col=1
        )
        # 下轨
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['bb_lower'],
                name='BB Lower',
                line=dict(color=COLORS['accent_cyan'], width=1, dash='dot'),
                opacity=0.5,
                fill='tonexty',
                fillcolor='rgba(0, 217, 255, 0.05)',
            ),
            row=1, col=1
        )

    # 买入点
    if buy_points:
        fig.add_trace(
            go.Scatter(
                x=[p['date'] for p in buy_points],
                y=[p['price'] for p in buy_points],
                mode='markers',
                name='买入',
                marker=dict(
                    symbol='triangle-up',
                    size=14,
                    color=COLORS['profit'],
                    line=dict(width=2, color='white'),
                ),
            ),
            row=1, col=1
        )

    # 卖出点
    if sell_points:
        fig.add_trace(
            go.Scatter(
                x=[p['date'] for p in sell_points],
                y=[p['price'] for p in sell_points],
                mode='markers',
                name='卖出',
                marker=dict(
                    symbol='triangle-down',
                    size=14,
                    color=COLORS['loss'],
                    line=dict(width=2, color='white'),
                ),
            ),
            row=1, col=1
        )

    # 成交量
    if show_volume and 'volume' in df.columns:
        colors = [
            COLORS['chart_up'] if row['close'] >= row['open'] else COLORS['chart_down']
            for _, row in df.iterrows()
        ]
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name='成交量',
                marker_color=colors,
                opacity=0.7,
                showlegend=False,
            ),
            row=2, col=1
        )

    # 应用主题
    theme = get_plotly_theme()
    fig.update_layout(
        **theme,
        title=title,
        height=height,
        xaxis_rangeslider_visible=False,
    )

    # 更新子图 Y 轴
    if show_volume:
        fig.update_yaxes(title_text="", row=1, col=1)
        fig.update_yaxes(title_text="", row=2, col=1, showgrid=False)

    return fig


def create_dark_radar(
    categories: List[str],
    values: List[float],
    title: str = "",
    max_value: float = 100,
    fill_color: Optional[str] = None,
    height: int = 400,
) -> go.Figure:
    """
    创建深色主题雷达图

    Args:
        categories: 类别名称列表
        values: 对应数值列表
        title: 图表标题
        max_value: 最大值
        fill_color: 填充颜色
        height: 图表高度
    """
    if fill_color is None:
        fill_color = COLORS['accent_cyan']

    # 闭合多边形
    categories = categories + [categories[0]]
    values = values + [values[0]]

    fig = go.Figure()

    # 添加雷达图
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor=f'{fill_color}20',
        line=dict(color=fill_color, width=2),
        marker=dict(
            size=8,
            color=fill_color,
            line=dict(width=2, color='white'),
        ),
    ))

    # 应用主题
    theme = get_plotly_theme()
    fig.update_layout(
        **theme,
        title=title,
        height=height,
        polar=dict(
            bgcolor=COLORS['bg_secondary'],
            radialaxis=dict(
                visible=True,
                range=[0, max_value],
                gridcolor=COLORS['chart_grid'],
                linecolor=COLORS['border'],
                tickfont=dict(color=COLORS['chart_text'], size=10),
            ),
            angularaxis=dict(
                gridcolor=COLORS['chart_grid'],
                linecolor=COLORS['border'],
                tickfont=dict(color=COLORS['text_secondary'], size=11),
            ),
        ),
        showlegend=False,
    )

    return fig


def create_dark_bar(
    x: List[str],
    y: List[float],
    title: str = "",
    color: Optional[str] = None,
    horizontal: bool = False,
    height: int = 400,
) -> go.Figure:
    """
    创建深色主题柱状图
    """
    if color is None:
        color = COLORS['accent_cyan']

    fig = go.Figure()

    if horizontal:
        fig.add_trace(go.Bar(
            y=x,
            x=y,
            orientation='h',
            marker_color=color,
            marker_line_color=color,
            marker_line_width=0,
        ))
    else:
        fig.add_trace(go.Bar(
            x=x,
            y=y,
            marker_color=color,
            marker_line_color=color,
            marker_line_width=0,
        ))

    theme = get_plotly_theme()
    fig.update_layout(
        **theme,
        title=title,
        height=height,
        bargap=0.3,
    )

    return fig


def create_dark_scatter(
    x: List[float],
    y: List[float],
    colors: Optional[List[float]] = None,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    colorscale: str = "Viridis",
    height: int = 400,
) -> go.Figure:
    """
    创建深色主题散点图
    """
    fig = go.Figure()

    marker_config = dict(
        size=8,
        color=colors if colors else COLORS['accent_cyan'],
        colorscale=colorscale if colors else None,
        showscale=True if colors else False,
        line=dict(width=1, color='white'),
        opacity=0.8,
    )

    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=marker_config,
    ))

    theme = get_plotly_theme()
    fig.update_layout(
        **theme,
        title=title,
        height=height,
        xaxis_title=x_title,
        yaxis_title=y_title,
    )

    return fig


def create_dark_pie(
    labels: List[str],
    values: List[float],
    title: str = "",
    colors: Optional[List[str]] = None,
    height: int = 400,
) -> go.Figure:
    """
    创建深色主题饼图/环形图
    """
    if colors is None:
        colors = [
            COLORS['accent_cyan'],
            COLORS['accent_purple'],
            COLORS['warning'],
            COLORS['profit'],
            COLORS['loss'],
            COLORS['info'],
        ]

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,  # 环形图
        marker=dict(
            colors=colors[:len(labels)],
            line=dict(color=COLORS['bg_primary'], width=2),
        ),
        textfont=dict(color=COLORS['text_primary'], size=12),
        textposition='outside',
        textinfo='label+percent',
    ))

    theme = get_plotly_theme()
    fig.update_layout(
        **theme,
        title=title,
        height=height,
        showlegend=False,
    )

    return fig


def create_dark_histogram(
    values: List[float],
    title: str = "",
    x_title: str = "",
    nbins: int = 20,
    color: Optional[str] = None,
    height: int = 400,
) -> go.Figure:
    """
    创建深色主题直方图
    """
    if color is None:
        color = COLORS['accent_cyan']

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=values,
        nbinsx=nbins,
        marker_color=color,
        marker_line_color=COLORS['bg_primary'],
        marker_line_width=1,
        opacity=0.8,
    ))

    theme = get_plotly_theme()
    fig.update_layout(
        **theme,
        title=title,
        height=height,
        xaxis_title=x_title,
        yaxis_title="频次",
        bargap=0.1,
    )

    return fig
