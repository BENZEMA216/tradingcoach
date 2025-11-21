"""
Chart Components
图表组件库

提供各种可复用的 Plotly 图表组件。
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Optional


def create_score_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """创建评分分布直方图"""
    fig = px.histogram(
        df,
        x='overall_score',
        nbins=20,
        title='质量评分分布',
        labels={'overall_score': '总体评分', 'count': '数量'},
        color_discrete_sequence=['#1f77b4']
    )

    fig.update_layout(
        xaxis_title='总体评分',
        yaxis_title='持仓数量',
        showlegend=False,
        height=400
    )

    return fig


def create_grade_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """创建等级分布饼图"""
    grade_counts = df['grade'].value_counts().sort_index()

    # 定义等级颜色
    grade_colors = {
        'A+': '#00C851', 'A': '#00C851', 'A-': '#2BBBAD',
        'B+': '#4285F4', 'B': '#4285F4', 'B-': '#4285F4',
        'C+': '#FFA000', 'C': '#FFA000', 'C-': '#FFA000',
        'D': '#FF3547', 'F': '#CC0000'
    }

    colors = [grade_colors.get(grade, '#999999') for grade in grade_counts.index]

    fig = go.Figure(data=[go.Pie(
        labels=grade_counts.index,
        values=grade_counts.values,
        marker=dict(colors=colors),
        textinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title='评分等级分布',
        height=400
    )

    return fig


def create_dimension_radar_chart(df: pd.DataFrame) -> go.Figure:
    """创建四维度雷达图"""
    dimensions = ['entry_score', 'exit_score', 'trend_score', 'risk_score']
    labels = ['进场质量', '出场质量', '趋势质量', '风险管理']

    avg_scores = [df[dim].mean() for dim in dimensions]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=avg_scores + [avg_scores[0]],  # 闭合图形
        theta=labels + [labels[0]],
        fill='toself',
        name='平均分',
        line=dict(color='#1f77b4')
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        title='四维度平均评分',
        height=400
    )

    return fig


def create_pnl_vs_score_scatter(df: pd.DataFrame) -> go.Figure:
    """创建盈亏率 vs 评分散点图"""
    fig = px.scatter(
        df,
        x='overall_score',
        y='net_pnl_pct',
        color='grade',
        hover_data=['symbol', 'net_pnl'],
        title='盈亏率 vs 质量评分',
        labels={
            'overall_score': '总体评分',
            'net_pnl_pct': '净盈亏率 (%)',
            'grade': '等级'
        }
    )

    # 添加零线
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(height=500)

    return fig


def create_candlestick_chart(df: pd.DataFrame,
                             trades: Optional[List] = None,
                             show_ma: bool = True,
                             show_bb: bool = False) -> go.Figure:
    """创建K线图"""
    # 创建子图
    if 'rsi' in df.columns and df['rsi'].notna().any():
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=('价格', 'RSI', 'MACD')
        )
    else:
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=('价格',)
        )

    # K线图
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='价格'
        ),
        row=1, col=1
    )

    # 移动平均线
    if show_ma:
        if 'ma_5' in df.columns and df['ma_5'].notna().any():
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['ma_5'], name='MA5',
                          line=dict(color='orange', width=1)),
                row=1, col=1
            )
        if 'ma_20' in df.columns and df['ma_20'].notna().any():
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['ma_20'], name='MA20',
                          line=dict(color='blue', width=1)),
                row=1, col=1
            )
        if 'ma_50' in df.columns and df['ma_50'].notna().any():
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['ma_50'], name='MA50',
                          line=dict(color='purple', width=1)),
                row=1, col=1
            )

    # 布林带
    if show_bb and 'bb_upper' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['bb_upper'], name='BB Upper',
                      line=dict(color='gray', width=1, dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['bb_middle'], name='BB Middle',
                      line=dict(color='gray', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['bb_lower'], name='BB Lower',
                      line=dict(color='gray', width=1, dash='dash')),
            row=1, col=1
        )

    # 标注交易点位
    if trades:
        buy_dates = []
        buy_prices = []
        sell_dates = []
        sell_prices = []

        for trade in trades:
            date = trade.filled_time
            price = float(trade.filled_price)
            is_buy = trade.direction.value in ['buy', 'buy_to_open']

            if is_buy:
                buy_dates.append(date)
                buy_prices.append(price)
            else:
                sell_dates.append(date)
                sell_prices.append(price)

        if buy_dates:
            fig.add_trace(
                go.Scatter(
                    x=buy_dates, y=buy_prices,
                    mode='markers',
                    name='买入',
                    marker=dict(symbol='triangle-up', size=10, color='green')
                ),
                row=1, col=1
            )

        if sell_dates:
            fig.add_trace(
                go.Scatter(
                    x=sell_dates, y=sell_prices,
                    mode='markers',
                    name='卖出',
                    marker=dict(symbol='triangle-down', size=10, color='red')
                ),
                row=1, col=1
            )

    # RSI 子图
    if 'rsi' in df.columns and df['rsi'].notna().any():
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['rsi'], name='RSI',
                      line=dict(color='purple', width=2)),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red",
                     opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green",
                     opacity=0.5, row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)

    # MACD 子图
    if 'macd' in df.columns and df['macd'].notna().any():
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['macd'], name='MACD',
                      line=dict(color='blue', width=2)),
            row=3, col=1
        )
        if 'macd_signal' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['macd_signal'], name='Signal',
                          line=dict(color='orange', width=2)),
                row=3, col=1
            )
        if 'macd_hist' in df.columns:
            colors = ['green' if val >= 0 else 'red' for val in df['macd_hist']]
            fig.add_trace(
                go.Bar(x=df['date'], y=df['macd_hist'], name='Histogram',
                      marker=dict(color=colors)),
                row=3, col=1
            )
        fig.update_yaxes(title_text="MACD", row=3, col=1)

    fig.update_layout(
        height=800,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )

    return fig


def create_fifo_timeline_chart(trades: List, positions: List) -> go.Figure:
    """创建 FIFO 匹配时间轴"""
    fig = go.Figure()

    # 买入交易
    buy_trades = [t for t in trades if t.direction.value in ['buy', 'buy_to_open']]
    sell_trades = [t for t in trades if t.direction.value in ['sell', 'sell_to_close']]

    # 添加买入点
    if buy_trades:
        fig.add_trace(go.Scatter(
            x=[t.filled_time for t in buy_trades],
            y=[float(t.filled_price) for t in buy_trades],
            mode='markers+text',
            name='买入',
            marker=dict(symbol='triangle-up', size=12, color='green'),
            text=[f'+{t.filled_quantity}' for t in buy_trades],
            textposition='top center'
        ))

    # 添加卖出点
    if sell_trades:
        fig.add_trace(go.Scatter(
            x=[t.filled_time for t in sell_trades],
            y=[float(t.filled_price) for t in sell_trades],
            mode='markers+text',
            name='卖出',
            marker=dict(symbol='triangle-down', size=12, color='red'),
            text=[f'-{t.filled_quantity}' for t in sell_trades],
            textposition='bottom center'
        ))

    fig.update_layout(
        title='交易时间轴',
        xaxis_title='时间',
        yaxis_title='价格',
        height=400,
        hovermode='closest'
    )

    return fig


def create_score_trend_chart(df: pd.DataFrame) -> go.Figure:
    """创建评分趋势图（按时间）"""
    df_sorted = df.sort_values('open_time')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_sorted['open_time'],
        y=df_sorted['overall_score'],
        mode='lines+markers',
        name='总体评分',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))

    # 添加移动平均线
    if len(df_sorted) > 5:
        df_sorted['ma'] = df_sorted['overall_score'].rolling(window=5).mean()
        fig.add_trace(go.Scatter(
            x=df_sorted['open_time'],
            y=df_sorted['ma'],
            mode='lines',
            name='5期移动平均',
            line=dict(color='red', width=2, dash='dash')
        ))

    fig.update_layout(
        title='质量评分趋势（按开仓时间）',
        xaxis_title='开仓时间',
        yaxis_title='质量评分',
        height=400,
        hovermode='x unified'
    )

    return fig
