"""
MetricCard - KPI 卡片组件

用于 Dashboard 顶部的关键指标显示
"""

import streamlit as st
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from visualization.styles import COLORS, FONTS


def metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_type: str = 'auto',  # 'auto', 'profit', 'loss', 'neutral'
    icon: Optional[str] = None,
    sublabel: Optional[str] = None,
    size: str = 'md',  # 'sm', 'md', 'lg'
) -> str:
    """
    生成 KPI 卡片的 HTML

    Args:
        label: 指标名称 ("Total P&L", "Win Rate")
        value: 格式化后的值 ("$12,345", "67.3%")
        delta: 变化指示器 ("+5.2% from last month")
        delta_type: 变化颜色类型
        icon: 可选的 emoji 图标
        sublabel: 副标签
        size: 卡片大小

    Returns:
        HTML 字符串
    """
    # 大小配置
    size_config = {
        'sm': {'value_size': '1.5rem', 'padding': '1rem'},
        'md': {'value_size': '2rem', 'padding': '1.25rem'},
        'lg': {'value_size': '2.5rem', 'padding': '1.5rem'},
    }
    config = size_config.get(size, size_config['md'])

    # Delta 颜色
    delta_color = COLORS['text_secondary']
    delta_icon = ""
    if delta:
        if delta_type == 'auto':
            if delta.startswith('+') or delta.startswith('▲'):
                delta_color = COLORS['profit']
                delta_icon = "▲ " if not delta.startswith('▲') else ""
            elif delta.startswith('-') or delta.startswith('▼'):
                delta_color = COLORS['loss']
                delta_icon = "▼ " if not delta.startswith('▼') else ""
        elif delta_type == 'profit':
            delta_color = COLORS['profit']
            delta_icon = "▲ "
        elif delta_type == 'loss':
            delta_color = COLORS['loss']
            delta_icon = "▼ "

    # 图标 HTML
    icon_html = f'<span style="margin-right: 0.5rem;">{icon}</span>' if icon else ''

    # 副标签 HTML (单行样式)
    sublabel_style = f"color: {COLORS['text_muted']}; font-size: 0.75rem; margin-top: 0.25rem;"
    sublabel_html = f'<div style="{sublabel_style}">{sublabel}</div>' if sublabel else ''

    # Delta HTML (单行样式)
    delta_style = f"display: flex; align-items: center; gap: 0.25rem; color: {delta_color}; font-size: 0.875rem; font-family: {FONTS['mono']}; margin-top: 0.5rem;"
    delta_html = f'<div style="{delta_style}">{delta_icon}{delta}</div>' if delta else ''

    # 主容器样式 (单行)
    container_style = f"background: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px; padding: {config['padding']}; height: 100%; transition: all 0.2s ease;"

    # 标签样式 (单行)
    label_style = f"color: {COLORS['text_secondary']}; font-size: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;"

    # 值样式 (单行)
    value_style = f"font-family: {FONTS['mono']}; font-size: {config['value_size']}; font-weight: 700; color: {COLORS['text_primary']}; line-height: 1.2;"

    return f'''<div style="{container_style}" class="metric-card-hover">
<div style="{label_style}">{icon_html}{label}</div>
<div style="{value_style}">{value}</div>
{sublabel_html}{delta_html}
</div>'''


def render_metric_row(metrics: List[Dict[str, Any]]) -> None:
    """
    渲染一行指标卡片

    Args:
        metrics: 指标列表，每个元素包含:
            - label: 标签
            - value: 值
            - delta: 变化 (可选)
            - delta_type: 变化类型 (可选)
            - icon: 图标 (可选)
    """
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            st.markdown(
                metric_card(
                    label=metric.get('label', ''),
                    value=metric.get('value', ''),
                    delta=metric.get('delta'),
                    delta_type=metric.get('delta_type', 'auto'),
                    icon=metric.get('icon'),
                    sublabel=metric.get('sublabel'),
                    size=metric.get('size', 'md'),
                ),
                unsafe_allow_html=True
            )


def render_kpi_cards(
    total_pnl: float,
    win_rate: float,
    avg_score: float,
    trade_count: int,
    prev_period_pnl: Optional[float] = None,
    prev_period_win_rate: Optional[float] = None,
) -> None:
    """
    渲染 Dashboard 顶部的 4 个 KPI 卡片

    Args:
        total_pnl: 总盈亏
        win_rate: 胜率 (0-100)
        avg_score: 平均评分 (0-100)
        trade_count: 交易数量
        prev_period_pnl: 上期盈亏 (用于计算变化)
        prev_period_win_rate: 上期胜率
    """
    # 计算 delta
    pnl_delta = None
    if prev_period_pnl is not None and prev_period_pnl != 0:
        pnl_change = ((total_pnl - prev_period_pnl) / abs(prev_period_pnl)) * 100
        pnl_delta = f"{'+' if pnl_change >= 0 else ''}{pnl_change:.1f}% vs 上期"

    win_rate_delta = None
    if prev_period_win_rate is not None:
        wr_change = win_rate - prev_period_win_rate
        win_rate_delta = f"{'+' if wr_change >= 0 else ''}{wr_change:.1f}%"

    # 评分等级
    if avg_score >= 80:
        score_grade = "A"
        score_color = COLORS['grade_a']
    elif avg_score >= 70:
        score_grade = "B"
        score_color = COLORS['grade_b']
    elif avg_score >= 60:
        score_grade = "C"
        score_color = COLORS['grade_c']
    elif avg_score >= 50:
        score_grade = "D"
        score_color = COLORS['grade_d']
    else:
        score_grade = "F"
        score_color = COLORS['grade_f']

    # PnL 颜色
    pnl_color = COLORS['profit'] if total_pnl >= 0 else COLORS['loss']
    pnl_sign = '+' if total_pnl >= 0 else ''

    metrics = [
        {
            'label': 'Total P&L',
            'value': f'{pnl_sign}${total_pnl:,.2f}',
            'delta': pnl_delta,
            'delta_type': 'profit' if total_pnl >= 0 else 'loss',
        },
        {
            'label': 'Win Rate',
            'value': f'{win_rate:.1f}%',
            'delta': win_rate_delta,
            'delta_type': 'auto',
        },
        {
            'label': 'Avg Score',
            'value': f'{avg_score:.0f}',
            'sublabel': f'Grade: {score_grade}',
        },
        {
            'label': 'Trades',
            'value': f'{trade_count}',
            'sublabel': 'Closed positions',
        },
    ]

    render_metric_row(metrics)


# 添加 hover 效果的 CSS
METRIC_CARD_CSS = f'''
<style>
.metric-card-hover:hover {{
    border-color: {COLORS['accent_cyan']}40 !important;
    box-shadow: 0 0 20px {COLORS['accent_cyan']}10;
}}
</style>
'''
