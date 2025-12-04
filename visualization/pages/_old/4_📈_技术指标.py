"""
Technical Indicators Page - Terminal Finance 主题
技术指标页面
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from visualization.utils.data_loader import get_data_loader
from visualization.components.charts import create_candlestick_chart, resample_to_weekly
from visualization.styles import inject_global_css

st.set_page_config(page_title="技术指标", page_icon="📈", layout="wide")

# 注入全局样式
inject_global_css()

st.title("📈 技术指标分析")
st.markdown("查看K线图与技术指标，验证数据正确性")

st.markdown("---")

# 加载数据
try:
    loader = get_data_loader()
    symbols = loader.get_symbols_with_market_data()

    if len(symbols) == 0:
        st.warning("⚠️ 没有市场数据")
        st.info("请先运行数据补充工具: `python3 scripts/supplement_data_from_csv.py --from-db`")
        st.stop()

    # 选择股票
    st.subheader("📌 选择股票和日期范围")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        selected_symbol = st.selectbox(
            "股票代码",
            symbols,
            help="选择要查看的股票代码"
        )

    with col2:
        # 获取该股票的日期范围
        if selected_symbol:
            sample_data = loader.get_market_data(selected_symbol)

            if len(sample_data) > 0:
                min_date = sample_data['date'].min()
                max_date = sample_data['date'].max()

                st.metric("数据起始", min_date.strftime('%Y-%m-%d'))
            else:
                min_date = datetime.now() - timedelta(days=365)
                max_date = datetime.now()

    with col3:
        if selected_symbol and len(sample_data) > 0:
            st.metric("数据记录", len(sample_data))

    if not selected_symbol:
        st.info("请选择股票代码")
        st.stop()

    # 时间范围快捷选择
    st.markdown("**快捷选择时间范围**")
    range_cols = st.columns(5)

    # 使用session_state来存储选择的时间范围
    if 'selected_range' not in st.session_state:
        st.session_state.selected_range = 365  # 默认1年

    with range_cols[0]:
        if st.button("3个月", use_container_width=True):
            st.session_state.selected_range = 90
    with range_cols[1]:
        if st.button("6个月", use_container_width=True):
            st.session_state.selected_range = 180
    with range_cols[2]:
        if st.button("1年", use_container_width=True, type="primary" if st.session_state.selected_range == 365 else "secondary"):
            st.session_state.selected_range = 365
    with range_cols[3]:
        if st.button("2年", use_container_width=True):
            st.session_state.selected_range = 730
    with range_cols[4]:
        if st.button("全部", use_container_width=True):
            st.session_state.selected_range = None  # None表示全部数据

    # 时间粒度选择
    st.markdown("")
    timeframe = st.radio(
        "时间粒度",
        ["日线", "周线"],
        horizontal=True,
        help="选择K线的时间粒度"
    )

    # 日期范围选择
    col1, col2 = st.columns(2)

    # 计算默认开始日期
    if st.session_state.selected_range is None:
        default_start = min_date.date() if len(sample_data) > 0 else (datetime.now() - timedelta(days=365)).date()
    else:
        default_start = (max_date - timedelta(days=st.session_state.selected_range)).date() if len(sample_data) > 0 else (datetime.now() - timedelta(days=st.session_state.selected_range)).date()
        # 确保不早于最小日期
        if len(sample_data) > 0 and default_start < min_date.date():
            default_start = min_date.date()

    with col1:
        start_date = st.date_input(
            "开始日期",
            value=default_start,
            min_value=min_date.date() if len(sample_data) > 0 else None,
            max_value=max_date.date() if len(sample_data) > 0 else None
        )

    with col2:
        end_date = st.date_input(
            "结束日期",
            value=max_date.date() if len(sample_data) > 0 else datetime.now().date(),
            min_value=min_date.date() if len(sample_data) > 0 else None,
            max_value=max_date.date() if len(sample_data) > 0 else None
        )

    if start_date > end_date:
        st.error("开始日期不能晚于结束日期")
        st.stop()

    st.markdown("---")

    # 指标显示选项
    st.subheader("⚙️ 显示选项")

    col1, col2, col3 = st.columns(3)

    with col1:
        show_ma = st.checkbox("显示移动平均线", value=True)

    with col2:
        show_bb = st.checkbox("显示布林带", value=False)

    with col3:
        show_trades = st.checkbox("显示交易点位", value=True)

    st.markdown("---")

    # 获取市场数据
    market_df = loader.get_market_data(
        selected_symbol,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    )

    if len(market_df) == 0:
        st.warning(f"股票 {selected_symbol} 在指定日期范围内没有市场数据")
        st.stop()

    # 根据时间粒度转换数据
    if timeframe == "周线":
        display_df = resample_to_weekly(market_df)
        timeframe_label = "周线"
    else:
        display_df = market_df
        timeframe_label = "日线"

    # 获取交易数据（如果需要）
    trades = None
    if show_trades:
        all_trades = loader.get_symbol_trades(selected_symbol)
        # 筛选日期范围内的交易
        trades = [
            t for t in all_trades
            if start_date <= t.filled_time.date() <= end_date
        ]

    # 绘制K线图
    st.subheader(f"📊 {selected_symbol} {timeframe_label}K线图与技术指标")

    fig = create_candlestick_chart(
        display_df,
        trades=trades if show_trades else None,
        show_ma=show_ma,
        show_bb=show_bb
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # 技术指标统计
    st.subheader(f"📊 技术指标统计 ({timeframe_label})")

    tab1, tab2, tab3 = st.tabs(["价格统计", "技术指标", "交易统计"])

    with tab1:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("最高价", f"${display_df['high'].max():.2f}")
            st.metric("最低价", f"${display_df['low'].min():.2f}")

        with col2:
            st.metric("当前价", f"${display_df['close'].iloc[-1]:.2f}")
            price_change = display_df['close'].iloc[-1] - display_df['close'].iloc[0]
            price_change_pct = (price_change / display_df['close'].iloc[0]) * 100
            st.metric(
                "期间涨跌",
                f"${price_change:.2f}",
                delta=f"{price_change_pct:.2f}%"
            )

        with col3:
            st.metric("平均价", f"${display_df['close'].mean():.2f}")
            st.metric("平均成交量", f"{display_df['volume'].mean():,.0f}")

        with col4:
            volatility = display_df['close'].pct_change().std() * 100
            st.metric("波动率", f"{volatility:.2f}%")

            if 'atr' in display_df.columns and display_df['atr'].notna().any():
                st.metric("平均ATR", f"${display_df['atr'].mean():.2f}")

    with tab2:
        if 'rsi' in display_df.columns and display_df['rsi'].notna().any():
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("**RSI**")
                current_rsi = display_df['rsi'].iloc[-1]
                st.metric("当前RSI", f"{current_rsi:.2f}")

                if current_rsi > 70:
                    st.warning("⚠️ 超买区域")
                elif current_rsi < 30:
                    st.warning("⚠️ 超卖区域")
                else:
                    st.success("✓ 中性区域")

            with col2:
                st.markdown("**MACD**")
                if 'macd' in display_df.columns and display_df['macd'].notna().any():
                    current_macd = display_df['macd'].iloc[-1]
                    current_signal = display_df['macd_signal'].iloc[-1]
                    st.metric("MACD", f"{current_macd:.3f}")
                    st.metric("Signal", f"{current_signal:.3f}")

                    if current_macd > current_signal:
                        st.success("✓ 金叉")
                    else:
                        st.info("死叉")

            with col3:
                st.markdown("**移动平均线**")
                if 'ma_5' in display_df.columns and display_df['ma_5'].notna().any():
                    st.metric("MA5", f"${display_df['ma_5'].iloc[-1]:.2f}")
                if 'ma_20' in display_df.columns and display_df['ma_20'].notna().any():
                    st.metric("MA20", f"${display_df['ma_20'].iloc[-1]:.2f}")
                if 'ma_50' in display_df.columns and display_df['ma_50'].notna().any():
                    st.metric("MA50", f"${display_df['ma_50'].iloc[-1]:.2f}")

            with col4:
                st.markdown("**布林带**")
                if 'bb_upper' in display_df.columns and display_df['bb_upper'].notna().any():
                    st.metric("上轨", f"${display_df['bb_upper'].iloc[-1]:.2f}")
                    st.metric("中轨", f"${display_df['bb_middle'].iloc[-1]:.2f}")
                    st.metric("下轨", f"${display_df['bb_lower'].iloc[-1]:.2f}")

        else:
            st.info("该股票没有技术指标数据")

    with tab3:
        if trades:
            buy_trades = [t for t in trades if t.direction.value in ['buy', 'buy_to_open']]
            sell_trades = [t for t in trades if t.direction.value in ['sell', 'sell_to_close']]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("买入次数", len(buy_trades))
                if buy_trades:
                    total_buy_qty = sum(t.filled_quantity for t in buy_trades)
                    st.metric("买入总量", total_buy_qty)

            with col2:
                st.metric("卖出次数", len(sell_trades))
                if sell_trades:
                    total_sell_qty = sum(t.filled_quantity for t in sell_trades)
                    st.metric("卖出总量", total_sell_qty)

            with col3:
                if buy_trades:
                    avg_buy_price = sum(float(t.filled_price) * t.filled_quantity for t in buy_trades) / sum(t.filled_quantity for t in buy_trades)
                    st.metric("平均买入价", f"${avg_buy_price:.2f}")

            with col4:
                if sell_trades:
                    avg_sell_price = sum(float(t.filled_price) * t.filled_quantity for t in sell_trades) / sum(t.filled_quantity for t in sell_trades)
                    st.metric("平均卖出价", f"${avg_sell_price:.2f}")

            st.markdown("---")

            # 交易列表
            st.markdown("**交易列表**")

            trades_data = []
            for trade in trades:
                is_buy = trade.direction.value in ['buy', 'buy_to_open']

                trades_data.append({
                    '时间': trade.filled_time.strftime('%Y-%m-%d %H:%M'),
                    '方向': '买入' if is_buy else '卖出',
                    '数量': trade.filled_quantity,
                    '价格': f"${float(trade.filled_price):.2f}",
                    '金额': f"${float(trade.filled_price) * trade.filled_quantity:,.2f}",
                    '手续费': f"${float(trade.filled_fee):.2f}" if trade.filled_fee else "N/A"
                })

            import pandas as pd
            trades_df = pd.DataFrame(trades_data)
            st.dataframe(trades_df, use_container_width=True, height=300)

        else:
            st.info("该时间范围内没有交易")

    st.markdown("---")

    # 数据质量验证
    st.subheader("✅ 数据质量验证")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**基本检查**")

        # 价格范围检查
        price_ok = (market_df[['open', 'high', 'low', 'close']] > 0).all().all()
        st.write(f"{'✓' if price_ok else '✗'} 价格数据正常")

        # 高低价顺序
        hl_ok = (market_df['high'] >= market_df['low']).all()
        st.write(f"{'✓' if hl_ok else '✗'} 高低价顺序正确")

        # 成交量
        volume_ok = (market_df['volume'] >= 0).all()
        st.write(f"{'✓' if volume_ok else '✗'} 成交量正常")

    with col2:
        st.markdown("**技术指标检查**")

        # RSI
        if 'rsi' in market_df.columns:
            rsi_ok = market_df['rsi'].notna().any() and (market_df['rsi'].dropna().between(0, 100)).all()
            st.write(f"{'✓' if rsi_ok else '✗'} RSI 在 0-100 范围内")

        # MACD
        if 'macd' in market_df.columns:
            macd_ok = market_df['macd'].notna().any()
            st.write(f"{'✓' if macd_ok else '✗'} MACD 数据存在")

        # MA
        if 'ma_20' in market_df.columns:
            ma_ok = market_df['ma_20'].notna().any()
            st.write(f"{'✓' if ma_ok else '✗'} 移动平均线数据存在")

        # BB
        if 'bb_upper' in market_df.columns:
            bb_ok = (market_df['bb_upper'] >= market_df['bb_middle']).all() and \
                    (market_df['bb_middle'] >= market_df['bb_lower']).all()
            st.write(f"{'✓' if bb_ok else '✗'} 布林带顺序正确")

    # 数据完整性
    st.markdown("---")
    st.markdown("**数据完整性**")

    null_counts = market_df.isnull().sum()
    if null_counts.any():
        st.warning("⚠️ 存在缺失值")
        st.dataframe(null_counts[null_counts > 0], use_container_width=True)
    else:
        st.success("✓ 数据完整，无缺失值")

    # 刷新按钮
    st.markdown("---")
    if st.button("🔄 刷新数据", type="primary"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"❌ 加载数据失败: {e}")

    with st.expander("查看错误详情"):
        import traceback
        st.code(traceback.format_exc())
