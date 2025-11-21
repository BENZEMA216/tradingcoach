"""
Metrics Components
指标卡片组件

提供各种指标展示卡片。
"""

import streamlit as st
from typing import Any, Optional


def metric_card(label: str, value: Any, delta: Optional[Any] = None,
               delta_color: str = "normal", help_text: Optional[str] = None):
    """
    创建指标卡片

    Args:
        label: 标签
        value: 值
        delta: 变化量（可选）
        delta_color: 变化量颜色 ("normal", "inverse", "off")
        help_text: 帮助文本（可选）
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def stats_card(title: str, stats: dict, columns: int = 4):
    """
    创建统计卡片组

    Args:
        title: 标题
        stats: 统计数据字典 {label: value}
        columns: 列数
    """
    st.subheader(title)
    cols = st.columns(columns)

    for i, (label, value) in enumerate(stats.items()):
        with cols[i % columns]:
            st.metric(label=label, value=value)


def grade_badge(grade: str) -> str:
    """
    返回评分等级徽章的 HTML

    Args:
        grade: 等级 (A+, A, A-, B+, B, B-, C+, C, C-, D, F)

    Returns:
        HTML 字符串
    """
    # 定义等级颜色
    grade_colors = {
        'A+': '#00C851', 'A': '#00C851', 'A-': '#2BBBAD',
        'B+': '#4285F4', 'B': '#4285F4', 'B-': '#4285F4',
        'C+': '#FFA000', 'C': '#FFA000', 'C-': '#FFA000',
        'D': '#FF3547', 'F': '#CC0000'
    }

    color = grade_colors.get(grade, '#999999')

    return f'''
    <span style="
        background-color: {color};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 14px;
    ">{grade}</span>
    '''


def pnl_badge(pnl: float) -> str:
    """
    返回盈亏徽章的 HTML

    Args:
        pnl: 盈亏金额

    Returns:
        HTML 字符串
    """
    color = '#00C851' if pnl >= 0 else '#FF3547'
    symbol = '+' if pnl >= 0 else ''

    return f'''
    <span style="
        color: {color};
        font-weight: bold;
        font-size: 16px;
    ">{symbol}${pnl:,.2f}</span>
    '''


def percentage_badge(pct: float) -> str:
    """
    返回百分比徽章的 HTML

    Args:
        pct: 百分比

    Returns:
        HTML 字符串
    """
    color = '#00C851' if pct >= 0 else '#FF3547'
    symbol = '+' if pct >= 0 else ''

    return f'''
    <span style="
        color: {color};
        font-weight: bold;
    ">{symbol}{pct:.2f}%</span>
    '''


def status_badge(status: str) -> str:
    """
    返回状态徽章的 HTML

    Args:
        status: 状态 ("通过", "失败", "警告" 等)

    Returns:
        HTML 字符串
    """
    status_colors = {
        '通过': '#00C851',
        '✓': '#00C851',
        '失败': '#FF3547',
        '✗': '#FF3547',
        '警告': '#FFA000',
        '⚠': '#FFA000',
        '缺失': '#999999'
    }

    color = status_colors.get(status, '#4285F4')

    return f'''
    <span style="
        background-color: {color};
        color: white;
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 12px;
    ">{status}</span>
    '''


def coverage_bar(has_data: bool, width: int = 100) -> str:
    """
    返回数据覆盖率进度条的 HTML

    Args:
        has_data: 是否有数据
        width: 宽度（像素）

    Returns:
        HTML 字符串
    """
    color = '#00C851' if has_data else '#FF3547'
    text = '✓' if has_data else '✗'

    return f'''
    <div style="
        width: {width}px;
        height: 20px;
        background-color: {color};
        border-radius: 4px;
        text-align: center;
        color: white;
        line-height: 20px;
        font-weight: bold;
    ">{text}</div>
    '''


def dimension_scores_table(entry: float, exit: float, trend: float, risk: float) -> str:
    """
    返回四维度评分表格的 HTML

    Args:
        entry: 进场质量
        exit: 出场质量
        trend: 趋势质量
        risk: 风险管理

    Returns:
        HTML 字符串
    """
    def score_color(score: float) -> str:
        if score >= 80:
            return '#00C851'
        elif score >= 60:
            return '#4285F4'
        elif score >= 40:
            return '#FFA000'
        else:
            return '#FF3547'

    return f'''
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">进场质量 (30%)</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">
                <span style="color: {score_color(entry)}; font-weight: bold;">{entry:.1f}</span>
            </td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">出场质量 (25%)</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">
                <span style="color: {score_color(exit)}; font-weight: bold;">{exit:.1f}</span>
            </td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">趋势质量 (25%)</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">
                <span style="color: {score_color(trend)}; font-weight: bold;">{trend:.1f}</span>
            </td>
        </tr>
        <tr>
            <td style="padding: 8px;">风险管理 (20%)</td>
            <td style="padding: 8px; text-align: right;">
                <span style="color: {score_color(risk)}; font-weight: bold;">{risk:.1f}</span>
            </td>
        </tr>
    </table>
    '''
