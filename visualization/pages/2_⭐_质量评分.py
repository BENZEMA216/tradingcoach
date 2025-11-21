"""
Quality Scoring Page
质量评分页面
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

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

st.set_page_config(page_title="质量评分", page_icon="⭐", layout="wide")

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
        st.subheader("详细持仓列表")

        # 筛选选项
        col1, col2, col3 = st.columns(3)

        with col1:
            symbol_filter = st.selectbox(
                "股票代码",
                ["全部"] + sorted(df['symbol'].unique().tolist())
            )

        with col2:
            grade_filter = st.selectbox(
                "等级",
                ["全部"] + sorted(df['grade'].unique().tolist())
            )

        with col3:
            pnl_filter = st.selectbox(
                "盈亏",
                ["全部", "盈利", "亏损"]
            )

        # 应用筛选
        filtered_df = df.copy()

        if symbol_filter != "全部":
            filtered_df = filtered_df[filtered_df['symbol'] == symbol_filter]

        if grade_filter != "全部":
            filtered_df = filtered_df[filtered_df['grade'] == grade_filter]

        if pnl_filter == "盈利":
            filtered_df = filtered_df[filtered_df['net_pnl'] > 0]
        elif pnl_filter == "亏损":
            filtered_df = filtered_df[filtered_df['net_pnl'] < 0]

        # 排序
        sort_col = st.selectbox(
            "排序",
            ["overall_score", "net_pnl", "net_pnl_pct", "open_time"],
            format_func=lambda x: {
                'overall_score': '总体评分',
                'net_pnl': '净盈亏',
                'net_pnl_pct': '盈亏率',
                'open_time': '开仓时间'
            }[x]
        )

        sort_order = st.radio("排序方向", ["降序", "升序"], horizontal=True)
        filtered_df = filtered_df.sort_values(sort_col, ascending=(sort_order == "升序"))

        # 显示表格
        st.markdown(f"**显示 {len(filtered_df)} / {len(df)} 个持仓**")

        # 格式化显示
        display_df = filtered_df[[
            'id', 'symbol', 'quantity', 'open_price', 'close_price',
            'net_pnl', 'net_pnl_pct', 'overall_score', 'grade',
            'entry_score', 'exit_score', 'trend_score', 'risk_score',
            'holding_days'
        ]].head(100)

        # 重命名列
        display_df.columns = [
            'ID', '股票', '数量', '进场价', '出场价',
            '净盈亏', '盈亏率(%)', '总分', '等级',
            '进场', '出场', '趋势', '风险', '持仓天数'
        ]

        st.dataframe(
            display_df.style.format({
                '进场价': '${:.2f}',
                '出场价': '${:.2f}',
                '净盈亏': '${:,.2f}',
                '盈亏率(%)': '{:.2f}%',
                '总分': '{:.1f}',
                '进场': '{:.1f}',
                '出场': '{:.1f}',
                '趋势': '{:.1f}',
                '风险': '{:.1f}'
            }).background_gradient(subset=['总分'], cmap='RdYlGn', vmin=0, vmax=100),
            use_container_width=True,
            height=400
        )

        # 详情查看
        st.markdown("---")
        st.subheader("🔍 查看持仓详情")

        position_id = st.number_input("输入持仓ID", min_value=1, step=1)

        if st.button("查看详情"):
            pos = loader.get_position_by_id(position_id)

            if pos:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"### 持仓 ID: {pos.id}")
                    st.markdown(f"**股票**: {pos.symbol}")
                    st.markdown(f"**数量**: {pos.quantity}")
                    st.markdown(f"**进场价**: ${float(pos.open_price):.2f}")
                    st.markdown(f"**出场价**: ${float(pos.close_price):.2f}" if pos.close_price else "未平仓")
                    st.markdown(f"**净盈亏**: ${float(pos.net_pnl):.2f}" if pos.net_pnl else "N/A")
                    st.markdown(f"**盈亏率**: {float(pos.net_pnl_pct):.2f}%" if pos.net_pnl_pct else "N/A")
                    st.markdown(f"**持仓天数**: {pos.holding_period_days}" if pos.holding_period_days else "N/A")

                with col2:
                    st.markdown("### 质量评分")
                    st.markdown(f"**总体评分**: {float(pos.overall_score):.2f}" if pos.overall_score else "未评分")
                    st.markdown(f"**等级**: {pos.score_grade}" if pos.score_grade else "N/A")

                    if pos.entry_quality_score:
                        st.markdown("---")
                        st.markdown(dimension_scores_table(
                            float(pos.entry_quality_score),
                            float(pos.exit_quality_score),
                            float(pos.trend_quality_score),
                            float(pos.risk_mgmt_score)
                        ), unsafe_allow_html=True)

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
