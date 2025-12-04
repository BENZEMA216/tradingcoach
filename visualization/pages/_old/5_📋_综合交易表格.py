"""
Comprehensive Trading Table Page - Terminal Finance 主题
综合交易表格页面

整合评分、FIFO配对、盈亏分析到一个页面，支持多视图切换
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from visualization.utils.data_loader import get_data_loader
from visualization.styles import inject_global_css

st.set_page_config(page_title="综合交易表格", page_icon="📋", layout="wide")

# 注入全局样式
inject_global_css()

st.title("📋 综合交易表格")
st.markdown("一站式查看所有交易的评分、FIFO配对和盈亏分析")

st.markdown("---")

# ==================== 加载数据 ====================
try:
    loader = get_data_loader()
    df = loader.get_positions_with_trades()

    if len(df) == 0:
        st.warning("暂无已平仓交易数据")
        st.stop()

    # ==================== 全局筛选器 ====================
    with st.expander("🔍 筛选条件", expanded=True):
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            symbols = sorted(df['symbol'].unique().tolist())
            symbol_filter = st.multiselect(
                "股票代码",
                options=symbols,
                default=[],
                placeholder="选择股票..."
            )

        with col2:
            grades = ['B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
            available_grades = [g for g in grades if g in df['grade'].unique()]
            grade_filter = st.multiselect(
                "评分等级",
                options=available_grades,
                default=[],
                placeholder="选择等级..."
            )

        with col3:
            pnl_filter = st.radio(
                "盈亏筛选",
                ["全部", "盈利", "亏损"],
                horizontal=True
            )

        with col4:
            # 时间范围
            min_date = df['open_time'].min().date() if pd.notna(df['open_time'].min()) else datetime.now().date() - timedelta(days=365)
            max_date = df['open_time'].max().date() if pd.notna(df['open_time'].max()) else datetime.now().date()
            date_range = st.date_input(
                "时间范围",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

        with col5:
            score_range = st.slider(
                "评分范围",
                min_value=0,
                max_value=100,
                value=(0, 100)
            )

    # ==================== 应用筛选 ====================
    filtered_df = df.copy()

    # 股票筛选
    if symbol_filter:
        filtered_df = filtered_df[filtered_df['symbol'].isin(symbol_filter)]

    # 等级筛选
    if grade_filter:
        filtered_df = filtered_df[filtered_df['grade'].isin(grade_filter)]

    # 盈亏筛选
    if pnl_filter == "盈利":
        filtered_df = filtered_df[filtered_df['net_pnl'] > 0]
    elif pnl_filter == "亏损":
        filtered_df = filtered_df[filtered_df['net_pnl'] < 0]

    # 时间筛选
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['open_time'].dt.date >= start_date) &
            (filtered_df['open_time'].dt.date <= end_date)
        ]

    # 评分范围筛选
    scored_mask = filtered_df['overall_score'].notna()
    filtered_df = filtered_df[
        (~scored_mask) |  # 保留未评分的
        ((filtered_df['overall_score'] >= score_range[0]) &
         (filtered_df['overall_score'] <= score_range[1]))
    ]

    # ==================== 视图切换 ====================
    st.markdown("---")
    view_mode = st.radio(
        "📊 视图模式",
        ["按时间排序", "按股票分组", "按等级分组", "按盈亏分组"],
        horizontal=True
    )

    # ==================== 统计汇总 ====================
    stat_cols = st.columns(5)
    with stat_cols[0]:
        st.metric("交易数量", f"{len(filtered_df)}")
    with stat_cols[1]:
        avg_score = filtered_df['overall_score'].mean()
        st.metric("平均评分", f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A")
    with stat_cols[2]:
        total_pnl = filtered_df['net_pnl'].sum()
        st.metric("总净盈亏", f"${total_pnl:,.2f}")
    with stat_cols[3]:
        win_count = (filtered_df['net_pnl'] > 0).sum()
        win_rate = win_count / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
        st.metric("胜率", f"{win_rate:.1f}%")
    with stat_cols[4]:
        avg_pnl = filtered_df['net_pnl'].mean()
        st.metric("平均盈亏", f"${avg_pnl:,.2f}" if pd.notna(avg_pnl) else "N/A")

    st.markdown("---")

    # ==================== 三个表格 Tab ====================
    tab1, tab2, tab3 = st.tabs(["⭐ 评分表格", "🔄 FIFO配对表格", "💰 盈亏分析表格"])

    # ==================== Tab1: 评分表格 ====================
    with tab1:
        st.subheader("交易质量评分详情")

        def render_score_table(data_df, group_name=None):
            """渲染评分表格"""
            if len(data_df) == 0:
                st.info("暂无数据")
                return

            if group_name:
                st.markdown(f"#### {group_name}")

            display_df = data_df[[
                'id', 'symbol', 'direction', 'quantity',
                'overall_score', 'grade',
                'entry_score', 'exit_score', 'trend_score', 'risk_score',
                'net_pnl', 'net_pnl_pct'
            ]].copy()

            display_df.columns = [
                'ID', '股票', '方向', '数量',
                '总评分', '等级',
                '进场分', '出场分', '趋势分', '风险分',
                '净盈亏($)', '盈亏率(%)'
            ]

            # 方向中文化
            display_df['方向'] = display_df['方向'].apply(
                lambda x: '做多' if x in ['long', 'buy'] else ('做空' if x in ['short', 'sell'] else x)
            )

            # 样式函数
            def color_grade(val):
                colors = {
                    'A+': 'background-color: #1a5f1a; color: white',
                    'A': 'background-color: #228b22; color: white',
                    'A-': 'background-color: #32cd32; color: white',
                    'B+': 'background-color: #90ee90',
                    'B': 'background-color: #98fb98',
                    'B-': 'background-color: #adff2f',
                    'C+': 'background-color: #ffff00',
                    'C': 'background-color: #ffd700',
                    'C-': 'background-color: #ffa500',
                    'D': 'background-color: #ff6347',
                    'F': 'background-color: #dc143c; color: white'
                }
                return colors.get(val, '')

            def color_pnl(val):
                if pd.isna(val):
                    return ''
                if val > 0:
                    return 'color: #00aa00; font-weight: bold'
                elif val < 0:
                    return 'color: #cc0000; font-weight: bold'
                return ''

            # 应用样式
            styled_df = display_df.style.format({
                '总评分': lambda x: f'{x:.1f}' if pd.notna(x) else '-',
                '进场分': lambda x: f'{x:.1f}' if pd.notna(x) else '-',
                '出场分': lambda x: f'{x:.1f}' if pd.notna(x) else '-',
                '趋势分': lambda x: f'{x:.1f}' if pd.notna(x) else '-',
                '风险分': lambda x: f'{x:.1f}' if pd.notna(x) else '-',
                '净盈亏($)': '${:,.2f}',
                '盈亏率(%)': '{:.2f}%'
            }).applymap(
                color_grade, subset=['等级']
            ).applymap(
                color_pnl, subset=['净盈亏($)', '盈亏率(%)']
            )

            # 对有数据的评分列应用渐变
            if display_df['总评分'].notna().any():
                styled_df = styled_df.background_gradient(
                    subset=['总评分'], cmap='RdYlGn', vmin=40, vmax=80
                )

            st.dataframe(styled_df, use_container_width=True, height=400)

            # 显示统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"共 {len(data_df)} 笔交易")
            with col2:
                avg = data_df['overall_score'].mean()
                st.caption(f"平均评分: {avg:.1f}" if pd.notna(avg) else "平均评分: N/A")
            with col3:
                total = data_df['net_pnl'].sum()
                st.caption(f"总盈亏: ${total:,.2f}")

        # 根据视图模式渲染
        if view_mode == "按时间排序":
            sorted_df = filtered_df.sort_values('open_time', ascending=False)
            render_score_table(sorted_df)

        elif view_mode == "按股票分组":
            for symbol in sorted(filtered_df['symbol'].unique()):
                symbol_df = filtered_df[filtered_df['symbol'] == symbol]
                with st.expander(f"📈 {symbol} ({len(symbol_df)}笔)", expanded=False):
                    render_score_table(symbol_df, None)

        elif view_mode == "按等级分组":
            grade_order = ['B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
            for grade in grade_order:
                grade_df = filtered_df[filtered_df['grade'] == grade]
                if len(grade_df) > 0:
                    win_rate = (grade_df['net_pnl'] > 0).sum() / len(grade_df) * 100
                    with st.expander(f"⭐ {grade} 等级 ({len(grade_df)}笔, 胜率{win_rate:.1f}%)", expanded=False):
                        render_score_table(grade_df, None)

        elif view_mode == "按盈亏分组":
            profit_df = filtered_df[filtered_df['net_pnl'] > 0].sort_values('net_pnl', ascending=False)
            loss_df = filtered_df[filtered_df['net_pnl'] < 0].sort_values('net_pnl', ascending=True)

            with st.expander(f"💚 盈利交易 ({len(profit_df)}笔, 总盈利${profit_df['net_pnl'].sum():,.2f})", expanded=True):
                render_score_table(profit_df, None)

            with st.expander(f"❤️ 亏损交易 ({len(loss_df)}笔, 总亏损${loss_df['net_pnl'].sum():,.2f})", expanded=False):
                render_score_table(loss_df, None)

    # ==================== Tab2: FIFO配对表格 ====================
    with tab2:
        st.subheader("FIFO交易配对详情")
        st.markdown("查看每笔持仓的开仓/平仓交易配对和费用分配")

        def render_fifo_table(data_df, group_name=None):
            """渲染FIFO配对表格"""
            if len(data_df) == 0:
                st.info("暂无数据")
                return

            if group_name:
                st.markdown(f"#### {group_name}")

            display_df = data_df[[
                'id', 'symbol', 'quantity',
                'buy_trade_ids', 'sell_trade_ids',
                'open_price', 'close_price',
                'open_fee', 'close_fee', 'total_fees',
                'realized_pnl', 'net_pnl'
            ]].copy()

            display_df.columns = [
                '持仓ID', '股票', '数量',
                '开仓交易ID', '平仓交易ID',
                '开仓价($)', '平仓价($)',
                '开仓费用($)', '平仓费用($)', '总费用($)',
                '毛盈亏($)', '净盈亏($)'
            ]

            def color_pnl(val):
                if pd.isna(val):
                    return ''
                if val > 0:
                    return 'color: #00aa00; font-weight: bold'
                elif val < 0:
                    return 'color: #cc0000; font-weight: bold'
                return ''

            styled_df = display_df.style.format({
                '开仓价($)': '${:.2f}',
                '平仓价($)': '${:.2f}',
                '开仓费用($)': '${:.2f}',
                '平仓费用($)': '${:.2f}',
                '总费用($)': '${:.2f}',
                '毛盈亏($)': '${:,.2f}',
                '净盈亏($)': '${:,.2f}'
            }).applymap(
                color_pnl, subset=['毛盈亏($)', '净盈亏($)']
            )

            st.dataframe(styled_df, use_container_width=True, height=400)

            # 费用统计
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.caption(f"共 {len(data_df)} 笔持仓")
            with col2:
                st.caption(f"总费用: ${data_df['total_fees'].sum():,.2f}")
            with col3:
                st.caption(f"毛盈亏: ${data_df['realized_pnl'].sum():,.2f}")
            with col4:
                st.caption(f"净盈亏: ${data_df['net_pnl'].sum():,.2f}")

        # 根据视图模式渲染
        if view_mode == "按时间排序":
            sorted_df = filtered_df.sort_values('open_time', ascending=False)
            render_fifo_table(sorted_df)

        elif view_mode == "按股票分组":
            for symbol in sorted(filtered_df['symbol'].unique()):
                symbol_df = filtered_df[filtered_df['symbol'] == symbol]
                with st.expander(f"📈 {symbol} ({len(symbol_df)}笔)", expanded=False):
                    render_fifo_table(symbol_df, None)

        elif view_mode == "按等级分组":
            grade_order = ['B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
            for grade in grade_order:
                grade_df = filtered_df[filtered_df['grade'] == grade]
                if len(grade_df) > 0:
                    with st.expander(f"⭐ {grade} 等级 ({len(grade_df)}笔)", expanded=False):
                        render_fifo_table(grade_df, None)

        elif view_mode == "按盈亏分组":
            profit_df = filtered_df[filtered_df['net_pnl'] > 0].sort_values('net_pnl', ascending=False)
            loss_df = filtered_df[filtered_df['net_pnl'] < 0].sort_values('net_pnl', ascending=True)

            with st.expander(f"💚 盈利交易 ({len(profit_df)}笔)", expanded=True):
                render_fifo_table(profit_df, None)

            with st.expander(f"❤️ 亏损交易 ({len(loss_df)}笔)", expanded=False):
                render_fifo_table(loss_df, None)

        # 交易详情查看
        st.markdown("---")
        st.subheader("🔍 查看交易配对详情")

        col1, col2 = st.columns([1, 3])
        with col1:
            pos_id = st.number_input("输入持仓ID", min_value=1, step=1, key="fifo_pos_id")
            if st.button("查看配对详情", type="primary"):
                trades = loader.get_trades_by_position(pos_id)
                if trades:
                    st.markdown("#### 关联交易列表")
                    trades_df = pd.DataFrame(trades)
                    trades_df['time'] = pd.to_datetime(trades_df['time']).dt.strftime('%Y-%m-%d %H:%M')
                    trades_df.columns = ['交易ID', '方向', '股票', '数量', '价格', '金额', '费用', '时间', '配对交易ID']
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.warning(f"未找到持仓 {pos_id} 的交易记录")

    # ==================== Tab3: 盈亏分析表格 ====================
    with tab3:
        st.subheader("盈亏分析详情")
        st.markdown("查看每笔交易的盈亏、风险指标和持仓效率")

        def render_pnl_table(data_df, group_name=None):
            """渲染盈亏分析表格"""
            if len(data_df) == 0:
                st.info("暂无数据")
                return

            if group_name:
                st.markdown(f"#### {group_name}")

            # 计算日均收益
            data_df = data_df.copy()
            data_df['daily_return'] = data_df.apply(
                lambda x: x['net_pnl_pct'] / x['holding_days'] if x['holding_days'] and x['holding_days'] > 0 else None,
                axis=1
            )

            display_df = data_df[[
                'id', 'symbol', 'holding_days',
                'open_time', 'close_time',
                'net_pnl', 'net_pnl_pct',
                'mae_pct', 'mfe_pct',
                'risk_reward_ratio', 'daily_return'
            ]].copy()

            display_df.columns = [
                'ID', '股票', '持仓天数',
                '开仓时间', '平仓时间',
                '净盈亏($)', '盈亏率(%)',
                'MAE(%)', 'MFE(%)',
                'R/R比', '日均收益(%)'
            ]

            # 格式化时间
            display_df['开仓时间'] = pd.to_datetime(display_df['开仓时间']).dt.strftime('%Y-%m-%d %H:%M')
            display_df['平仓时间'] = pd.to_datetime(display_df['平仓时间']).dt.strftime('%Y-%m-%d %H:%M')

            def color_pnl(val):
                if pd.isna(val):
                    return ''
                if val > 0:
                    return 'color: #00aa00; font-weight: bold'
                elif val < 0:
                    return 'color: #cc0000; font-weight: bold'
                return ''

            def color_mae(val):
                """MAE越小越好（负值）"""
                if pd.isna(val):
                    return ''
                if val > -1:
                    return 'background-color: #90ee90'  # 回撤小
                elif val > -3:
                    return 'background-color: #ffff00'  # 回撤中等
                else:
                    return 'background-color: #ff6347'  # 回撤大

            styled_df = display_df.style.format({
                '净盈亏($)': '${:,.2f}',
                '盈亏率(%)': '{:.2f}%',
                'MAE(%)': lambda x: f'{x:.2f}%' if pd.notna(x) else '-',
                'MFE(%)': lambda x: f'{x:.2f}%' if pd.notna(x) else '-',
                'R/R比': lambda x: f'{x:.2f}' if pd.notna(x) else '-',
                '日均收益(%)': lambda x: f'{x:.3f}%' if pd.notna(x) else '-'
            }).applymap(
                color_pnl, subset=['净盈亏($)', '盈亏率(%)']
            )

            st.dataframe(styled_df, use_container_width=True, height=400)

            # 统计
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_hold = data_df['holding_days'].mean()
                st.caption(f"平均持仓: {avg_hold:.1f}天" if pd.notna(avg_hold) else "平均持仓: N/A")
            with col2:
                avg_mae = data_df['mae_pct'].mean()
                st.caption(f"平均MAE: {avg_mae:.2f}%" if pd.notna(avg_mae) else "平均MAE: N/A")
            with col3:
                avg_mfe = data_df['mfe_pct'].mean()
                st.caption(f"平均MFE: {avg_mfe:.2f}%" if pd.notna(avg_mfe) else "平均MFE: N/A")
            with col4:
                avg_daily = data_df['daily_return'].mean()
                st.caption(f"平均日收益: {avg_daily:.3f}%" if pd.notna(avg_daily) else "平均日收益: N/A")

        # 根据视图模式渲染
        if view_mode == "按时间排序":
            sorted_df = filtered_df.sort_values('open_time', ascending=False)
            render_pnl_table(sorted_df)

        elif view_mode == "按股票分组":
            for symbol in sorted(filtered_df['symbol'].unique()):
                symbol_df = filtered_df[filtered_df['symbol'] == symbol]
                with st.expander(f"📈 {symbol} ({len(symbol_df)}笔)", expanded=False):
                    render_pnl_table(symbol_df, None)

        elif view_mode == "按等级分组":
            grade_order = ['B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
            for grade in grade_order:
                grade_df = filtered_df[filtered_df['grade'] == grade]
                if len(grade_df) > 0:
                    with st.expander(f"⭐ {grade} 等级 ({len(grade_df)}笔)", expanded=False):
                        render_pnl_table(grade_df, None)

        elif view_mode == "按盈亏分组":
            profit_df = filtered_df[filtered_df['net_pnl'] > 0].sort_values('net_pnl', ascending=False)
            loss_df = filtered_df[filtered_df['net_pnl'] < 0].sort_values('net_pnl', ascending=True)

            with st.expander(f"💚 盈利交易 ({len(profit_df)}笔)", expanded=True):
                render_pnl_table(profit_df, None)

            with st.expander(f"❤️ 亏损交易 ({len(loss_df)}笔)", expanded=False):
                render_pnl_table(loss_df, None)

    # ==================== 导出功能 ====================
    st.markdown("---")
    st.subheader("📥 导出数据")

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_all = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="导出完整数据 (CSV)",
            data=csv_all,
            file_name=f"trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with col2:
        # 导出评分数据
        score_cols = ['id', 'symbol', 'direction', 'quantity', 'overall_score', 'grade',
                      'entry_score', 'exit_score', 'trend_score', 'risk_score', 'net_pnl', 'net_pnl_pct']
        csv_scores = filtered_df[score_cols].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="导出评分数据 (CSV)",
            data=csv_scores,
            file_name=f"trading_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with col3:
        # 导出FIFO数据
        fifo_cols = ['id', 'symbol', 'quantity', 'buy_trade_ids', 'sell_trade_ids',
                     'open_price', 'close_price', 'open_fee', 'close_fee', 'total_fees',
                     'realized_pnl', 'net_pnl']
        csv_fifo = filtered_df[fifo_cols].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="导出FIFO数据 (CSV)",
            data=csv_fifo,
            file_name=f"fifo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    # ==================== 刷新按钮 ====================
    st.markdown("---")
    if st.button("🔄 刷新数据", type="primary"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"加载数据失败: {e}")

    with st.expander("查看错误详情"):
        import traceback
        st.code(traceback.format_exc())
