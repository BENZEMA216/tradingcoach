#!/usr/bin/env python3
"""
Position Analyzer - 持仓分析器
深度单笔交易分析，TradingView风格

核心功能:
- TradingView风格增强K线图 (含MAE/MFE)
- 入场/出场指标对比
- 四维评分环形图
- 离场后走势分析
- 上一笔/下一笔快速导航
- 复盘笔记保存
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 页面配置
st.set_page_config(
    page_title="持仓分析 - Trading Coach",
    page_icon="🔍",
    layout="wide"
)

# 导入样式系统
from visualization.styles import (
    inject_global_css, COLORS, FONTS,
    indicator_card, section_header, render_html, render_progress_rings,
)
inject_global_css()

# 导入组件
from visualization.components.charts import create_enhanced_candlestick
from visualization.components.core import STRATEGY_NAMES, GRADE_COLORS

# 导入数据层
from visualization.utils.data_loader import DataLoader
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.models.base import get_session
from src.analyzers.strategy_classifier import StrategyClassifier
from src.utils.option_parser import OptionParser
from config import (
    RSI_OVERSOLD, RSI_OVERBOUGHT,
    STOCH_OVERSOLD, STOCH_OVERBOUGHT,
    ADX_WEAK_TREND, ADX_MODERATE_TREND, ADX_STRONG_TREND
)


@st.cache_resource
def get_data_loader():
    return DataLoader()


def get_indicator_status(name: str, value: float) -> tuple:
    """获取指标状态和类型"""
    if name == 'RSI':
        if value < RSI_OVERSOLD:
            return "超卖", "bullish"
        elif value > RSI_OVERBOUGHT:
            return "超买", "bearish"
        else:
            return "中性", "neutral"
    elif name == 'Stoch':
        if value < STOCH_OVERSOLD:
            return "超卖", "bullish"
        elif value > STOCH_OVERBOUGHT:
            return "超买", "bearish"
        else:
            return "中性", "neutral"
    elif name == 'ADX':
        if value >= ADX_STRONG_TREND:
            return "强趋势", "bullish"
        elif value >= ADX_MODERATE_TREND:
            return "中等趋势", "neutral"
        elif value >= ADX_WEAK_TREND:
            return "弱趋势", "neutral"
        else:
            return "无趋势", "bearish"
    return "", "neutral"


def render_hero_section(position: Position):
    """渲染顶部概览区 - 简化版"""
    is_long = position.direction in ['long', 'buy', 'buy_to_open']
    net_pnl = float(position.net_pnl) if position.net_pnl else 0
    net_pnl_pct = float(position.net_pnl_pct) if position.net_pnl_pct else 0
    is_profit = net_pnl >= 0

    # 格式化日期
    open_date_str = position.open_date.strftime('%Y.%m.%d') if position.open_date else '-'
    close_date_str = position.close_date.strftime('%Y.%m.%d') if position.close_date else '-'
    holding_days = position.holding_period_days or 0

    # PnL 颜色和图标
    pnl_color = COLORS['profit'] if is_profit else COLORS['loss']
    pnl_sign = "+" if is_profit else ""

    # 策略信息
    strategy_type = position.strategy_type or "unknown"
    strategy_name = STRATEGY_NAMES.get(strategy_type, strategy_type)
    strategy_color = {
        'trend': COLORS.get('strategy_trend', '#4CAF50'),
        'mean_reversion': COLORS.get('strategy_reversion', '#2196F3'),
        'breakout': COLORS.get('strategy_breakout', '#FF9800'),
        'range': COLORS.get('strategy_range', '#9C27B0'),
        'momentum': COLORS.get('strategy_momentum', '#E91E63'),
    }.get(strategy_type, COLORS['neutral'])

    # 等级
    grade = position.score_grade or "-"
    grade_color = GRADE_COLORS.get(grade[0] if grade else 'C', COLORS['neutral'])

    # 三列布局
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 1rem;
        ">
            <div style="
                font-family: {FONTS['mono']};
                font-size: 2rem;
                font-weight: 700;
                color: {COLORS['text_primary']};
            ">{position.symbol}</div>
            <span style="
                color: {'#00FF88' if is_long else '#FF3B5C'};
                font-weight: 600;
                padding: 0.25rem 0.75rem;
                background: {'#00FF88' if is_long else '#FF3B5C'}15;
                border-radius: 6px;
            ">{'▲ 做多' if is_long else '▼ 做空'}</span>
        </div>
        <div style="
            color: {COLORS['text_secondary']};
            font-size: 0.85rem;
            margin-top: 0.5rem;
        ">
            {open_date_str} → {close_date_str}
            <span style="
                margin-left: 0.75rem;
                padding: 0.125rem 0.5rem;
                background: {COLORS['bg_tertiary']};
                border-radius: 4px;
                font-size: 0.75rem;
            ">{holding_days} 天</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="
                font-family: {FONTS['mono']};
                font-size: 2.5rem;
                font-weight: 700;
                color: {pnl_color};
            ">{pnl_sign}${abs(net_pnl):,.2f}</div>
            <div style="
                color: {pnl_color};
                font-size: 1rem;
                font-family: {FONTS['mono']};
            ">{pnl_sign}{net_pnl_pct:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="text-align: right;">
            <div style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 3rem;
                height: 3rem;
                background: {grade_color}15;
                border: 2px solid {grade_color};
                border-radius: 10px;
                font-family: {FONTS['mono']};
                font-size: 1.5rem;
                font-weight: 700;
                color: {grade_color};
            ">{grade}</div>
            <div style="
                margin-top: 0.5rem;
            ">
                <span style="
                    padding: 0.25rem 0.5rem;
                    background: {strategy_color}15;
                    border: 1px solid {strategy_color};
                    border-radius: 4px;
                    color: {strategy_color};
                    font-size: 0.75rem;
                    font-weight: 600;
                ">{strategy_name}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_metrics_row(position: Position):
    """渲染指标行"""
    open_price = float(position.open_price) if position.open_price else 0
    close_price = float(position.close_price) if position.close_price else 0
    quantity = position.quantity or 0
    mae_pct = float(position.mae_pct) if position.mae_pct else 0
    mfe_pct = float(position.mfe_pct) if position.mfe_pct else 0

    cols = st.columns(5)

    metrics = [
        ("开仓价", f"${open_price:.2f}", COLORS['text_primary']),
        ("平仓价", f"${close_price:.2f}", COLORS['text_primary']),
        ("数量", f"{quantity:,}", COLORS['text_primary']),
        ("MAE", f"{mae_pct:.2f}%", COLORS['loss']),
        ("MFE", f"{mfe_pct:.2f}%", COLORS['profit']),
    ]

    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 0.75rem;
                text-align: center;
            ">
                <div style="color: {COLORS['text_muted']}; font-size: 0.7rem; text-transform: uppercase;">{label}</div>
                <div style="font-family: {FONTS['mono']}; font-size: 1.1rem; font-weight: 600; color: {color}; margin-top: 0.25rem;">{value}</div>
            </div>
            """, unsafe_allow_html=True)


def render_kline_chart(position: Position):
    """渲染增强K线图"""
    symbol = position.symbol
    if OptionParser.is_option_symbol(symbol):
        symbol = OptionParser.extract_underlying(symbol)

    if not position.open_date or not position.close_date:
        st.warning("缺少开仓或平仓日期")
        return

    start_date = position.open_date - timedelta(days=30)
    end_date = position.close_date + timedelta(days=30)

    session = get_session()
    try:
        market_data = session.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.date >= start_date,
            MarketData.date <= end_date
        ).order_by(MarketData.date).all()

        if not market_data:
            st.warning(f"未找到 {symbol} 的市场数据")
            return

        df = pd.DataFrame([{
            'date': md.date,
            'open': float(md.open) if md.open else None,
            'high': float(md.high) if md.high else None,
            'low': float(md.low) if md.low else None,
            'close': float(md.close) if md.close else None,
            'volume': float(md.volume) if md.volume else None,
        } for md in market_data])

        if df.empty:
            st.warning("无有效数据")
            return

        # 计算MAE/MFE价格
        is_long = position.direction in ['long', 'buy', 'buy_to_open']
        open_price = float(position.open_price) if position.open_price else 0

        # 持仓期间数据
        holding_df = df[(df['date'] >= position.open_date) & (df['date'] <= position.close_date)]

        mae_price = None
        mfe_price = None
        if not holding_df.empty and open_price > 0:
            if is_long:
                mae_price = holding_df['low'].min()  # 做多时最低点
                mfe_price = holding_df['high'].max()  # 做多时最高点
            else:
                mae_price = holding_df['high'].max()  # 做空时最高点
                mfe_price = holding_df['low'].min()  # 做空时最低点

        # 创建增强K线图
        fig = create_enhanced_candlestick(
            df,
            entry_date=position.open_date,
            exit_date=position.close_date,
            entry_price=float(position.open_price) if position.open_price else None,
            exit_price=float(position.close_price) if position.close_price else None,
            mae_price=mae_price,
            mfe_price=mfe_price,
            is_long=is_long,
            title=f"{symbol} · 交易复盘",
            show_volume=True,
            show_ma=False,
            show_post_exit_fade=True,
            height=450,
        )

        st.plotly_chart(fig, use_container_width=True)

    finally:
        session.close()


def render_execution_scores(position: Position):
    """渲染执行评分"""
    entry_score = float(position.entry_quality_score) if position.entry_quality_score else 0
    exit_score = float(position.exit_quality_score) if position.exit_quality_score else 0
    trend_score = float(position.trend_quality_score) if position.trend_quality_score else 0
    risk_score = float(position.risk_mgmt_score) if position.risk_mgmt_score else 0
    overall_score = float(position.overall_score) if position.overall_score else 0

    # 使用环形图
    render_progress_rings([
        {'label': '入场', 'value': entry_score},
        {'label': '出场', 'value': exit_score},
        {'label': '趋势', 'value': trend_score},
        {'label': '风控', 'value': risk_score},
    ])

    # 综合评分
    st.markdown(f"""
    <div style="
        text-align: center;
        margin-top: 1rem;
        padding: 1rem;
        background: {COLORS['bg_secondary']};
        border-radius: 8px;
    ">
        <span style="color: {COLORS['text_secondary']};">综合评分</span>
        <span style="
            font-family: {FONTS['mono']};
            font-size: 1.5rem;
            font-weight: 700;
            color: {COLORS['text_primary']};
            margin-left: 0.5rem;
        ">{overall_score:.0f}</span>
    </div>
    """, unsafe_allow_html=True)


def render_indicator_comparison(position: Position):
    """渲染入场/出场指标对比"""
    entry_ind = position.entry_indicators or {}
    exit_ind = position.exit_indicators or {}

    if not entry_ind and not exit_ind:
        st.info("暂无技术指标数据")
        return

    indicators = [
        ('rsi_14', 'RSI'),
        ('macd', 'MACD'),
        ('adx', 'ADX'),
        ('bb_position', 'BB位置'),
        ('volume_ratio', '量比'),
    ]

    rows_html = ""
    for field, label in indicators:
        entry_val = entry_ind.get(field)
        exit_val = exit_ind.get(field)

        def format_val(v):
            if v is None:
                return "-"
            if isinstance(v, float):
                return f"{v:.2f}"
            return str(v)

        change_icon = ""
        if entry_val is not None and exit_val is not None:
            try:
                diff = float(exit_val) - float(entry_val)
                if diff > 0:
                    change_icon = f"<span style='color: {COLORS['profit']};'>▲</span>"
                elif diff < 0:
                    change_icon = f"<span style='color: {COLORS['loss']};'>▼</span>"
                else:
                    change_icon = "→"
            except:
                change_icon = ""

        rows_html += f"""
        <tr>
            <td style="padding: 0.5rem; border-bottom: 1px solid {COLORS['border']}; color: {COLORS['text_secondary']};">{label}</td>
            <td style="padding: 0.5rem; border-bottom: 1px solid {COLORS['border']}; font-family: {FONTS['mono']}; color: {COLORS['accent_cyan']}; text-align: center;">{format_val(entry_val)}</td>
            <td style="padding: 0.5rem; border-bottom: 1px solid {COLORS['border']}; text-align: center;">{change_icon}</td>
            <td style="padding: 0.5rem; border-bottom: 1px solid {COLORS['border']}; font-family: {FONTS['mono']}; color: {COLORS['accent_purple']}; text-align: center;">{format_val(exit_val)}</td>
        </tr>
        """

    st.markdown(f"""
    <table style="width: 100%; border-collapse: collapse; background: {COLORS['bg_secondary']}; border-radius: 8px; overflow: hidden;">
        <thead>
            <tr>
                <th style="padding: 0.5rem; border-bottom: 2px solid {COLORS['border']}; color: {COLORS['text_secondary']}; text-align: left;">指标</th>
                <th style="padding: 0.5rem; border-bottom: 2px solid {COLORS['border']}; color: {COLORS['accent_cyan']}; text-align: center;">入场</th>
                <th style="padding: 0.5rem; border-bottom: 2px solid {COLORS['border']}; color: {COLORS['text_muted']}; text-align: center;">→</th>
                <th style="padding: 0.5rem; border-bottom: 2px solid {COLORS['border']}; color: {COLORS['accent_purple']}; text-align: center;">出场</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """, unsafe_allow_html=True)


def render_post_exit_analysis(position: Position):
    """渲染离场后走势"""
    has_data = any([
        position.post_exit_5d_pct,
        position.post_exit_10d_pct,
        position.post_exit_20d_pct
    ])

    if not has_data:
        st.info("暂无离场后走势数据")
        return

    pct_5d = float(position.post_exit_5d_pct) if position.post_exit_5d_pct else 0
    pct_10d = float(position.post_exit_10d_pct) if position.post_exit_10d_pct else 0
    pct_20d = float(position.post_exit_20d_pct) if position.post_exit_20d_pct else 0

    cols = st.columns(3)

    for col, (days, pct) in zip(cols, [('5日', pct_5d), ('10日', pct_10d), ('20日', pct_20d)]):
        color = COLORS['profit'] if pct >= 0 else COLORS['loss']
        sign = "+" if pct >= 0 else ""
        icon = "▲" if pct >= 0 else "▼"

        with col:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_secondary']};
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            ">
                <div style="color: {COLORS['text_muted']}; font-size: 0.75rem;">{days}后</div>
                <div style="font-family: {FONTS['mono']}; font-size: 1.25rem; font-weight: 600; color: {color};">
                    {icon} {sign}{pct:.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)


def main():
    loader = get_data_loader()
    session = get_session()

    try:
        positions = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_time.desc()).all()

        if not positions:
            st.warning("暂无已平仓交易")
            return

        # 创建位置ID映射
        position_ids = [p.id for p in positions]

        # 检查是否从交易浏览器跳转
        selected_id = st.session_state.get('selected_position_id')
        if selected_id and selected_id in position_ids:
            current_idx = position_ids.index(selected_id)
        else:
            current_idx = 0

        # ================================================================
        # 导航栏
        # ================================================================
        nav_cols = st.columns([1, 3, 1])

        with nav_cols[0]:
            if current_idx > 0:
                if st.button("← 上一笔", use_container_width=True):
                    st.session_state['selected_position_id'] = position_ids[current_idx - 1]
                    st.rerun()
            else:
                st.button("← 上一笔", disabled=True, use_container_width=True)

        with nav_cols[1]:
            # 交易选择器
            position_options = {
                p.id: f"{p.symbol} | {p.close_time.strftime('%Y-%m-%d') if p.close_time else 'N/A'} | {'盈利' if p.net_pnl and float(p.net_pnl) >= 0 else '亏损'} ${abs(float(p.net_pnl or 0)):,.2f}"
                for p in positions
            }

            selected_id = st.selectbox(
                "选择交易",
                options=list(position_options.keys()),
                format_func=lambda x: position_options[x],
                index=current_idx,
                label_visibility="collapsed",
            )
            st.session_state['selected_position_id'] = selected_id

        with nav_cols[2]:
            if current_idx < len(position_ids) - 1:
                if st.button("下一笔 →", use_container_width=True):
                    st.session_state['selected_position_id'] = position_ids[current_idx + 1]
                    st.rerun()
            else:
                st.button("下一笔 →", disabled=True, use_container_width=True)

        st.markdown("<hr style='margin: 1rem 0; border-color: #333;'>", unsafe_allow_html=True)

        # 获取当前持仓
        position = session.query(Position).filter(Position.id == selected_id).first()

        if not position:
            st.error("未找到该交易")
            return

        # ================================================================
        # 主要内容
        # ================================================================

        # Hero区域
        render_hero_section(position)

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # 指标行
        render_metrics_row(position)

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # K线图
        render_kline_chart(position)

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # 三列布局: 评分 | 指标对比 | 离场后
        col1, col2, col3 = st.columns([1, 1.2, 0.8])

        with col1:
            st.markdown(f"""
            <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
                ⚡ 执行评分
            </div>
            """, unsafe_allow_html=True)
            render_execution_scores(position)

        with col2:
            st.markdown(f"""
            <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
                📊 指标对比
            </div>
            """, unsafe_allow_html=True)
            render_indicator_comparison(position)

        with col3:
            st.markdown(f"""
            <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
                📉 离场后走势
            </div>
            """, unsafe_allow_html=True)
            render_post_exit_analysis(position)

        # ================================================================
        # 复盘笔记
        # ================================================================
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 0.75rem;">
            📝 复盘笔记
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])

        with col1:
            emotion_options = {
                None: "未选择",
                "calm": "😌 冷静",
                "greedy": "🤑 贪婪",
                "fearful": "😰 恐惧",
                "impulsive": "💢 冲动"
            }
            current_emotion = position.emotion_tag
            emotion_idx = list(emotion_options.keys()).index(current_emotion) if current_emotion in emotion_options else 0

            new_emotion = st.selectbox(
                "交易情绪",
                options=list(emotion_options.keys()),
                format_func=lambda x: emotion_options[x],
                index=emotion_idx,
                key=f"emotion_{position.id}"
            )

            discipline_score = position.discipline_score or 3
            new_discipline = st.slider(
                "纪律执行",
                min_value=1,
                max_value=5,
                value=discipline_score,
                help="1=完全没按计划执行, 5=严格按计划执行",
                key=f"discipline_{position.id}"
            )

        with col2:
            current_notes = position.review_notes or {}
            user_notes = current_notes.get('user_notes', '') if isinstance(current_notes, dict) else ''
            new_notes = st.text_area(
                "心得笔记",
                value=user_notes,
                height=120,
                placeholder="记录你的复盘心得...",
                key=f"notes_{position.id}"
            )

        if st.button("💾 保存复盘", key=f"save_{position.id}", type="primary"):
            try:
                pos = session.query(Position).filter(Position.id == position.id).first()
                if pos:
                    pos.emotion_tag = new_emotion
                    pos.discipline_score = new_discipline
                    pos.review_notes = {'user_notes': new_notes}
                    pos.reviewed_at = datetime.utcnow()
                    session.commit()
                    st.success("✅ 复盘已保存！")
                    st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")

    finally:
        session.close()


if __name__ == "__main__":
    main()
