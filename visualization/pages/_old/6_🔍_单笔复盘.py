"""
单笔交易复盘页面 - Terminal Finance 主题

提供完整的单笔交易复盘功能，包括：
- 交易概况和盈亏信息
- 入场时技术指标分析
- 执行质量评估
- 离场后走势分析
- 复盘总结和用户备注
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

# 页面配置
st.set_page_config(
    page_title="单笔复盘",
    page_icon="🔍",
    layout="wide"
)

# 导入样式系统
from visualization.styles import (
    inject_global_css, COLORS, FONTS,
    metric_display, pnl_badge, grade_badge, progress_ring,
    indicator_card, section_header, strategy_badge, direction_badge,
    date_range_display, render_html, render_progress_rings,
)
from visualization.styles.plotly_theme import create_dark_candlestick, get_plotly_theme

inject_global_css()


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


def get_strategy_name(strategy_type: str) -> str:
    """获取策略中文名称"""
    return StrategyClassifier.STRATEGY_NAMES.get(strategy_type, strategy_type or "未分类")


def render_hero_section(position: Position):
    """渲染顶部概览区"""
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
    pnl_icon = "▲" if is_profit else "▼"
    pnl_sign = "+" if is_profit else ""

    # 策略信息
    strategy_type = position.strategy_type or "unknown"
    strategy_name = get_strategy_name(strategy_type)
    strategy_color = {
        'trend': COLORS['strategy_trend'],
        'mean_reversion': COLORS['strategy_reversion'],
        'breakout': COLORS['strategy_breakout'],
        'range': COLORS['strategy_range'],
        'momentum': COLORS['strategy_momentum'],
    }.get(strategy_type, COLORS['neutral'])

    # 等级
    grade = position.score_grade or "-"
    grade_color = {
        'A': COLORS['grade_a'], 'B': COLORS['grade_b'],
        'C': COLORS['grade_c'], 'D': COLORS['grade_d'], 'F': COLORS['grade_f']
    }.get(grade[0] if grade else 'C', COLORS['neutral'])

    st.markdown(f"""
    <div class="hero-section fade-in" style="
        background: linear-gradient(135deg, {COLORS['bg_secondary']} 0%, {COLORS['bg_tertiary']} 100%);
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 2rem;">
            <!-- 左侧：股票信息 -->
            <div style="flex: 1; min-width: 200px;">
                <div style="
                    font-family: {FONTS['mono']};
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: {COLORS['text_primary']};
                    letter-spacing: -0.02em;
                ">{position.symbol}</div>
                <div style="
                    color: {COLORS['text_secondary']};
                    font-size: 1rem;
                    margin-top: 0.25rem;
                ">{position.symbol_name or ''}</div>
                <div style="margin-top: 1rem;">
                    <span style="
                        display: inline-flex;
                        align-items: center;
                        gap: 0.25rem;
                        color: {'#00FF88' if is_long else '#FF3B5C'};
                        font-weight: 600;
                        font-size: 1rem;
                    ">{'▲ 做多' if is_long else '▼ 做空'}</span>
                </div>
                <div style="
                    color: {COLORS['text_secondary']};
                    font-size: 0.875rem;
                    margin-top: 1rem;
                ">
                    <span style="color: {COLORS['text_primary']};">{open_date_str}</span>
                    <span style="margin: 0 0.5rem;">→</span>
                    <span style="color: {COLORS['text_primary']};">{close_date_str}</span>
                    <span style="
                        margin-left: 0.75rem;
                        padding: 0.125rem 0.5rem;
                        background: {COLORS['bg_tertiary']};
                        border-radius: 9999px;
                        font-size: 0.75rem;
                    ">{holding_days} 天</span>
                </div>
            </div>

            <!-- 中间：盈亏 -->
            <div style="flex: 1; min-width: 200px; text-align: center;">
                <div style="
                    font-family: {FONTS['mono']};
                    font-size: 3rem;
                    font-weight: 700;
                    color: {pnl_color};
                    text-shadow: 0 0 30px {pnl_color}50;
                    line-height: 1.2;
                ">
                    {pnl_sign}${abs(net_pnl):,.2f}
                </div>
                <div style="
                    display: inline-flex;
                    align-items: center;
                    gap: 0.25rem;
                    color: {pnl_color};
                    font-family: {FONTS['mono']};
                    font-size: 1.25rem;
                    margin-top: 0.5rem;
                ">
                    {pnl_icon} {pnl_sign}{net_pnl_pct:.2f}%
                </div>
            </div>

            <!-- 右侧：评分和策略 -->
            <div style="flex: 1; min-width: 200px; text-align: right;">
                <div style="
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 4rem;
                    height: 4rem;
                    background: {grade_color}15;
                    border: 2px solid {grade_color};
                    border-radius: 12px;
                    font-family: {FONTS['mono']};
                    font-size: 1.75rem;
                    font-weight: 700;
                    color: {grade_color};
                    text-shadow: 0 0 10px {grade_color};
                ">{grade}</div>
                <div style="
                    color: {COLORS['text_secondary']};
                    font-size: 0.875rem;
                    margin-top: 0.5rem;
                ">综合评级</div>
                <div style="margin-top: 1rem;">
                    <span style="
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        padding: 0.5rem 1rem;
                        background: {strategy_color}15;
                        border: 1px solid {strategy_color};
                        border-radius: 9999px;
                        color: {strategy_color};
                        font-weight: 600;
                        font-size: 0.875rem;
                    ">
                        <span style="
                            width: 8px;
                            height: 8px;
                            background: {strategy_color};
                            border-radius: 50%;
                            box-shadow: 0 0 8px {strategy_color};
                        "></span>
                        {strategy_name}
                    </span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics_bar(position: Position):
    """渲染指标条"""
    open_price = float(position.open_price) if position.open_price else 0
    close_price = float(position.close_price) if position.close_price else 0
    quantity = position.quantity or 0
    mae_pct = float(position.mae_pct) if position.mae_pct else 0
    mfe_pct = float(position.mfe_pct) if position.mfe_pct else 0

    st.markdown(f"""
    <div style="
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    ">
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">开仓价</div>
            <div style="font-family: {FONTS['mono']}; font-size: 1.25rem; font-weight: 600; color: {COLORS['text_primary']}; margin-top: 0.25rem;">${open_price:.2f}</div>
        </div>
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">平仓价</div>
            <div style="font-family: {FONTS['mono']}; font-size: 1.25rem; font-weight: 600; color: {COLORS['text_primary']}; margin-top: 0.25rem;">${close_price:.2f}</div>
        </div>
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">数量</div>
            <div style="font-family: {FONTS['mono']}; font-size: 1.25rem; font-weight: 600; color: {COLORS['text_primary']}; margin-top: 0.25rem;">{quantity}</div>
        </div>
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">MAE (最大回撤)</div>
            <div style="font-family: {FONTS['mono']}; font-size: 1.25rem; font-weight: 600; color: {COLORS['loss']}; margin-top: 0.25rem;">{mae_pct:.2f}%</div>
        </div>
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">MFE (最大盈利)</div>
            <div style="font-family: {FONTS['mono']}; font-size: 1.25rem; font-weight: 600; color: {COLORS['profit']}; margin-top: 0.25rem;">{mfe_pct:.2f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_kline_chart(position: Position):
    """渲染K线图"""
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

        # 构建买卖点
        buy_points = [{'date': position.open_date, 'price': float(position.open_price)}]
        sell_points = []
        if position.close_date and position.close_price:
            sell_points = [{'date': position.close_date, 'price': float(position.close_price)}]

        # 创建深色主题K线图
        fig = create_dark_candlestick(
            df,
            title=f"{symbol} · 交易复盘",
            show_volume=True,
            show_ma=False,
            buy_points=buy_points,
            sell_points=sell_points,
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    finally:
        session.close()


def render_entry_analysis(position: Position, market_data: MarketData):
    """渲染入场分析Tab"""
    render_html(section_header("入场时技术指标", icon="📊"))

    if not market_data:
        st.info("未找到入场时的市场数据")
        return

    # 指标卡片网格
    indicators = []

    if market_data.rsi_14:
        rsi = float(market_data.rsi_14)
        status, status_type = get_indicator_status('RSI', rsi)
        indicators.append(indicator_card("RSI (14)", f"{rsi:.1f}", status, status_type))

    if market_data.macd and market_data.macd_signal:
        macd = float(market_data.macd)
        signal = float(market_data.macd_signal)
        macd_status = "金叉" if macd > signal else "死叉"
        macd_type = "bullish" if macd > signal else "bearish"
        indicators.append(indicator_card("MACD", f"{macd:.4f}", macd_status, macd_type))

    if market_data.adx:
        adx = float(market_data.adx)
        status, status_type = get_indicator_status('ADX', adx)
        indicators.append(indicator_card("ADX", f"{adx:.1f}", status, status_type))

    if market_data.stoch_k:
        stoch = float(market_data.stoch_k)
        status, status_type = get_indicator_status('Stoch', stoch)
        indicators.append(indicator_card("Stochastic %K", f"{stoch:.1f}", status, status_type))

    if market_data.bb_upper and market_data.bb_lower and market_data.close:
        upper = float(market_data.bb_upper)
        lower = float(market_data.bb_lower)
        close = float(market_data.close)
        bb_pct = (close - lower) / (upper - lower) if upper != lower else 0.5

        if bb_pct > 0.8:
            bb_status, bb_type = "接近上轨", "bearish"
        elif bb_pct < 0.2:
            bb_status, bb_type = "接近下轨", "bullish"
        else:
            bb_status, bb_type = "中间区域", "neutral"
        indicators.append(indicator_card("布林带 %B", f"{bb_pct:.2f}", bb_status, bb_type))

    if market_data.volume and market_data.volume_sma_20:
        vol = float(market_data.volume)
        vol_ma = float(market_data.volume_sma_20)
        vol_ratio = vol / vol_ma if vol_ma > 0 else 1
        if vol_ratio > 1.5:
            vol_status, vol_type = "放量", "bullish"
        elif vol_ratio < 0.7:
            vol_status, vol_type = "缩量", "bearish"
        else:
            vol_status, vol_type = "正常", "neutral"
        indicators.append(indicator_card("成交量比", f"{vol_ratio:.2f}x", vol_status, vol_type))

    # 渲染指标网格
    if indicators:
        cols = st.columns(min(len(indicators), 4))
        for i, ind_html in enumerate(indicators):
            with cols[i % 4]:
                render_html(ind_html)

    # 均线分析
    st.markdown("<br>", unsafe_allow_html=True)
    if market_data.ma_5 and market_data.ma_20 and market_data.ma_50:
        ma5 = float(market_data.ma_5)
        ma20 = float(market_data.ma_20)
        ma50 = float(market_data.ma_50)

        if ma5 > ma20 > ma50:
            ma_status = ("多头排列", COLORS['profit'], "MA5 > MA20 > MA50")
        elif ma5 < ma20 < ma50:
            ma_status = ("空头排列", COLORS['loss'], "MA5 < MA20 < MA50")
        else:
            ma_status = ("均线交织", COLORS['warning'], "趋势不明确")

        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div>
                <span style="color: {COLORS['text_secondary']};">均线排列：</span>
                <span style="color: {ma_status[1]}; font-weight: 600;">{ma_status[0]}</span>
                <span style="color: {COLORS['text_muted']}; margin-left: 0.5rem;">({ma_status[2]})</span>
            </div>
            <div style="display: flex; gap: 1.5rem;">
                <div><span style="color: {COLORS['text_secondary']};">MA5</span> <span style="font-family: {FONTS['mono']}; color: {COLORS['warning']};">${ma5:.2f}</span></div>
                <div><span style="color: {COLORS['text_secondary']};">MA20</span> <span style="font-family: {FONTS['mono']}; color: {COLORS['accent_cyan']};">${ma20:.2f}</span></div>
                <div><span style="color: {COLORS['text_secondary']};">MA50</span> <span style="font-family: {FONTS['mono']}; color: {COLORS['accent_purple']};">${ma50:.2f}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_execution_analysis(position: Position):
    """渲染执行评估Tab"""
    render_html(section_header("执行质量评估", icon="⚡"))

    # 四维评分环形图
    entry_score = float(position.entry_quality_score) if position.entry_quality_score else 0
    exit_score = float(position.exit_quality_score) if position.exit_quality_score else 0
    trend_score = float(position.trend_quality_score) if position.trend_quality_score else 0
    risk_score = float(position.risk_mgmt_score) if position.risk_mgmt_score else 0
    overall_score = float(position.overall_score) if position.overall_score else 0

    render_progress_rings([
        {'label': '入场质量', 'value': entry_score},
        {'label': '出场质量', 'value': exit_score},
        {'label': '趋势把握', 'value': trend_score},
        {'label': '风险管理', 'value': risk_score},
    ])

    # 综合评分
    st.markdown("<br>", unsafe_allow_html=True)
    grade = position.score_grade or "-"
    grade_color = {
        'A': COLORS['grade_a'], 'B': COLORS['grade_b'],
        'C': COLORS['grade_c'], 'D': COLORS['grade_d'], 'F': COLORS['grade_f']
    }.get(grade[0] if grade else 'C', COLORS['neutral'])

    st.markdown(f"""
    <div style="
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 2rem;
    ">
        <div style="text-align: center;">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem; margin-bottom: 0.5rem;">综合评分</div>
            <div style="font-family: {FONTS['mono']}; font-size: 3rem; font-weight: 700; color: {COLORS['text_primary']};">
                {overall_score:.0f}
            </div>
        </div>
        <div style="
            width: 1px;
            height: 60px;
            background: {COLORS['border']};
        "></div>
        <div style="text-align: center;">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem; margin-bottom: 0.5rem;">评级</div>
            <div style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 3.5rem;
                height: 3.5rem;
                background: {grade_color}15;
                border: 2px solid {grade_color};
                border-radius: 10px;
                font-family: {FONTS['mono']};
                font-size: 1.75rem;
                font-weight: 700;
                color: {grade_color};
                text-shadow: 0 0 10px {grade_color};
            ">{grade}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_indicator_timeline(position: Position):
    """渲染入场/出场技术指标对比"""
    render_html(section_header("技术指标时间线", icon="📈"))

    entry_indicators = position.entry_indicators
    exit_indicators = position.exit_indicators

    if not entry_indicators and not exit_indicators:
        st.info("暂无技术指标数据。请运行 `python3 scripts/enrich_position_indicators.py --force` 来填充指标快照。")
        return

    # 关键指标对比
    key_indicators = [
        ('rsi_14', 'RSI', 0, 100, ''),
        ('macd', 'MACD', None, None, ''),
        ('adx', 'ADX', 0, 100, ''),
        ('bb_position', 'BB位置', 0, 1, '%'),
        ('ma20_deviation_pct', 'MA20偏离', None, None, '%'),
        ('volume_ratio', '量比', 0, 5, 'x'),
    ]

    def get_change_icon(entry_val, exit_val):
        if entry_val is None or exit_val is None:
            return ""
        diff = exit_val - entry_val
        if diff > 0:
            return f"<span style='color: {COLORS['profit']};'>▲</span>"
        elif diff < 0:
            return f"<span style='color: {COLORS['loss']};'>▼</span>"
        return "→"

    def format_value(val, suffix=''):
        if val is None:
            return "-"
        if isinstance(val, float):
            if suffix == '%':
                return f"{val*100:.1f}%" if abs(val) < 10 else f"{val:.1f}%"
            return f"{val:.2f}{suffix}"
        return str(val)

    # 构建HTML表格
    rows_html = ""
    for field, label, min_val, max_val, suffix in key_indicators:
        entry_val = entry_indicators.get(field) if entry_indicators else None
        exit_val = exit_indicators.get(field) if exit_indicators else None
        change_icon = get_change_icon(entry_val, exit_val)

        entry_str = format_value(entry_val, suffix)
        exit_str = format_value(exit_val, suffix)

        rows_html += f"""
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid {COLORS['border']}; color: {COLORS['text_secondary']};">{label}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid {COLORS['border']}; font-family: {FONTS['mono']}; color: {COLORS['accent_cyan']}; text-align: center;">{entry_str}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid {COLORS['border']}; text-align: center;">{change_icon}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid {COLORS['border']}; font-family: {FONTS['mono']}; color: {COLORS['accent_purple']}; text-align: center;">{exit_str}</td>
        </tr>
        """

    st.markdown(f"""
    <div style="
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    ">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr>
                    <th style="padding: 0.75rem; border-bottom: 2px solid {COLORS['border']}; color: {COLORS['text_secondary']}; text-align: left;">指标</th>
                    <th style="padding: 0.75rem; border-bottom: 2px solid {COLORS['border']}; color: {COLORS['accent_cyan']}; text-align: center;">入场时</th>
                    <th style="padding: 0.75rem; border-bottom: 2px solid {COLORS['border']}; color: {COLORS['text_muted']}; text-align: center;">变化</th>
                    <th style="padding: 0.75rem; border-bottom: 2px solid {COLORS['border']}; color: {COLORS['accent_purple']}; text-align: center;">出场时</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # 入场/出场日期信息
    col1, col2 = st.columns(2)

    with col1:
        entry_date = entry_indicators.get('date', '-') if entry_indicators else '-'
        entry_close = entry_indicators.get('close', 0) if entry_indicators else 0
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_tertiary']};
            border-left: 3px solid {COLORS['accent_cyan']};
            padding: 1rem;
            border-radius: 0 8px 8px 0;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">入场日期</div>
            <div style="color: {COLORS['text_primary']}; font-family: {FONTS['mono']}; font-size: 1.125rem;">{entry_date}</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.75rem; margin-top: 0.5rem;">收盘价: ${entry_close:.2f if entry_close else 0}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        exit_date = exit_indicators.get('date', '-') if exit_indicators else '-'
        exit_close = exit_indicators.get('close', 0) if exit_indicators else 0
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_tertiary']};
            border-left: 3px solid {COLORS['accent_purple']};
            padding: 1rem;
            border-radius: 0 8px 8px 0;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">出场日期</div>
            <div style="color: {COLORS['text_primary']}; font-family: {FONTS['mono']}; font-size: 1.125rem;">{exit_date}</div>
            <div style="color: {COLORS['text_muted']}; font-size: 0.75rem; margin-top: 0.5rem;">收盘价: ${exit_close:.2f if exit_close else 0}</div>
        </div>
        """, unsafe_allow_html=True)

    # 详细指标展开
    with st.expander("查看完整指标数据"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**入场时指标**")
            if entry_indicators:
                for k, v in entry_indicators.items():
                    if k != 'date':
                        st.write(f"- {k}: {v}")
            else:
                st.write("无数据")

        with col2:
            st.markdown(f"**出场时指标**")
            if exit_indicators:
                for k, v in exit_indicators.items():
                    if k != 'date':
                        st.write(f"- {k}: {v}")
            else:
                st.write("无数据")


def render_post_exit_analysis(position: Position):
    """渲染离场后走势Tab"""
    render_html(section_header("离场后走势分析", icon="📉"))

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

    def get_pct_style(pct):
        color = COLORS['profit'] if pct >= 0 else COLORS['loss']
        sign = "+" if pct >= 0 else ""
        icon = "▲" if pct >= 0 else "▼"
        return color, f"{icon} {sign}{pct:.2f}%"

    c5, t5 = get_pct_style(pct_5d)
    c10, t10 = get_pct_style(pct_10d)
    c20, t20 = get_pct_style(pct_20d)

    st.markdown(f"""
    <div style="
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    ">
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">5日后</div>
            <div style="font-family: {FONTS['mono']}; font-size: 1.5rem; font-weight: 600; color: {c5}; margin-top: 0.5rem;">{t5}</div>
        </div>
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">10日后</div>
            <div style="font-family: {FONTS['mono']}; font-size: 1.5rem; font-weight: 600; color: {c10}; margin-top: 0.5rem;">{t10}</div>
        </div>
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">20日后</div>
            <div style="font-family: {FONTS['mono']}; font-size: 1.5rem; font-weight: 600; color: {c20}; margin-top: 0.5rem;">{t20}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 离场决策评价
    is_long = position.direction in ['long', 'buy', 'buy_to_open']
    net_pnl = float(position.net_pnl) if position.net_pnl else 0
    is_winner = net_pnl >= 0

    if is_winner:
        if (is_long and pct_20d > 10) or (not is_long and pct_20d < -10):
            st.warning("⚠️ 过早离场 - 离场后行情继续朝有利方向发展")
        elif (is_long and pct_20d < -10) or (not is_long and pct_20d > 10):
            st.success("✅ 及时离场 - 成功锁定利润")
        else:
            st.info("ℹ️ 正常离场 - 离场时机适中")
    else:
        if (is_long and pct_20d > 20) or (not is_long and pct_20d < -20):
            st.error("❌ 止损后反转 - 考虑是否止损太紧")
        elif (is_long and pct_20d < -10) or (not is_long and pct_20d > 10):
            st.success("✅ 正确止损 - 避免了更大损失")
        else:
            st.info("ℹ️ 止损合理 - 符合风险管理")


def render_summary(position: Position):
    """渲染复盘总结Tab"""
    render_html(section_header("复盘总结", icon="📝"))

    # 系统分析
    positives = []
    negatives = []
    suggestions = []

    net_pnl = float(position.net_pnl) if position.net_pnl else 0
    is_winner = net_pnl >= 0

    if is_winner:
        positives.append("这笔交易实现了盈利")

    if position.entry_quality_score and float(position.entry_quality_score) >= 70:
        positives.append("入场时机把握较好")
    elif position.entry_quality_score and float(position.entry_quality_score) < 50:
        negatives.append("入场时机欠佳")
        suggestions.append("建议等待更好的入场信号")

    if position.exit_quality_score and float(position.exit_quality_score) >= 70:
        positives.append("出场时机合理")
    elif position.exit_quality_score and float(position.exit_quality_score) < 50:
        negatives.append("出场时机可以改进")

    if position.risk_mgmt_score and float(position.risk_mgmt_score) >= 70:
        positives.append("风险控制得当")
    elif position.risk_mgmt_score and float(position.risk_mgmt_score) < 50:
        negatives.append("风险管理需要加强")
        suggestions.append("建议设置更合理的止损位")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1.5rem;
            height: 100%;
        ">
            <div style="color: {COLORS['profit']}; font-weight: 600; margin-bottom: 1rem;">✓ 做对了什么</div>
            {''.join([f'<div style="color: {COLORS["text_secondary"]}; padding: 0.25rem 0;">• {p}</div>' for p in (positives or ['暂无明显亮点'])])}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1.5rem;
            height: 100%;
        ">
            <div style="color: {COLORS['loss']}; font-weight: 600; margin-bottom: 1rem;">✗ 可以改进</div>
            {''.join([f'<div style="color: {COLORS["text_secondary"]}; padding: 0.25rem 0;">• {n}</div>' for n in (negatives or ['暂无明显问题'])])}
        </div>
        """, unsafe_allow_html=True)

    if suggestions:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['warning']};
            border-radius: 12px;
            padding: 1.5rem;
        ">
            <div style="color: {COLORS['warning']}; font-weight: 600; margin-bottom: 1rem;">💡 改进建议</div>
            {''.join([f'<div style="color: {COLORS["text_secondary"]}; padding: 0.25rem 0;">• {s}</div>' for s in suggestions])}
        </div>
        """, unsafe_allow_html=True)

    # 用户备注
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="color: {COLORS['text_primary']}; font-weight: 600; margin-bottom: 1rem;">个人复盘</div>
    """, unsafe_allow_html=True)

    session = get_session()

    col1, col2 = st.columns([1, 1])

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
            "交易时的情绪状态",
            options=list(emotion_options.keys()),
            format_func=lambda x: emotion_options[x],
            index=emotion_idx,
            key=f"emotion_{position.id}"
        )

    with col2:
        discipline_score = position.discipline_score or 3
        new_discipline = st.slider(
            "纪律执行评分",
            min_value=1,
            max_value=5,
            value=discipline_score,
            help="1=完全没按计划执行, 5=严格按计划执行",
            key=f"discipline_{position.id}"
        )

    current_notes = position.review_notes or {}
    user_notes = current_notes.get('user_notes', '') if isinstance(current_notes, dict) else ''
    new_notes = st.text_area(
        "复盘笔记",
        value=user_notes,
        height=100,
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

        # 侧边栏选择器
        st.sidebar.markdown(f"""
        <div style="
            color: {COLORS['text_primary']};
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1rem;
        ">选择交易</div>
        """, unsafe_allow_html=True)

        symbols = sorted(list(set([p.symbol for p in positions])))
        selected_symbol = st.sidebar.selectbox(
            "股票代码",
            options=["全部"] + symbols,
            label_visibility="collapsed"
        )

        filtered_positions = positions
        if selected_symbol != "全部":
            filtered_positions = [p for p in positions if p.symbol == selected_symbol]

        position_options = {
            p.id: f"{p.symbol} | {p.close_time.strftime('%Y-%m-%d') if p.close_time else 'N/A'} | {'盈利' if p.net_pnl and float(p.net_pnl) >= 0 else '亏损'} ${abs(float(p.net_pnl or 0)):,.2f}"
            for p in filtered_positions
        }

        if not position_options:
            st.warning("没有符合条件的交易")
            return

        selected_id = st.sidebar.selectbox(
            "选择交易",
            options=list(position_options.keys()),
            format_func=lambda x: position_options[x],
            label_visibility="collapsed"
        )

        position = session.query(Position).filter(Position.id == selected_id).first()

        if not position:
            st.error("未找到该交易")
            return

        # 获取入场时市场数据
        entry_symbol = position.symbol
        if OptionParser.is_option_symbol(entry_symbol):
            entry_symbol = OptionParser.extract_underlying(entry_symbol)

        entry_market_data = None
        if position.open_date:
            entry_market_data = session.query(MarketData).filter(
                MarketData.symbol == entry_symbol,
                MarketData.date == position.open_date
            ).first()

        # 渲染页面
        render_hero_section(position)
        render_metrics_bar(position)
        render_kline_chart(position)

        # Tab页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 入场分析",
            "📈 指标对比",
            "⚡ 执行评估",
            "📉 离场后走势",
            "📝 复盘总结"
        ])

        with tab1:
            render_entry_analysis(position, entry_market_data)

        with tab2:
            render_indicator_timeline(position)

        with tab3:
            render_execution_analysis(position)

        with tab4:
            render_post_exit_analysis(position)

        with tab5:
            render_summary(position)

    finally:
        session.close()


if __name__ == "__main__":
    main()
