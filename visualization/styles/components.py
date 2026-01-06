"""
HTML/CSS 组件库
可复用的 UI 组件函数
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from .theme import COLORS, FONTS, get_pnl_color, get_grade_color, get_strategy_color


def glow_card(
    content: str,
    variant: str = "default",
    class_name: str = ""
) -> str:
    """
    发光边框卡片

    Args:
        content: HTML 内容
        variant: 'default' | 'profit' | 'loss'
        class_name: 额外的 CSS 类
    """
    return f"""
    <div class="glow-card {variant} {class_name} fade-in">
        {content}
    </div>
    """


def metric_display(
    label: str,
    value: str,
    delta: Optional[str] = None,
    is_profit: Optional[bool] = None,
    size: str = "lg"
) -> str:
    """
    大数字指标显示

    Args:
        label: 标签文字
        value: 主要数值
        delta: 变化值（可选）
        is_profit: True=盈利(绿), False=亏损(红), None=中性
        size: 'sm' | 'md' | 'lg' | 'xl'
    """
    size_classes = {
        'sm': 'font-size: 1.25rem;',
        'md': 'font-size: 1.75rem;',
        'lg': 'font-size: 2.5rem;',
        'xl': 'font-size: 3rem;',
    }

    value_class = ""
    if is_profit is True:
        value_class = "profit"
    elif is_profit is False:
        value_class = "loss"

    delta_html = ""
    if delta:
        delta_color = COLORS['profit'] if is_profit else COLORS['loss'] if is_profit is False else COLORS['text_secondary']
        delta_html = f"""
        <div style="
            font-family: {FONTS['mono']};
            font-size: 1rem;
            color: {delta_color};
            margin-top: 0.25rem;
        ">{delta}</div>
        """

    return f"""
    <div class="fade-in" style="text-align: center;">
        <div class="metric-label">{label}</div>
        <div class="metric-value {value_class}" style="{size_classes.get(size, size_classes['lg'])}">
            {value}
        </div>
        {delta_html}
    </div>
    """


def pnl_badge(value: float, show_sign: bool = True) -> str:
    """
    盈亏徽章

    Args:
        value: 盈亏数值
        show_sign: 是否显示正负号
    """
    is_profit = value >= 0
    variant = "profit" if is_profit else "loss"
    sign = "+" if is_profit and show_sign else ""
    icon = "▲" if is_profit else "▼"

    return f"""
    <span class="pnl-badge {variant}">
        {icon} {sign}${abs(value):,.2f}
    </span>
    """


def pnl_pct_badge(value: float) -> str:
    """盈亏百分比徽章"""
    is_profit = value >= 0
    variant = "profit" if is_profit else "loss"
    sign = "+" if is_profit else ""
    icon = "▲" if is_profit else "▼"

    return f"""
    <span class="pnl-badge {variant}">
        {icon} {sign}{value:.2f}%
    </span>
    """


def grade_badge(grade: str, size: str = "md") -> str:
    """
    评分等级徽章

    Args:
        grade: 评分等级 (A+, A, B, C, D, F)
        size: 'sm' | 'md' | 'lg'
    """
    grade_letter = grade[0].upper() if grade else "?"
    grade_class = f"grade-{grade_letter.lower()}" if grade_letter in "ABCDF" else "grade-c"

    size_styles = {
        'sm': 'width: 2rem; height: 2rem; font-size: 1rem;',
        'md': 'width: 3rem; height: 3rem; font-size: 1.5rem;',
        'lg': 'width: 4rem; height: 4rem; font-size: 2rem;',
    }

    return f"""
    <span class="grade-badge {grade_class}" style="{size_styles.get(size, size_styles['md'])}">
        {grade}
    </span>
    """


def progress_ring(
    value: float,
    max_value: float = 100,
    size: int = 80,
    stroke_width: int = 8,
    color: Optional[str] = None,
    show_value: bool = True
) -> str:
    """
    环形进度条

    Args:
        value: 当前值
        max_value: 最大值
        size: SVG 尺寸
        stroke_width: 线条宽度
        color: 颜色（默认根据值自动选择）
        show_value: 是否显示数值
    """
    percentage = min(value / max_value, 1) * 100
    radius = (size - stroke_width) / 2
    circumference = 2 * 3.14159 * radius
    stroke_dashoffset = circumference * (1 - percentage / 100)

    # 自动选择颜色
    if color is None:
        if percentage >= 70:
            color = COLORS['profit']
        elif percentage >= 50:
            color = COLORS['warning']
        else:
            color = COLORS['loss']

    value_html = ""
    if show_value:
        value_html = f"""
        <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle"
              fill="{COLORS['text_primary']}"
              font-family="{FONTS['mono']}"
              font-size="{size * 0.25}px"
              font-weight="600">
            {value:.0f}
        </text>
        """

    return f"""
    <svg width="{size}" height="{size}" class="progress-ring">
        <circle
            cx="{size/2}" cy="{size/2}" r="{radius}"
            fill="none"
            stroke="{COLORS['bg_tertiary']}"
            stroke-width="{stroke_width}"
        />
        <circle
            cx="{size/2}" cy="{size/2}" r="{radius}"
            fill="none"
            stroke="{color}"
            stroke-width="{stroke_width}"
            stroke-dasharray="{circumference}"
            stroke-dashoffset="{stroke_dashoffset}"
            stroke-linecap="round"
            transform="rotate(-90 {size/2} {size/2})"
            style="transition: stroke-dashoffset 0.5s ease; filter: drop-shadow(0 0 6px {color}40);"
        />
        {value_html}
    </svg>
    """


def indicator_card(
    name: str,
    value: str,
    status: str = "",
    status_type: str = "neutral"
) -> str:
    """
    技术指标卡片

    Args:
        name: 指标名称
        value: 指标数值
        status: 状态文字
        status_type: 'bullish' | 'bearish' | 'neutral'
    """
    status_html = ""
    if status:
        status_html = f"""
        <div class="indicator-status {status_type}">{status}</div>
        """

    return f"""
    <div class="indicator-card fade-in">
        <div class="indicator-name">{name}</div>
        <div class="indicator-value">{value}</div>
        {status_html}
    </div>
    """


def section_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None
) -> str:
    """
    区域标题

    Args:
        title: 主标题
        subtitle: 副标题
        icon: emoji 或图标
    """
    icon_html = f'<span style="margin-right: 0.5rem;">{icon}</span>' if icon else ""
    subtitle_html = f"""
    <span style="
        color: {COLORS['text_secondary']};
        font-size: 0.875rem;
        font-weight: 400;
        margin-left: 0.75rem;
    ">{subtitle}</span>
    """ if subtitle else ""

    return f"""
    <div style="
        display: flex;
        align-items: baseline;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid {COLORS['border']};
    ">
        <h2 style="
            font-family: {FONTS['heading']};
            font-size: 1.25rem;
            font-weight: 600;
            color: {COLORS['text_primary']};
            margin: 0;
        ">
            {icon_html}{title}
        </h2>
        {subtitle_html}
    </div>
    """


def stat_row(items: List[Dict[str, Any]]) -> str:
    """
    统计数据行

    Args:
        items: [{'label': str, 'value': str, 'color': str (optional)}]
    """
    item_htmls = []
    for item in items:
        color = item.get('color', COLORS['text_primary'])
        item_htmls.append(f"""
        <div style="
            text-align: center;
            padding: 0 1rem;
            border-right: 1px solid {COLORS['border']};
        ">
            <div style="
                color: {COLORS['text_secondary']};
                font-size: 0.75rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.25rem;
            ">{item['label']}</div>
            <div style="
                font-family: {FONTS['mono']};
                font-size: 1.125rem;
                font-weight: 600;
                color: {color};
            ">{item['value']}</div>
        </div>
        """)

    # 移除最后一个元素的右边框
    return f"""
    <div style="
        display: flex;
        justify-content: space-around;
        align-items: center;
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1rem 0;
    ">
        {''.join(item_htmls)}
    </div>
    """


def strategy_badge(strategy_type: str, strategy_name: str) -> str:
    """策略类型徽章"""
    color = get_strategy_color(strategy_type)

    return f"""
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: {color}15;
        border: 1px solid {color};
        border-radius: 9999px;
        color: {color};
        font-weight: 600;
        font-size: 0.875rem;
    ">
        <span style="
            width: 8px;
            height: 8px;
            background: {color};
            border-radius: 50%;
            box-shadow: 0 0 8px {color};
        "></span>
        {strategy_name}
    </span>
    """


def direction_badge(direction: str, is_long: bool) -> str:
    """交易方向徽章"""
    if is_long:
        color = COLORS['profit']
        icon = "▲"
        text = "做多"
    else:
        color = COLORS['loss']
        icon = "▼"
        text = "做空"

    return f"""
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        color: {color};
        font-weight: 600;
    ">
        {icon} {text}
    </span>
    """


def date_range_display(start_date: str, end_date: str, days: int) -> str:
    """日期范围显示"""
    return f"""
    <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">
        <span style="color: {COLORS['text_primary']};">{start_date}</span>
        <span style="margin: 0 0.5rem;">→</span>
        <span style="color: {COLORS['text_primary']};">{end_date}</span>
        <span style="
            margin-left: 0.75rem;
            padding: 0.125rem 0.5rem;
            background: {COLORS['bg_tertiary']};
            border-radius: 9999px;
            font-size: 0.75rem;
        ">{days} 天</span>
    </div>
    """


def divider() -> str:
    """分隔线"""
    return '<div class="section-divider"></div>'


# ============================================================
# Streamlit 便捷函数
# ============================================================

def render_html(html: str):
    """渲染 HTML 到 Streamlit"""
    st.markdown(html, unsafe_allow_html=True)


def render_metric_row(metrics: List[Dict[str, Any]]):
    """
    渲染一行指标

    Args:
        metrics: [{'label': str, 'value': str, 'delta': str, 'is_profit': bool}]
    """
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            render_html(metric_display(
                label=metric.get('label', ''),
                value=metric.get('value', ''),
                delta=metric.get('delta'),
                is_profit=metric.get('is_profit'),
                size=metric.get('size', 'md')
            ))


def render_indicator_row(indicators: List[Dict[str, Any]]):
    """
    渲染一行指标卡片

    Args:
        indicators: [{'name': str, 'value': str, 'status': str, 'status_type': str}]
    """
    cols = st.columns(len(indicators))
    for i, ind in enumerate(indicators):
        with cols[i]:
            render_html(indicator_card(
                name=ind.get('name', ''),
                value=ind.get('value', ''),
                status=ind.get('status', ''),
                status_type=ind.get('status_type', 'neutral')
            ))


def render_progress_rings(scores: List[Dict[str, Any]]):
    """
    渲染一行环形进度条

    Args:
        scores: [{'label': str, 'value': float, 'color': str (optional)}]
    """
    cols = st.columns(len(scores))
    for i, score in enumerate(scores):
        with cols[i]:
            html = f"""
            <div style="text-align: center;">
                <div style="
                    color: {COLORS['text_secondary']};
                    font-size: 0.75rem;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 0.5rem;
                ">{score['label']}</div>
                {progress_ring(
                    value=score['value'],
                    size=80,
                    color=score.get('color')
                )}
            </div>
            """
            render_html(html)
