#!/usr/bin/env python3
"""
System Health - 系统状态
数据覆盖率和系统健康检查

核心功能:
- 数据覆盖率检查
- FIFO配对验证
- 缺失数据列表
- 系统统计
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 页面配置
st.set_page_config(
    page_title="系统状态 - Trading Coach",
    page_icon="⚙️",
    layout="wide"
)

# 导入样式系统
from visualization.styles import inject_global_css, COLORS, FONTS
inject_global_css()

# 导入数据层
from visualization.utils.data_loader import get_data_loader
from src.models.base import get_session
from src.models.position import Position, PositionStatus
from src.models.trade import Trade
from src.models.market_data import MarketData


def render_metric_card(title: str, value: str, subtitle: str = "", color: str = None, icon: str = ""):
    """渲染指标卡片"""
    if color is None:
        color = COLORS['text_primary']

    st.markdown(f"""
    <div style="
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    ">
        <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{icon}</div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.75rem; text-transform: uppercase;">{title}</div>
        <div style="color: {color}; font-size: 1.75rem; font-weight: 700; font-family: {FONTS['mono']}; margin: 0.25rem 0;">{value}</div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.7rem;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def get_data_statistics():
    """获取数据统计"""
    session = get_session()
    try:
        # 交易统计
        total_trades = session.query(Trade).count()

        # 持仓统计
        total_positions = session.query(Position).count()
        closed_positions = session.query(Position).filter(Position.status == PositionStatus.CLOSED).count()
        open_positions = session.query(Position).filter(Position.status == PositionStatus.OPEN).count()

        # 评分统计
        scored_positions = session.query(Position).filter(
            Position.overall_score.isnot(None)
        ).count()

        # 市场数据统计
        total_market_data = session.query(MarketData).count()
        unique_symbols = session.query(MarketData.symbol).distinct().count()

        # 计算评分覆盖率
        score_coverage = (scored_positions / closed_positions * 100) if closed_positions > 0 else 0

        return {
            'total_trades': total_trades,
            'total_positions': total_positions,
            'closed_positions': closed_positions,
            'open_positions': open_positions,
            'scored_positions': scored_positions,
            'score_coverage': score_coverage,
            'total_market_data': total_market_data,
            'unique_symbols': unique_symbols,
        }
    finally:
        session.close()


def get_missing_data_summary():
    """获取缺失数据汇总"""
    session = get_session()
    try:
        # 找出缺少市场数据的持仓
        positions = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        missing_market_data = []
        missing_scores = []

        for pos in positions:
            # 检查市场数据
            market_data = session.query(MarketData).filter(
                MarketData.symbol == pos.symbol,
                MarketData.date >= pos.open_date,
                MarketData.date <= pos.close_date
            ).first()

            if not market_data:
                missing_market_data.append({
                    'symbol': pos.symbol,
                    'open_date': pos.open_date,
                    'close_date': pos.close_date,
                })

            # 检查评分
            if pos.overall_score is None:
                missing_scores.append({
                    'id': pos.id,
                    'symbol': pos.symbol,
                    'close_date': pos.close_date,
                })

        return {
            'missing_market_data': missing_market_data,
            'missing_scores': missing_scores,
        }
    finally:
        session.close()


def render_fifo_validation():
    """渲染FIFO验证"""
    session = get_session()
    try:
        # 获取所有已平仓持仓
        positions = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        issues = []

        for pos in positions:
            # 通过 trades relationship 检查买入和卖出交易
            buy_trades = [t for t in pos.trades if t.direction == '买入']
            sell_trades = [t for t in pos.trades if t.direction == '卖出']

            if not buy_trades or not sell_trades:
                issues.append({
                    'id': pos.id,
                    'symbol': pos.symbol,
                    'issue': '缺少买入或卖出交易记录',
                })
                continue

            # 检查盈亏计算
            if pos.realized_pnl is None or pos.net_pnl is None:
                issues.append({
                    'id': pos.id,
                    'symbol': pos.symbol,
                    'issue': '盈亏未计算',
                })

        return issues

    finally:
        session.close()


def main():
    """主函数"""
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
            ">⚙️ 系统状态</div>
            <div style="
                color: {COLORS['text_secondary']};
                font-size: 0.85rem;
            ">数据覆盖率和系统健康检查</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ================================================================
    # 数据统计
    # ================================================================
    st.markdown(f"""
    <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
        📊 数据概览
    </div>
    """, unsafe_allow_html=True)

    stats = get_data_statistics()

    cols = st.columns(4)

    with cols[0]:
        render_metric_card(
            "总交易记录",
            f"{stats['total_trades']:,}",
            "原始交易数据",
            icon="📝"
        )

    with cols[1]:
        render_metric_card(
            "持仓配对",
            f"{stats['closed_positions']:,}",
            f"共 {stats['total_positions']:,} 个持仓",
            icon="🔗"
        )

    with cols[2]:
        coverage_color = COLORS['profit'] if stats['score_coverage'] >= 90 else COLORS['warning'] if stats['score_coverage'] >= 70 else COLORS['loss']
        render_metric_card(
            "评分覆盖率",
            f"{stats['score_coverage']:.1f}%",
            f"{stats['scored_positions']:,} 已评分",
            color=coverage_color,
            icon="⭐"
        )

    with cols[3]:
        render_metric_card(
            "市场数据",
            f"{stats['total_market_data']:,}",
            f"{stats['unique_symbols']} 只股票",
            icon="📈"
        )

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ================================================================
    # 健康检查
    # ================================================================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
            🔍 FIFO配对验证
        </div>
        """, unsafe_allow_html=True)

        fifo_issues = render_fifo_validation()

        if not fifo_issues:
            st.success("✅ 所有持仓配对正常")
        else:
            st.warning(f"⚠️ 发现 {len(fifo_issues)} 个配对问题")

            for issue in fifo_issues[:10]:
                st.markdown(f"""
                <div style="
                    background: {COLORS['bg_secondary']};
                    border-left: 3px solid {COLORS['warning']};
                    border-radius: 0 8px 8px 0;
                    padding: 0.5rem 0.75rem;
                    margin-bottom: 0.5rem;
                    font-size: 0.85rem;
                ">
                    <span style="color: {COLORS['text_primary']}; font-family: {FONTS['mono']};">{issue['symbol']}</span>
                    <span style="color: {COLORS['text_muted']}; margin-left: 0.5rem;">ID: {issue['id']}</span>
                    <br>
                    <span style="color: {COLORS['warning']}; font-size: 0.8rem;">{issue['issue']}</span>
                </div>
                """, unsafe_allow_html=True)

            if len(fifo_issues) > 10:
                st.markdown(f"<div style='color: {COLORS['text_muted']}; font-size: 0.8rem;'>...还有 {len(fifo_issues) - 10} 个问题</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
            📉 缺失数据
        </div>
        """, unsafe_allow_html=True)

        missing = get_missing_data_summary()

        # 缺失市场数据
        if not missing['missing_market_data']:
            st.success("✅ 所有持仓都有对应的市场数据")
        else:
            st.warning(f"⚠️ {len(missing['missing_market_data'])} 个持仓缺少市场数据")

            # 按symbol分组
            symbols = set(item['symbol'] for item in missing['missing_market_data'])

            for symbol in list(symbols)[:5]:
                count = len([m for m in missing['missing_market_data'] if m['symbol'] == symbol])
                st.markdown(f"""
                <div style="
                    background: {COLORS['bg_secondary']};
                    border-radius: 6px;
                    padding: 0.5rem 0.75rem;
                    margin-bottom: 0.25rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <span style="color: {COLORS['text_primary']}; font-family: {FONTS['mono']};">{symbol}</span>
                    <span style="color: {COLORS['text_muted']}; font-size: 0.8rem;">{count} 条缺失</span>
                </div>
                """, unsafe_allow_html=True)

            if len(symbols) > 5:
                st.markdown(f"<div style='color: {COLORS['text_muted']}; font-size: 0.8rem;'>...还有 {len(symbols) - 5} 只股票</div>", unsafe_allow_html=True)

        # 缺失评分
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        if not missing['missing_scores']:
            st.success("✅ 所有持仓都已评分")
        else:
            st.info(f"ℹ️ {len(missing['missing_scores'])} 个持仓未评分")

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ================================================================
    # 快捷操作
    # ================================================================
    st.markdown(f"""
    <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
        🛠️ 快捷操作
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)

    with cols[0]:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 1rem;
        ">
            <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.5rem;">重新计算评分</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-bottom: 0.75rem;">
                运行评分脚本更新所有持仓评分
            </div>
            <code style="
                background: {COLORS['bg_tertiary']};
                color: {COLORS['accent_cyan']};
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
            ">python3 scripts/score_positions.py --all</code>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 1rem;
        ">
            <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.5rem;">补充市场数据</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-bottom: 0.75rem;">
                下载缺失的历史价格数据
            </div>
            <code style="
                background: {COLORS['bg_tertiary']};
                color: {COLORS['accent_cyan']};
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
            ">python3 scripts/supplement_data.py</code>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 1rem;
        ">
            <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.5rem;">计算技术指标</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-bottom: 0.75rem;">
                为市场数据计算技术指标
            </div>
            <code style="
                background: {COLORS['bg_tertiary']};
                color: {COLORS['accent_cyan']};
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
            ">python3 scripts/calculate_indicators.py</code>
        </div>
        """, unsafe_allow_html=True)

    with cols[3]:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 1rem;
        ">
            <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.5rem;">离场后分析</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-bottom: 0.75rem;">
                计算离场后5/10/20日收益
            </div>
            <code style="
                background: {COLORS['bg_tertiary']};
                color: {COLORS['accent_cyan']};
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
            ">python3 scripts/calculate_post_exit.py</code>
        </div>
        """, unsafe_allow_html=True)

    # ================================================================
    # 刷新按钮
    # ================================================================
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    if st.button("🔄 刷新数据", type="primary"):
        st.cache_data.clear()
        st.rerun()

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
        最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
