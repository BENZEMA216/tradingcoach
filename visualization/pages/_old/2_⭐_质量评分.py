"""
Quality Scoring Page - Terminal Finance 主题
质量评分页面
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from visualization.utils.data_loader import get_data_loader
from visualization.components.charts import (
    create_score_distribution_chart,
    create_grade_distribution_chart,
    create_dimension_radar_chart,
    create_pnl_vs_score_scatter,
    create_score_trend_chart
)
from visualization.components.metrics import grade_badge, pnl_badge, percentage_badge, dimension_scores_table
from visualization.styles import inject_global_css, COLORS, FONTS

st.set_page_config(page_title="质量评分", page_icon="⭐", layout="wide")

# 注入全局样式
inject_global_css()

st.title("⭐ 质量评分分析")
st.markdown("深入分析交易质量评分，发现优秀交易模式")

st.markdown("---")

# 加载数据
try:
    loader = get_data_loader()
    df = loader.get_quality_scores()

    if len(df) == 0:
        st.warning("⚠️ 尚未进行质量评分")
        st.info("请运行命令: `python3 scripts/score_positions.py --all`")
        st.stop()

    # 总体统计
    st.subheader("📊 总体统计")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("已评分持仓", f"{len(df):,}")

    with col2:
        avg_score = df['overall_score'].mean()
        st.metric("平均评分", f"{avg_score:.2f}")

    with col3:
        winning_pct = (df['net_pnl'] > 0).sum() / len(df) * 100
        st.metric("胜率", f"{winning_pct:.1f}%")

    with col4:
        total_pnl = df['net_pnl'].sum()
        pnl_color = "normal" if total_pnl >= 0 else "inverse"
        st.metric("总净盈亏", f"${total_pnl:,.2f}", delta_color=pnl_color)

    with col5:
        avg_pnl_pct = df['net_pnl_pct'].mean()
        st.metric("平均盈亏率", f"{avg_pnl_pct:.2f}%")

    st.markdown("---")

    # 图表区域
    tab1, tab2, tab3, tab4 = st.tabs(["📈 分布分析", "🎯 维度分析", "💰 盈亏分析", "📋 详细列表"])

    with tab1:
        st.subheader("评分分布")

        col1, col2 = st.columns(2)

        with col1:
            # 评分分布直方图
            fig_dist = create_score_distribution_chart(df)
            st.plotly_chart(fig_dist, use_container_width=True)

        with col2:
            # 等级分布饼图
            fig_grade = create_grade_distribution_chart(df)
            st.plotly_chart(fig_grade, use_container_width=True)

        # 等级统计表
        st.subheader("等级详细统计")

        grade_stats = df.groupby('grade').agg({
            'id': 'count',
            'net_pnl': ['sum', 'mean'],
            'net_pnl_pct': 'mean',
            'overall_score': 'mean'
        }).round(2)

        grade_stats.columns = ['数量', '总盈亏', '平均盈亏', '平均盈亏率', '平均评分']
        grade_stats = grade_stats.sort_index()

        # 计算胜率
        win_rates = df.groupby('grade').apply(
            lambda x: (x['net_pnl'] > 0).sum() / len(x) * 100
        ).round(1)
        grade_stats['胜率 (%)'] = win_rates

        st.dataframe(grade_stats, use_container_width=True)

    with tab2:
        st.subheader("四维度分析")

        col1, col2 = st.columns([1, 1])

        with col1:
            # 雷达图
            fig_radar = create_dimension_radar_chart(df)
            st.plotly_chart(fig_radar, use_container_width=True)

        with col2:
            # 维度平均分
            st.markdown("### 维度平均分")

            dimensions = {
                '进场质量 (30%)': df['entry_score'].mean(),
                '出场质量 (25%)': df['exit_score'].mean(),
                '趋势质量 (25%)': df['trend_score'].mean(),
                '风险管理 (20%)': df['risk_score'].mean()
            }

            for dim, score in dimensions.items():
                st.metric(dim, f"{score:.2f}")

        # 维度对比分析
        st.markdown("---")
        st.subheader("维度相关性分析")

        import plotly.express as px

        # 创建散点矩阵
        fig_matrix = px.scatter_matrix(
            df,
            dimensions=['entry_score', 'exit_score', 'trend_score', 'risk_score', 'net_pnl_pct'],
            labels={
                'entry_score': '进场',
                'exit_score': '出场',
                'trend_score': '趋势',
                'risk_score': '风险',
                'net_pnl_pct': '盈亏率'
            },
            title='维度相关性矩阵',
            height=600
        )

        st.plotly_chart(fig_matrix, use_container_width=True)

    with tab3:
        st.subheader("盈亏 vs 评分关系")

        # 散点图
        fig_scatter = create_pnl_vs_score_scatter(df)
        st.plotly_chart(fig_scatter, use_container_width=True)

        # 评分趋势
        st.subheader("评分时间趋势")
        fig_trend = create_score_trend_chart(df)
        st.plotly_chart(fig_trend, use_container_width=True)

        # 统计分析
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 高分交易 (≥80分)")
            high_score_df = df[df['overall_score'] >= 80]
            if len(high_score_df) > 0:
                st.metric("数量", len(high_score_df))
                st.metric("平均盈亏", f"${high_score_df['net_pnl'].mean():,.2f}")
                st.metric("胜率", f"{(high_score_df['net_pnl'] > 0).sum() / len(high_score_df) * 100:.1f}%")
            else:
                st.info("暂无高分交易")

        with col2:
            st.markdown("### 低分交易 (<50分)")
            low_score_df = df[df['overall_score'] < 50]
            if len(low_score_df) > 0:
                st.metric("数量", len(low_score_df))
                st.metric("平均盈亏", f"${low_score_df['net_pnl'].mean():,.2f}")
                st.metric("胜率", f"{(low_score_df['net_pnl'] > 0).sum() / len(low_score_df) * 100:.1f}%")
            else:
                st.info("暂无低分交易")

    with tab4:
        st.subheader("📋 全部交易评分表格")
        st.markdown("查看每一笔交易的详细评分信息，支持搜索、筛选和导出")

        # 筛选区域 - 使用expander折叠
        with st.expander("🔍 筛选条件", expanded=True):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # 股票代码搜索
                symbol_search = st.text_input("搜索股票代码", placeholder="输入代码...")
                symbol_list = sorted(df['symbol'].unique().tolist())
                if symbol_search:
                    symbol_list = [s for s in symbol_list if symbol_search.upper() in s.upper()]
                symbol_filter = st.selectbox(
                    "选择股票",
                    ["全部"] + symbol_list,
                    key="symbol_filter_tab4"
                )

            with col2:
                grade_filter = st.selectbox(
                    "等级筛选",
                    ["全部", "A级(85+)", "B级(70-84)", "C级(55-69)", "D级(50-54)", "F级(<50)"],
                    key="grade_filter_tab4"
                )

            with col3:
                pnl_filter = st.selectbox(
                    "盈亏筛选",
                    ["全部", "盈利", "亏损"],
                    key="pnl_filter_tab4"
                )

            with col4:
                score_range = st.slider(
                    "评分范围",
                    min_value=0,
                    max_value=100,
                    value=(0, 100),
                    key="score_range_tab4"
                )

        # 应用筛选
        filtered_df = df.copy()

        if symbol_filter != "全部":
            filtered_df = filtered_df[filtered_df['symbol'] == symbol_filter]

        if grade_filter == "A级(85+)":
            filtered_df = filtered_df[filtered_df['overall_score'] >= 85]
        elif grade_filter == "B级(70-84)":
            filtered_df = filtered_df[(filtered_df['overall_score'] >= 70) & (filtered_df['overall_score'] < 85)]
        elif grade_filter == "C级(55-69)":
            filtered_df = filtered_df[(filtered_df['overall_score'] >= 55) & (filtered_df['overall_score'] < 70)]
        elif grade_filter == "D级(50-54)":
            filtered_df = filtered_df[(filtered_df['overall_score'] >= 50) & (filtered_df['overall_score'] < 55)]
        elif grade_filter == "F级(<50)":
            filtered_df = filtered_df[filtered_df['overall_score'] < 50]

        if pnl_filter == "盈利":
            filtered_df = filtered_df[filtered_df['net_pnl'] > 0]
        elif pnl_filter == "亏损":
            filtered_df = filtered_df[filtered_df['net_pnl'] < 0]

        # 应用评分范围筛选
        filtered_df = filtered_df[
            (filtered_df['overall_score'] >= score_range[0]) &
            (filtered_df['overall_score'] <= score_range[1])
        ]

        # 排序选项
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            sort_col = st.selectbox(
                "排序字段",
                ["overall_score", "net_pnl", "net_pnl_pct", "open_time", "entry_score", "exit_score", "trend_score", "risk_score"],
                format_func=lambda x: {
                    'overall_score': '总体评分',
                    'net_pnl': '净盈亏',
                    'net_pnl_pct': '盈亏率',
                    'open_time': '开仓时间',
                    'entry_score': '进场评分',
                    'exit_score': '出场评分',
                    'trend_score': '趋势评分',
                    'risk_score': '风险评分'
                }[x],
                key="sort_col_tab4"
            )

        with col2:
            sort_order = st.radio("排序方向", ["降序", "升序"], horizontal=True, key="sort_order_tab4")

        with col3:
            show_all = st.checkbox("显示全部", value=False, key="show_all_tab4")

        filtered_df = filtered_df.sort_values(sort_col, ascending=(sort_order == "升序"))

        # 统计信息
        st.markdown("---")
        stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)
        with stat_col1:
            st.metric("筛选结果", f"{len(filtered_df)} 笔")
        with stat_col2:
            if len(filtered_df) > 0:
                st.metric("平均评分", f"{filtered_df['overall_score'].mean():.1f}")
        with stat_col3:
            if len(filtered_df) > 0:
                st.metric("总盈亏", f"${filtered_df['net_pnl'].sum():,.2f}")
        with stat_col4:
            if len(filtered_df) > 0:
                win_rate = (filtered_df['net_pnl'] > 0).sum() / len(filtered_df) * 100
                st.metric("胜率", f"{win_rate:.1f}%")
        with stat_col5:
            if len(filtered_df) > 0:
                st.metric("平均盈亏", f"${filtered_df['net_pnl'].mean():,.2f}")

        # 显示条数限制
        display_limit = len(filtered_df) if show_all else min(100, len(filtered_df))

        # 格式化显示
        display_df = filtered_df[[
            'id', 'symbol', 'quantity', 'open_price', 'close_price',
            'net_pnl', 'net_pnl_pct', 'overall_score', 'grade',
            'entry_score', 'exit_score', 'trend_score', 'risk_score',
            'holding_days', 'open_time', 'close_time'
        ]].head(display_limit).copy()

        # 重命名列
        display_df.columns = [
            'ID', '股票代码', '数量', '进场价', '出场价',
            '净盈亏($)', '盈亏率(%)', '总评分', '等级',
            '进场分', '出场分', '趋势分', '风险分',
            '持仓天数', '开仓时间', '平仓时间'
        ]

        # 格式化时间列
        display_df['开仓时间'] = pd.to_datetime(display_df['开仓时间']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['平仓时间'] = pd.to_datetime(display_df['平仓时间']).dt.strftime('%Y-%m-%d %H:%M')

        # 创建样式函数
        def color_grade(val):
            """根据等级设置颜色"""
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
            """根据盈亏设置颜色"""
            if pd.isna(val):
                return ''
            if val > 0:
                return 'color: #00aa00; font-weight: bold'
            elif val < 0:
                return 'color: #cc0000; font-weight: bold'
            return ''

        # 应用样式
        styled_df = display_df.style.format({
            '进场价': '${:.2f}',
            '出场价': '${:.2f}',
            '净盈亏($)': '${:,.2f}',
            '盈亏率(%)': '{:.2f}%',
            '总评分': '{:.1f}',
            '进场分': '{:.1f}',
            '出场分': '{:.1f}',
            '趋势分': '{:.1f}',
            '风险分': '{:.1f}'
        }).applymap(
            color_grade, subset=['等级']
        ).applymap(
            color_pnl, subset=['净盈亏($)', '盈亏率(%)']
        ).background_gradient(
            subset=['总评分'], cmap='RdYlGn', vmin=40, vmax=80
        ).background_gradient(
            subset=['进场分', '出场分', '趋势分', '风险分'], cmap='Blues', vmin=40, vmax=80
        )

        # 显示表格
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600
        )

        # 导出功能
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            # 导出CSV
            csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 导出CSV",
                data=csv,
                file_name=f"trading_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        # 详情查看区域
        st.markdown("---")
        st.subheader("🔍 查看单笔交易详情")

        col1, col2 = st.columns([1, 3])
        with col1:
            position_id = st.number_input("输入持仓ID", min_value=1, step=1, key="pos_id_input")
            view_btn = st.button("查看详情", type="primary")

        if view_btn:
            pos = loader.get_position_by_id(position_id)

            if pos:
                st.markdown("---")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("### 📊 基本信息")
                    st.markdown(f"**持仓ID**: {pos.id}")
                    st.markdown(f"**股票代码**: {pos.symbol}")
                    st.markdown(f"**持仓方向**: {'做多' if pos.direction == 'long' else '做空'}")
                    st.markdown(f"**数量**: {pos.quantity}")
                    st.markdown(f"**持仓天数**: {pos.holding_period_days or 'N/A'}")

                with col2:
                    st.markdown("### 💰 盈亏信息")
                    st.markdown(f"**进场价**: ${float(pos.open_price):.2f}")
                    st.markdown(f"**出场价**: ${float(pos.close_price):.2f}" if pos.close_price else "**出场价**: 未平仓")
                    pnl_color = "green" if pos.net_pnl and float(pos.net_pnl) > 0 else "red"
                    st.markdown(f"**净盈亏**: <span style='color:{pnl_color};font-weight:bold'>${float(pos.net_pnl):,.2f}</span>" if pos.net_pnl else "**净盈亏**: N/A", unsafe_allow_html=True)
                    st.markdown(f"**盈亏率**: <span style='color:{pnl_color};font-weight:bold'>{float(pos.net_pnl_pct):.2f}%</span>" if pos.net_pnl_pct else "**盈亏率**: N/A", unsafe_allow_html=True)

                with col3:
                    st.markdown("### ⭐ 质量评分")
                    if pos.overall_score:
                        grade_colors = {
                            'A+': '#1a5f1a', 'A': '#228b22', 'A-': '#32cd32',
                            'B+': '#90ee90', 'B': '#98fb98', 'B-': '#adff2f',
                            'C+': '#ffd700', 'C': '#ffa500', 'C-': '#ff8c00',
                            'D': '#ff6347', 'F': '#dc143c'
                        }
                        grade_color = grade_colors.get(pos.score_grade, '#666')
                        st.markdown(f"**总体评分**: {float(pos.overall_score):.1f}")
                        st.markdown(f"**等级**: <span style='background-color:{grade_color};padding:2px 8px;border-radius:4px;font-weight:bold'>{pos.score_grade}</span>", unsafe_allow_html=True)
                    else:
                        st.warning("未评分")

                # 四维度评分详情
                if pos.entry_quality_score:
                    st.markdown("---")
                    st.markdown("### 📈 四维度评分详情")

                    score_col1, score_col2, score_col3, score_col4 = st.columns(4)

                    with score_col1:
                        entry = float(pos.entry_quality_score)
                        st.metric("进场质量 (30%)", f"{entry:.1f}", delta=f"{entry-60:.1f}" if entry != 60 else None)

                    with score_col2:
                        exit_s = float(pos.exit_quality_score)
                        st.metric("出场质量 (25%)", f"{exit_s:.1f}", delta=f"{exit_s-60:.1f}" if exit_s != 60 else None)

                    with score_col3:
                        trend = float(pos.trend_quality_score)
                        st.metric("趋势把握 (25%)", f"{trend:.1f}", delta=f"{trend-60:.1f}" if trend != 60 else None)

                    with score_col4:
                        risk = float(pos.risk_mgmt_score)
                        st.metric("风险管理 (20%)", f"{risk:.1f}", delta=f"{risk-60:.1f}" if risk != 60 else None)

                    # 评分条形图
                    import plotly.graph_objects as go

                    fig = go.Figure()
                    dimensions = ['进场质量', '出场质量', '趋势把握', '风险管理']
                    scores = [entry, exit_s, trend, risk]
                    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c']

                    fig.add_trace(go.Bar(
                        x=dimensions,
                        y=scores,
                        marker_color=colors,
                        text=[f'{s:.1f}' for s in scores],
                        textposition='auto'
                    ))

                    fig.update_layout(
                        title='四维度评分对比',
                        yaxis_title='评分',
                        yaxis_range=[0, 100],
                        height=300,
                        showlegend=False
                    )

                    # 添加60分参考线
                    fig.add_hline(y=60, line_dash="dash", line_color="gray", annotation_text="平均线(60)")

                    st.plotly_chart(fig, use_container_width=True)

            else:
                st.error(f"未找到持仓 ID: {position_id}")

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
