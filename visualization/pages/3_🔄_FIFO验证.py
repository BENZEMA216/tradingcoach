"""
FIFO Verification Page
FIFO验证页面
"""

import streamlit as st
import sys
from pathlib import Path
from collections import deque

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from visualization.utils.data_loader import get_data_loader
from visualization.components.charts import create_fifo_timeline_chart

st.set_page_config(page_title="FIFO验证", page_icon="🔄", layout="wide")

st.title("🔄 FIFO 匹配验证")
st.markdown("可视化先进先出(FIFO)匹配过程，验证系统逻辑")

st.markdown("---")

# 加载数据
try:
    loader = get_data_loader()
    symbols = loader.get_all_symbols()

    if len(symbols) == 0:
        st.warning("⚠️ 数据库中没有交易记录")
        st.stop()

    # 选择股票
    st.subheader("📌 选择股票")

    col1, col2 = st.columns([3, 1])

    with col1:
        selected_symbol = st.selectbox(
            "股票代码",
            symbols,
            help="选择要验证的股票代码"
        )

    with col2:
        # 获取该股票的交易数量
        trades = loader.get_symbol_trades(selected_symbol)
        st.metric("交易数量", len(trades))

    if not selected_symbol:
        st.info("请选择股票代码")
        st.stop()

    st.markdown("---")

    # 获取数据
    trades = loader.get_symbol_trades(selected_symbol)
    positions = loader.get_symbol_positions(selected_symbol)

    if len(trades) == 0:
        st.warning(f"股票 {selected_symbol} 没有交易记录")
        st.stop()

    # 交易概览
    st.subheader(f"📊 {selected_symbol} 交易概览")

    col1, col2, col3, col4 = st.columns(4)

    buy_trades = [t for t in trades if t.direction.value in ['buy', 'buy_to_open']]
    sell_trades = [t for t in trades if t.direction.value in ['sell', 'sell_to_close']]

    with col1:
        st.metric("买入交易", len(buy_trades))

    with col2:
        st.metric("卖出交易", len(sell_trades))

    with col3:
        st.metric("生成持仓", len(positions))

    with col4:
        closed_positions = [p for p in positions if p.status.value == 'closed']
        st.metric("已平仓", len(closed_positions))

    st.markdown("---")

    # 交易序列
    st.subheader("📋 交易序列（按时间顺序）")

    # 显示交易列表
    trades_data = []
    cumulative_qty = 0

    for trade in trades:
        is_buy = trade.direction.value in ['buy', 'buy_to_open']

        if is_buy:
            cumulative_qty += trade.filled_quantity
            direction_display = "🟢 买入"
        else:
            cumulative_qty -= trade.filled_quantity
            direction_display = "🔴 卖出"

        trades_data.append({
            '时间': trade.filled_time.strftime('%Y-%m-%d %H:%M:%S'),
            '方向': direction_display,
            '数量': trade.filled_quantity,
            '价格': f"${float(trade.filled_price):.2f}",
            '手续费': f"${float(trade.filled_fee):.2f}" if trade.filled_fee else "N/A",
            '累计持仓': cumulative_qty
        })

    import pandas as pd
    trades_df = pd.DataFrame(trades_data)
    st.dataframe(trades_df, use_container_width=True, height=300)

    st.markdown("---")

    # 手动FIFO匹配模拟
    st.subheader("🔄 FIFO 匹配过程（手动模拟）")

    # 执行手动FIFO匹配
    manual_positions = []
    open_queue = deque()

    for trade in trades:
        is_buy = trade.direction.value in ['buy', 'buy_to_open']

        if is_buy:
            # 买入：加入队列
            open_queue.append({
                'trade': trade,
                'remaining_qty': trade.filled_quantity
            })
        else:
            # 卖出：从队列头部开始匹配
            sell_remaining = trade.filled_quantity

            while sell_remaining > 0 and open_queue:
                buy_entry = open_queue[0]
                match_qty = min(sell_remaining, buy_entry['remaining_qty'])

                # 创建匹配记录
                buy_trade = buy_entry['trade']

                entry_fee = float(buy_trade.filled_fee or 0) * (match_qty / buy_trade.filled_quantity)
                exit_fee = float(trade.filled_fee or 0) * (match_qty / trade.filled_quantity)

                pnl = (float(trade.filled_price) - float(buy_trade.filled_price)) * match_qty
                net_pnl = pnl - entry_fee - exit_fee

                manual_positions.append({
                    'buy_trade': buy_trade,
                    'sell_trade': trade,
                    'quantity': match_qty,
                    'entry_price': float(buy_trade.filled_price),
                    'exit_price': float(trade.filled_price),
                    'entry_fee': entry_fee,
                    'exit_fee': exit_fee,
                    'pnl': pnl,
                    'net_pnl': net_pnl
                })

                # 更新剩余数量
                buy_entry['remaining_qty'] -= match_qty
                sell_remaining -= match_qty

                # 如果买入交易完全匹配，移出队列
                if buy_entry['remaining_qty'] == 0:
                    open_queue.popleft()

    # 显示匹配过程
    if manual_positions:
        for i, match in enumerate(manual_positions, 1):
            with st.expander(f"匹配 #{i}: {match['quantity']} 股"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**开仓交易**")
                    st.write(f"时间: {match['buy_trade'].filled_time}")
                    st.write(f"方向: 买入")
                    st.write(f"数量: {match['buy_trade'].filled_quantity}")
                    st.write(f"价格: ${match['entry_price']:.2f}")
                    st.write(f"手续费分配: ${match['entry_fee']:.2f}")

                with col2:
                    st.markdown("**平仓交易**")
                    st.write(f"时间: {match['sell_trade'].filled_time}")
                    st.write(f"方向: 卖出")
                    st.write(f"数量: {match['sell_trade'].filled_quantity}")
                    st.write(f"价格: ${match['exit_price']:.2f}")
                    st.write(f"手续费分配: ${match['exit_fee']:.2f}")

                st.markdown("---")
                st.markdown("**计算结果**")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("匹配数量", f"{match['quantity']} 股")

                with col2:
                    st.metric("盈亏", f"${match['pnl']:.2f}")

                with col3:
                    pnl_color = "normal" if match['net_pnl'] >= 0 else "inverse"
                    st.metric("净盈亏", f"${match['net_pnl']:.2f}", delta_color=pnl_color)

                # 详细计算公式
                st.markdown("**计算详情**")
                st.code(f"""
进场价格: ${match['entry_price']:.2f}
出场价格: ${match['exit_price']:.2f}
进场手续费: ${match['entry_fee']:.2f}
出场手续费: ${match['exit_fee']:.2f}
盈亏: ({match['exit_price']:.2f} - {match['entry_price']:.2f}) × {match['quantity']} = ${match['pnl']:.2f}
净盈亏: ${match['pnl']:.2f} - ${match['entry_fee']:.2f} - ${match['exit_fee']:.2f} = ${match['net_pnl']:.2f}
                """)

    else:
        st.info("没有已匹配的持仓")

    # 未平仓持仓
    if open_queue:
        st.markdown("---")
        st.subheader("📦 未平仓持仓")

        for i, entry in enumerate(open_queue, 1):
            st.write(f"**#{i}**: 买入 {entry['remaining_qty']} @ ${float(entry['trade'].filled_price):.2f} ({entry['trade'].filled_time.date()})")

    st.markdown("---")

    # 对比数据库持仓
    st.subheader("✅ 数据库持仓记录对比")

    if positions:
        comparison_data = []

        for i, pos in enumerate(positions, 1):
            # 尝试找到对应的手动匹配
            matched = False
            status = "⚠️ 未匹配"

            if i <= len(manual_positions):
                manual_pos = manual_positions[i-1]

                # 对比数量、价格、盈亏
                qty_match = pos.quantity == manual_pos['quantity']
                entry_match = abs(float(pos.open_price) - manual_pos['entry_price']) < 0.01
                exit_match = abs(float(pos.close_price or 0) - manual_pos['exit_price']) < 0.01 if pos.close_price else True

                if pos.net_pnl:
                    pnl_match = abs(float(pos.net_pnl) - manual_pos['net_pnl']) < 0.01
                else:
                    pnl_match = False

                if qty_match and entry_match and exit_match and pnl_match:
                    status = "✓ 完全匹配"
                    matched = True
                elif qty_match and entry_match:
                    status = "⚠️ 部分匹配"
                else:
                    status = "✗ 不匹配"

            comparison_data.append({
                '#': i,
                'Position ID': pos.id,
                '数量': pos.quantity,
                '进场价': f"${float(pos.open_price):.2f}",
                '出场价': f"${float(pos.close_price):.2f}" if pos.close_price else "N/A",
                '净盈亏': f"${float(pos.net_pnl):.2f}" if pos.net_pnl else "N/A",
                '状态': status
            })

        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)

        # 验证总结
        matched_count = sum(1 for d in comparison_data if '完全匹配' in d['状态'])
        total_count = len(comparison_data)

        if matched_count == total_count:
            st.success(f"✅ 验证通过！所有 {total_count} 个持仓完全匹配")
        else:
            st.warning(f"⚠️ {matched_count}/{total_count} 个持仓完全匹配")

    else:
        st.info("该股票没有持仓记录")

    st.markdown("---")

    # 交易时间轴
    st.subheader("📈 交易时间轴")

    fig_timeline = create_fifo_timeline_chart(trades, positions)
    st.plotly_chart(fig_timeline, use_container_width=True)

    # 验证检查清单
    st.markdown("---")
    st.subheader("📝 验证检查清单")

    checks = [
        ("FIFO顺序", "最早的买入交易被最先匹配"),
        ("数量匹配", "买入数量 = 卖出数量（对于已平仓）"),
        ("手续费分配", "手续费按比例正确分配"),
        ("盈亏计算", "盈亏 = (出场价 - 进场价) × 数量"),
        ("净盈亏计算", "净盈亏 = 盈亏 - 总手续费"),
        ("价格匹配", "进场价/出场价正确对应交易价格"),
    ]

    for check, desc in checks:
        st.checkbox(check, help=desc, key=check)

except Exception as e:
    st.error(f"❌ 加载数据失败: {e}")

    with st.expander("查看错误详情"):
        import traceback
        st.code(traceback.format_exc())
