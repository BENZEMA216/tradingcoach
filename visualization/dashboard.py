#!/usr/bin/env python3
"""
Trading Coach Dashboard
交易教练可视化仪表板

主入口文件。
"""

import streamlit as st
import sys
from pathlib import Path

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 页面配置
st.set_page_config(
    page_title="Trading Coach Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .feature-box {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        border-left: 5px solid #1f77b4;
    }
    .feature-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .feature-desc {
        color: #666;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# 主页面
st.markdown('<div class="main-header">📊 Trading Coach Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">交易质量分析与验证工具</div>', unsafe_allow_html=True)

# 欢迎信息
st.markdown("""
欢迎使用 Trading Coach 可视化分析工具！这是一个专为交易者设计的综合分析平台，
帮助你深入理解交易表现、验证系统逻辑、并持续改进交易质量。
""")

st.markdown("---")

# 功能介绍
st.subheader("🎯 核心功能")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-title">📊 数据概览</div>
        <div class="feature-desc">
            • 查看整体交易统计<br>
            • 检查市场数据覆盖率<br>
            • 识别数据缺失的股票<br>
            • 快速补充市场数据
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-box">
        <div class="feature-title">🔄 FIFO 验证</div>
        <div class="feature-desc">
            • 可视化交易匹配过程<br>
            • 验证先进先出逻辑<br>
            • 对比数据库计算结果<br>
            • 发现潜在的匹配问题
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <div class="feature-title">⭐ 质量评分</div>
        <div class="feature-desc">
            • 四维度评分分析<br>
            • 评分分布与趋势<br>
            • 按股票查看表现<br>
            • 发现最佳/最差交易
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-box">
        <div class="feature-title">📈 技术指标</div>
        <div class="feature-desc">
            • K线图与技术指标<br>
            • 标注交易点位<br>
            • 验证指标正确性<br>
            • 支持多种指标组合
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 快速开始
st.subheader("🚀 快速开始")

st.markdown("""
1. **数据检查**: 点击左侧"📊 数据概览"查看当前数据状态
2. **质量分析**: 前往"⭐ 质量评分"页面查看交易质量分析
3. **验证逻辑**: 使用"🔄 FIFO验证"工具验证匹配算法
4. **技术分析**: 在"📈 技术指标"页面查看价格走势和指标
""")

# 系统状态
st.markdown("---")
st.subheader("📡 系统状态")

try:
    from visualization.utils.data_loader import get_data_loader

    loader = get_data_loader()
    stats = loader.get_overview_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("交易记录", f"{stats['total_trades']:,}")

    with col2:
        st.metric("持仓数量", f"{stats['total_positions']:,}")

    with col3:
        coverage_pct = (stats['symbols_with_data'] / max(stats['total_symbols'], 1)) * 100
        st.metric("数据覆盖率", f"{coverage_pct:.1f}%")

    with col4:
        st.metric("已评分", f"{stats['scored_positions']:,}")

    # 状态指示器
    if coverage_pct < 50:
        st.warning("⚠️ 市场数据覆盖率较低，建议补充数据以获得更准确的质量评分")
        st.info("💡 提示: 使用命令 `python3 scripts/supplement_data_from_csv.py --from-db` 补充数据")
    elif stats['scored_positions'] == 0:
        st.warning("⚠️ 尚未进行质量评分")
        st.info("💡 提示: 使用命令 `python3 scripts/score_positions.py --all` 进行评分")
    else:
        st.success("✅ 系统运行正常，所有功能可用")

except Exception as e:
    st.error(f"❌ 无法连接数据库: {e}")
    st.info("请确保数据库文件存在于 `data/tradingcoach.db`")

# 帮助信息
st.markdown("---")

with st.expander("❓ 需要帮助？"):
    st.markdown("""
    **文档**:
    - [可视化工具文档](../visualization/README.md)
    - [数据补充指南](../project_docs/data_supplementation_guide.md)
    - [FIFO验证工具](../verification/README.md)

    **常见问题**:
    - Q: 如何补充市场数据？
      A: 运行 `python3 scripts/supplement_data_from_csv.py --from-db`

    - Q: 如何重新评分？
      A: 运行 `python3 scripts/score_positions.py --all --force`

    - Q: 仪表板运行缓慢？
      A: 尝试刷新页面或减少显示的数据量

    **技术支持**:
    - 查看项目 README.md
    - 检查日志文件
    """)

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; padding: 2rem 0;">
    Trading Coach Dashboard v1.0.0 |
    基于 Streamlit + Plotly |
    <a href="https://github.com/yourusername/tradingcoach" style="color: #1f77b4;">GitHub</a>
</div>
""", unsafe_allow_html=True)
