"""
Data Overview Page - Terminal Finance 主题
数据概览页面
"""

import streamlit as st
import sys
from pathlib import Path

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from visualization.utils.data_loader import get_data_loader
from visualization.components.metrics import status_badge
from visualization.styles import inject_global_css, COLORS, FONTS

st.set_page_config(page_title="数据概览", page_icon="📊", layout="wide")

# 注入全局样式
inject_global_css()

st.title("📊 数据概览")
st.markdown("查看系统整体数据状态，检查市场数据覆盖率")

st.markdown("---")

# 加载数据
try:
    loader = get_data_loader()
    stats = loader.get_overview_stats()
    coverage_df = loader.get_data_coverage()

    # 概览卡片
    st.subheader("📈 总体统计")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("交易记录", f"{stats['total_trades']:,}")

    with col2:
        st.metric("总持仓", f"{stats['total_positions']:,}")
        st.caption(f"已平仓: {stats['closed_positions']} | 未平仓: {stats['open_positions']}")

    with col3:
        coverage_pct = (stats['symbols_with_data'] / max(stats['total_symbols'], 1)) * 100
        st.metric(
            "数据覆盖率",
            f"{coverage_pct:.1f}%",
            delta=f"{stats['symbols_with_data']}/{stats['total_symbols']} 股票"
        )

    with col4:
        score_pct = (stats['scored_positions'] / max(stats['closed_positions'], 1)) * 100
        st.metric(
            "已评分",
            f"{stats['scored_positions']:,}",
            delta=f"{score_pct:.1f}%"
        )

    with col5:
        pnl_color = "normal" if stats['total_net_pnl'] >= 0 else "inverse"
        st.metric(
            "总净盈亏",
            f"${stats['total_net_pnl']:,.2f}",
            delta=f"胜率 {stats['win_rate']:.1f}%",
            delta_color=pnl_color
        )

    st.markdown("---")

    # 数据覆盖率分析
    st.subheader("🔍 市场数据覆盖率")

    # 分类统计
    has_data_count = coverage_df['has_data'].sum()
    missing_data_count = len(coverage_df) - has_data_count

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric("有数据", has_data_count, delta="股票")
        st.metric("缺失数据", missing_data_count, delta="股票")

        coverage_ratio = has_data_count / max(len(coverage_df), 1)
        if coverage_ratio < 0.5:
            st.error("⚠️ 数据覆盖率低于 50%")
            st.info("建议运行数据补充工具")
        elif coverage_ratio < 0.9:
            st.warning("⚠️ 部分股票缺少市场数据")
        else:
            st.success("✅ 数据覆盖率良好")

    with col2:
        # 饼图
        import plotly.graph_objects as go

        fig = go.Figure(data=[go.Pie(
            labels=['有数据', '缺失数据'],
            values=[has_data_count, missing_data_count],
            marker=dict(colors=['#00C851', '#FF3547']),
            hole=0.4
        )])

        fig.update_layout(
            title='数据覆盖率',
            height=300,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # 详细列表
    st.subheader("📋 股票详细列表")

    # 筛选选项
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        filter_option = st.selectbox(
            "筛选",
            ["全部", "有数据", "缺失数据"]
        )

    with col2:
        sort_option = st.selectbox(
            "排序",
            ["交易次数（降序）", "交易次数（升序）", "股票代码"]
        )

    with col3:
        limit = st.number_input("显示数量", min_value=10, max_value=500, value=50, step=10)

    # 应用筛选
    if filter_option == "有数据":
        filtered_df = coverage_df[coverage_df['has_data'] == True]
    elif filter_option == "缺失数据":
        filtered_df = coverage_df[coverage_df['has_data'] == False]
    else:
        filtered_df = coverage_df

    # 应用排序
    if sort_option == "交易次数（降序）":
        filtered_df = filtered_df.sort_values('trade_count', ascending=False)
    elif sort_option == "交易次数（升序）":
        filtered_df = filtered_df.sort_values('trade_count', ascending=True)
    else:
        filtered_df = filtered_df.sort_values('symbol')

    # 限制数量
    filtered_df = filtered_df.head(limit)

    # 显示表格
    if len(filtered_df) > 0:
        # 格式化显示
        display_df = filtered_df.copy()
        display_df['首次交易'] = display_df['first_trade'].dt.strftime('%Y-%m-%d')
        display_df['最后交易'] = display_df['last_trade'].dt.strftime('%Y-%m-%d')
        display_df['状态'] = display_df['has_data'].apply(lambda x: '✓ 有数据' if x else '✗ 缺失')

        # 选择要显示的列
        display_df = display_df[[
            'symbol', 'trade_count', 'data_count', '首次交易', '最后交易', '状态'
        ]]

        display_df.columns = ['股票代码', '交易次数', '市场数据记录', '首次交易', '最后交易', '状态']

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )

        st.caption(f"显示 {len(filtered_df)} / {len(coverage_df)} 个股票")

    else:
        st.info("没有符合条件的数据")

    st.markdown("---")

    # 缺失数据列表
    missing_df = coverage_df[coverage_df['has_data'] == False]

    if len(missing_df) > 0:
        st.subheader(f"❌ 缺失市场数据的股票 ({len(missing_df)})")

        # 按交易次数排序
        missing_df = missing_df.sort_values('trade_count', ascending=False)

        # 显示前20个
        top_missing = missing_df.head(20)

        st.write("**交易次数最多的缺失数据股票（前20）:**")
        for idx, row in top_missing.iterrows():
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                st.write(f"**{row['symbol']}**")
            with col2:
                st.write(f"交易 {row['trade_count']} 次")
            with col3:
                st.write(f"{row['first_trade'].date()} ~ {row['last_trade'].date()}")

        if len(missing_df) > 20:
            st.caption(f"... 还有 {len(missing_df) - 20} 个股票缺少数据")

        st.markdown("---")

        # 补充数据建议
        st.info("💡 **建议操作**: 运行以下命令补充市场数据")

        st.code("""
# 从数据库已有交易中提取股票代码并补充数据
python3 scripts/supplement_data_from_csv.py --from-db --verbose

# 或从CSV文件补充
python3 scripts/supplement_data_from_csv.py original_data/your_trades.csv --verbose

# 补充后重新评分
python3 scripts/score_positions.py --all --force
        """, language='bash')

    else:
        st.success("✅ 所有股票都有市场数据！")

    # 刷新按钮
    st.markdown("---")
    if st.button("🔄 刷新数据", type="primary"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"❌ 加载数据失败: {e}")
    st.info("请确保数据库文件存在且格式正确")

    with st.expander("查看错误详情"):
        import traceback
        st.code(traceback.format_exc())
