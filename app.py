#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易复盘报告系统 - Streamlit Web应用
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="交易复盘系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .insight-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    .warning-card {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
    .success-card {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """加载和清洗数据"""
    filepath = 'original_data/历史-保证金综合账户(2663)-20251103-231527.csv'
    df = pd.read_csv(filepath, encoding='utf-8-sig')

    # 只保留已成交的记录
    df_clean = df[df['交易状态'] == '全部成交'].copy()

    # 转换数值字段
    df_clean['成交价格'] = pd.to_numeric(df_clean['成交价格'], errors='coerce')
    df_clean['成交数量'] = pd.to_numeric(df_clean['成交数量'], errors='coerce')
    df_clean['成交金额'] = pd.to_numeric(df_clean['成交金额'], errors='coerce')
    df_clean['合计费用'] = pd.to_numeric(df_clean['合计费用'], errors='coerce')

    # 转换时间字段
    df_clean['成交时间_parsed'] = pd.to_datetime(
        df_clean['成交时间'].str.extract(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})')[0],
        format='%Y/%m/%d %H:%M:%S',
        errors='coerce'
    )
    df_clean['日期'] = df_clean['成交时间_parsed'].dt.date

    return df_clean


@st.cache_data
def identify_paired_trades(df):
    """识别配对交易"""
    paired_trades = []

    for symbol in df['代码'].unique():
        symbol_df = df[df['代码'] == symbol].copy()
        symbol_df = symbol_df.sort_values('成交时间_parsed')

        buy_records = symbol_df[symbol_df['方向'] == '买入']
        sell_records = symbol_df[symbol_df['方向'].isin(['卖出', '卖空'])]

        for _, buy in buy_records.iterrows():
            later_sells = sell_records[sell_records['成交时间_parsed'] > buy['成交时间_parsed']]
            if not later_sells.empty:
                sell = later_sells.iloc[0]

                buy_amount = buy['成交金额'] + buy['合计费用']
                sell_amount = sell['成交金额'] - sell['合计费用']

                pnl = sell_amount - buy_amount
                pnl_pct = (pnl / buy_amount) * 100 if buy_amount > 0 else 0

                # 计算持仓时间
                holding_days = (sell['成交时间_parsed'] - buy['成交时间_parsed']).days

                paired_trades.append({
                    '标的': symbol,
                    '名称': buy['名称'],
                    '买入时间': buy['成交时间_parsed'],
                    '卖出时间': sell['成交时间_parsed'],
                    '买入价': buy['成交价格'],
                    '卖出价': sell['成交价格'],
                    '数量': buy['成交数量'],
                    '买入金额': buy_amount,
                    '卖出金额': sell_amount,
                    '盈亏': pnl,
                    '盈亏率': pnl_pct,
                    '持仓天数': holding_days,
                    '市场': buy['市场']
                })

    if paired_trades:
        return pd.DataFrame(paired_trades)
    return pd.DataFrame()


def dashboard_page(df, paired_df):
    """仪表盘页面"""
    st.markdown('<h1 class="main-header">📊 交易复盘仪表盘</h1>', unsafe_allow_html=True)

    # 关键指标卡片
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="总交易笔数",
            value=f"{len(df):,}",
            delta=None
        )

    with col2:
        if not paired_df.empty:
            total_pnl = paired_df['盈亏'].sum()
            st.metric(
                label="总盈亏",
                value=f"${total_pnl:,.2f}",
                delta=None,
                delta_color="normal" if total_pnl >= 0 else "inverse"
            )
        else:
            st.metric(label="总盈亏", value="N/A")

    with col3:
        if not paired_df.empty:
            win_rate = len(paired_df[paired_df['盈亏'] > 0]) / len(paired_df) * 100
            st.metric(
                label="胜率",
                value=f"{win_rate:.1f}%",
                delta=None
            )
        else:
            st.metric(label="胜率", value="N/A")

    with col4:
        total_fees = df['合计费用'].sum()
        st.metric(
            label="总费用",
            value=f"${total_fees:,.2f}",
            delta=None
        )

    with col5:
        date_range = (df['成交时间_parsed'].max() - df['成交时间_parsed'].min()).days
        avg_trades_per_day = len(df) / date_range if date_range > 0 else 0
        st.metric(
            label="日均交易",
            value=f"{avg_trades_per_day:.1f}",
            delta=None
        )

    st.markdown("---")

    # 盈亏曲线
    if not paired_df.empty:
        st.subheader("📈 盈亏曲线")

        paired_df_sorted = paired_df.sort_values('卖出时间')
        paired_df_sorted['累计盈亏'] = paired_df_sorted['盈亏'].cumsum()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=paired_df_sorted['卖出时间'],
            y=paired_df_sorted['累计盈亏'],
            mode='lines+markers',
            name='累计盈亏',
            line=dict(color='#667eea', width=3),
            fill='tozeroy'
        ))

        fig.update_layout(
            title='累计盈亏曲线',
            xaxis_title='日期',
            yaxis_title='累计盈亏 ($)',
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    # AI洞察卡片
    st.subheader("🤖 AI 洞察")

    col1, col2 = st.columns(2)

    with col1:
        if not paired_df.empty and len(paired_df) > 0:
            win_rate = len(paired_df[paired_df['盈亏'] > 0]) / len(paired_df) * 100
            if win_rate < 30:
                st.markdown(f"""
                <div class="warning-card">
                    <h4>⚠️ 胜率极低警告</h4>
                    <p>当前胜率仅 <strong>{win_rate:.1f}%</strong>，远低于健康水平。建议：</p>
                    <ul>
                        <li>暂停交易，深度复盘</li>
                        <li>重新评估交易策略</li>
                        <li>设置严格的止损纪律</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            elif win_rate < 50:
                st.markdown(f"""
                <div class="insight-card">
                    <h4>💡 胜率需要改进</h4>
                    <p>当前胜率 <strong>{win_rate:.1f}%</strong>，低于50%。需要优化交易策略。</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="success-card">
                    <h4>✅ 胜率表现良好</h4>
                    <p>当前胜率 <strong>{win_rate:.1f}%</strong>，继续保持！</p>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        # 费用分析
        total_fees = df['合计费用'].sum()
        total_amount = df['成交金额'].sum()
        fee_rate = (total_fees / total_amount * 100) if total_amount > 0 else 0

        if fee_rate > 0.5:
            st.markdown(f"""
            <div class="warning-card">
                <h4>⚠️ 费用占比过高</h4>
                <p>费用占交易额的 <strong>{fee_rate:.3f}%</strong></p>
                <p>建议减少交易频率，增加单笔交易规模</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="success-card">
                <h4>✅ 费用控制良好</h4>
                <p>费用占比 <strong>{fee_rate:.3f}%</strong></p>
            </div>
            """, unsafe_allow_html=True)

    # 市场分布
    st.subheader("🌍 市场分布")
    col1, col2 = st.columns(2)

    with col1:
        market_counts = df['市场'].value_counts()
        fig = px.pie(
            values=market_counts.values,
            names=market_counts.index,
            title='交易次数分布',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 按方向统计
        direction_counts = df['方向'].value_counts()
        fig = px.bar(
            x=direction_counts.index,
            y=direction_counts.values,
            title='交易方向分布',
            labels={'x': '方向', 'y': '次数'},
            color=direction_counts.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)


def trades_list_page(df, paired_df):
    """交易列表页面"""
    st.markdown('<h1 class="main-header">📋 交易列表</h1>', unsafe_allow_html=True)

    # 筛选器
    col1, col2, col3 = st.columns(3)

    with col1:
        markets = ['全部'] + list(df['市场'].unique())
        selected_market = st.selectbox('选择市场', markets)

    with col2:
        directions = ['全部'] + list(df['方向'].unique())
        selected_direction = st.selectbox('选择方向', directions)

    with col3:
        symbols = ['全部'] + sorted(df['代码'].unique().tolist())
        selected_symbol = st.selectbox('选择标的', symbols)

    # 应用筛选
    filtered_df = df.copy()
    if selected_market != '全部':
        filtered_df = filtered_df[filtered_df['市场'] == selected_market]
    if selected_direction != '全部':
        filtered_df = filtered_df[filtered_df['方向'] == selected_direction]
    if selected_symbol != '全部':
        filtered_df = filtered_df[filtered_df['代码'] == selected_symbol]

    # 显示统计
    st.info(f"共找到 {len(filtered_df)} 条交易记录")

    # 显示交易表格
    display_df = filtered_df[[
        '成交时间', '方向', '代码', '名称', '成交价格', '成交数量',
        '成交金额', '合计费用', '市场'
    ]].sort_values('成交时间', ascending=False)

    st.dataframe(
        display_df,
        use_container_width=True,
        height=600
    )

    # 下载按钮
    csv = display_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 下载交易列表 CSV",
        data=csv,
        file_name=f"trades_list_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


def periodic_report_page(df, paired_df):
    """周期性报告页面"""
    st.markdown('<h1 class="main-header">📅 周期性报告</h1>', unsafe_allow_html=True)

    # 日期范围选择
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            '开始日期',
            value=df['日期'].min(),
            min_value=df['日期'].min(),
            max_value=df['日期'].max()
        )

    with col2:
        end_date = st.date_input(
            '结束日期',
            value=df['日期'].max(),
            min_value=df['日期'].min(),
            max_value=df['日期'].max()
        )

    # 筛选数据
    mask = (df['日期'] >= start_date) & (df['日期'] <= end_date)
    period_df = df[mask]

    if not paired_df.empty:
        paired_mask = (paired_df['卖出时间'].dt.date >= start_date) & (paired_df['卖出时间'].dt.date <= end_date)
        period_paired_df = paired_df[paired_mask]
    else:
        period_paired_df = pd.DataFrame()

    st.markdown("---")

    # 绩效概览
    st.subheader("📊 绩效概览")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("交易笔数", f"{len(period_df):,}")

    with col2:
        if not period_paired_df.empty:
            st.metric("配对交易", f"{len(period_paired_df):,}")
        else:
            st.metric("配对交易", "0")

    with col3:
        if not period_paired_df.empty:
            win_count = len(period_paired_df[period_paired_df['盈亏'] > 0])
            st.metric("盈利笔数", f"{win_count}")
        else:
            st.metric("盈利笔数", "0")

    with col4:
        if not period_paired_df.empty:
            loss_count = len(period_paired_df[period_paired_df['盈亏'] < 0])
            st.metric("亏损笔数", f"{loss_count}")
        else:
            st.metric("亏损笔数", "0")

    st.markdown("---")

    # 盈亏分析
    if not period_paired_df.empty:
        st.subheader("💰 盈亏分析")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_pnl = period_paired_df['盈亏'].sum()
            st.metric("总盈亏", f"${total_pnl:,.2f}")

        with col2:
            win_rate = len(period_paired_df[period_paired_df['盈亏'] > 0]) / len(period_paired_df) * 100
            st.metric("胜率", f"{win_rate:.1f}%")

        with col3:
            if len(period_paired_df[period_paired_df['盈亏'] > 0]) > 0:
                avg_win = period_paired_df[period_paired_df['盈亏'] > 0]['盈亏'].mean()
                st.metric("平均盈利", f"${avg_win:,.2f}")
            else:
                st.metric("平均盈利", "N/A")

        with col4:
            if len(period_paired_df[period_paired_df['盈亏'] < 0]) > 0:
                avg_loss = period_paired_df[period_paired_df['盈亏'] < 0]['盈亏'].mean()
                st.metric("平均亏损", f"${avg_loss:,.2f}")
            else:
                st.metric("平均亏损", "N/A")

        # 盈亏分布图
        col1, col2 = st.columns(2)

        with col1:
            fig = px.histogram(
                period_paired_df,
                x='盈亏',
                nbins=30,
                title='盈亏分布',
                labels={'盈亏': '盈亏 ($)', 'count': '次数'},
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # 持仓时间分布
            fig = px.histogram(
                period_paired_df,
                x='持仓天数',
                nbins=20,
                title='持仓时间分布',
                labels={'持仓天数': '持仓天数', 'count': '次数'},
                color_discrete_sequence=['#764ba2']
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # 标的分析
    st.subheader("🎯 标的分析")

    symbol_stats = period_df.groupby('代码').agg({
        '成交金额': 'sum',
        '合计费用': 'sum',
        '方向': 'count'
    }).rename(columns={'方向': '交易次数'}).sort_values('交易次数', ascending=False).head(10)

    fig = px.bar(
        symbol_stats.reset_index(),
        x='代码',
        y='交易次数',
        title='交易最频繁的10个标的',
        labels={'代码': '标的代码', '交易次数': '交易次数'},
        color='交易次数',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig, use_container_width=True)

    # 交易时间热力图
    st.subheader("⏰ 交易时间分析")

    period_df_time = period_df[period_df['成交时间_parsed'].notna()].copy()
    period_df_time['星期'] = period_df_time['成交时间_parsed'].dt.dayofweek
    period_df_time['小时'] = period_df_time['成交时间_parsed'].dt.hour

    weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
    weekday_counts = period_df_time['星期'].map(weekday_map).value_counts()

    fig = px.bar(
        x=list(weekday_map.values()),
        y=[weekday_counts.get(day, 0) for day in weekday_map.values()],
        title='星期几交易分布',
        labels={'x': '星期', 'y': '交易次数'},
        color=[weekday_counts.get(day, 0) for day in weekday_map.values()],
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig, use_container_width=True)


def trade_detail_page(df, paired_df):
    """单笔交易详情页面"""
    st.markdown('<h1 class="main-header">🔍 单笔交易详情</h1>', unsafe_allow_html=True)

    if paired_df.empty:
        st.warning("没有配对交易数据")
        return

    # 选择交易
    paired_df_sorted = paired_df.sort_values('卖出时间', ascending=False)
    paired_df_sorted['显示名称'] = (
        paired_df_sorted['名称'] + ' | ' +
        paired_df_sorted['卖出时间'].dt.strftime('%Y-%m-%d') + ' | ' +
        paired_df_sorted['盈亏'].apply(lambda x: f"${x:,.2f}")
    )

    selected_trade = st.selectbox(
        '选择交易',
        options=range(len(paired_df_sorted)),
        format_func=lambda x: paired_df_sorted.iloc[x]['显示名称']
    )

    trade = paired_df_sorted.iloc[selected_trade]

    # 显示交易详情
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 基本信息")
        st.write(f"**标的**: {trade['名称']} ({trade['标的']})")
        st.write(f"**市场**: {trade['市场']}")
        st.write(f"**持仓天数**: {trade['持仓天数']} 天")

    with col2:
        st.markdown("### 买入信息")
        st.write(f"**买入时间**: {trade['买入时间'].strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**买入价格**: ${trade['买入价']:.2f}")
        st.write(f"**买入金额**: ${trade['买入金额']:,.2f}")

    with col3:
        st.markdown("### 卖出信息")
        st.write(f"**卖出时间**: {trade['卖出时间'].strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**卖出价格**: ${trade['卖出价']:.2f}")
        st.write(f"**卖出金额**: ${trade['卖出金额']:,.2f}")

    st.markdown("---")

    # 盈亏分析
    col1, col2, col3 = st.columns(3)

    with col1:
        pnl_color = "green" if trade['盈亏'] >= 0 else "red"
        st.markdown(f"### <span style='color:{pnl_color}'>盈亏: ${trade['盈亏']:,.2f}</span>", unsafe_allow_html=True)

    with col2:
        pnl_pct_color = "green" if trade['盈亏率'] >= 0 else "red"
        st.markdown(f"### <span style='color:{pnl_pct_color}'>盈亏率: {trade['盈亏率']:.2f}%</span>", unsafe_allow_html=True)

    with col3:
        price_change = ((trade['卖出价'] - trade['买入价']) / trade['买入价']) * 100 if trade['买入价'] > 0 else 0
        st.markdown(f"### 价格变化: {price_change:.2f}%")

    # AI 分析
    st.markdown("---")
    st.subheader("🤖 AI 分析")

    if trade['盈亏'] > 0:
        st.markdown(f"""
        <div class="success-card">
            <h4>✅ 盈利交易</h4>
            <p>这是一笔成功的交易，盈利 ${trade['盈亏']:,.2f} ({trade['盈亏率']:.2f}%)</p>
            <p><strong>持仓时间</strong>: {trade['持仓天数']} 天</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="warning-card">
            <h4>⚠️ 亏损交易</h4>
            <p>这笔交易亏损 ${abs(trade['盈亏']):,.2f} ({trade['盈亏率']:.2f}%)</p>
            <p><strong>持仓时间</strong>: {trade['持仓天数']} 天</p>
            <p><strong>建议</strong>: 回顾进场理由，检查是否执行了止损策略</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """主函数"""
    # 加载数据
    with st.spinner('正在加载数据...'):
        df = load_data()
        paired_df = identify_paired_trades(df)

    # 侧边栏导航
    st.sidebar.title("📊 交易复盘系统")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "选择页面",
        ["📊 仪表盘", "📋 交易列表", "📅 周期性报告", "🔍 单笔交易详情"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 数据概览")
    st.sidebar.info(f"""
    **数据期间**
    {df['日期'].min()} 至 {df['日期'].max()}

    **总交易笔数**
    {len(df):,}

    **配对交易**
    {len(paired_df):,}
    """)

    # 根据选择显示不同页面
    if page == "📊 仪表盘":
        dashboard_page(df, paired_df)
    elif page == "📋 交易列表":
        trades_list_page(df, paired_df)
    elif page == "📅 周期性报告":
        periodic_report_page(df, paired_df)
    elif page == "🔍 单笔交易详情":
        trade_detail_page(df, paired_df)


if __name__ == '__main__':
    main()
