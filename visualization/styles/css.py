"""
全局 CSS 样式
注入 Streamlit 应用的自定义样式
"""

import streamlit as st
from .theme import COLORS, FONTS, SPACING, SHADOWS, RADIUS


def get_global_css() -> str:
    """生成全局 CSS 字符串"""
    return f"""
    <style>
    /* ============================================================
       字体导入
       ============================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ============================================================
       全局样式重置
       ============================================================ */
    .stApp {{
        background: linear-gradient(180deg, {COLORS['bg_primary']} 0%, {COLORS['bg_secondary']} 100%);
        color: {COLORS['text_primary']};
        font-family: {FONTS['body']};
    }}

    /* 隐藏默认 Streamlit 元素 */
    .stDeployButton, footer, #MainMenu {{
        display: none !important;
    }}

    /* 自定义滚动条 */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {COLORS['bg_secondary']};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {COLORS['border']};
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['bg_hover']};
    }}

    /* ============================================================
       侧边栏样式
       ============================================================ */
    [data-testid="stSidebar"] {{
        background: {COLORS['bg_secondary']} !important;
        border-right: 1px solid {COLORS['border']} !important;
    }}

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label {{
        color: {COLORS['text_secondary']} !important;
        font-size: 0.875rem !important;
    }}

    /* ============================================================
       标题样式
       ============================================================ */
    h1, h2, h3, h4, h5, h6 {{
        font-family: {FONTS['heading']} !important;
        color: {COLORS['text_primary']} !important;
        font-weight: 600 !important;
    }}

    h1 {{
        font-size: 2rem !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 1.5rem !important;
    }}

    h2 {{
        font-size: 1.5rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }}

    h3 {{
        font-size: 1.25rem !important;
        color: {COLORS['text_secondary']} !important;
    }}

    /* ============================================================
       卡片和容器
       ============================================================ */
    .stTabs [data-baseweb="tab-list"] {{
        background: {COLORS['bg_secondary']} !important;
        border-radius: {RADIUS['lg']} !important;
        padding: 4px !important;
        gap: 4px !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: {COLORS['text_secondary']} !important;
        border-radius: {RADIUS['md']} !important;
        padding: 0.75rem 1.25rem !important;
        font-weight: 500 !important;
    }}

    .stTabs [aria-selected="true"] {{
        background: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
    }}

    /* ============================================================
       Metric 组件
       ============================================================ */
    [data-testid="stMetric"] {{
        background: {COLORS['bg_secondary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: {RADIUS['lg']} !important;
        padding: 1rem 1.25rem !important;
    }}

    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']} !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }}

    [data-testid="stMetricValue"] {{
        font-family: {FONTS['mono']} !important;
        color: {COLORS['text_primary']} !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }}

    [data-testid="stMetricDelta"] {{
        font-family: {FONTS['mono']} !important;
        font-size: 0.875rem !important;
    }}

    /* ============================================================
       按钮样式
       ============================================================ */
    .stButton > button {{
        background: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: {RADIUS['md']} !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }}

    .stButton > button:hover {{
        background: {COLORS['bg_hover']} !important;
        border-color: {COLORS['accent_cyan']} !important;
        box-shadow: {SHADOWS['glow_cyan']} !important;
    }}

    /* Primary 按钮 */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS['accent_cyan']} 0%, {COLORS['accent_blue']} 100%) !important;
        border: none !important;
        color: {COLORS['bg_primary']} !important;
    }}

    /* ============================================================
       输入框样式
       ============================================================ */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {{
        background: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: {RADIUS['md']} !important;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: {COLORS['accent_cyan']} !important;
        box-shadow: 0 0 0 1px {COLORS['accent_cyan']} !important;
    }}

    /* ============================================================
       进度条样式
       ============================================================ */
    .stProgress > div > div > div {{
        background: {COLORS['bg_tertiary']} !important;
        border-radius: {RADIUS['full']} !important;
    }}

    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {COLORS['accent_cyan']} 0%, {COLORS['accent_purple']} 100%) !important;
        border-radius: {RADIUS['full']} !important;
    }}

    /* ============================================================
       表格样式
       ============================================================ */
    .stDataFrame {{
        border: 1px solid {COLORS['border']} !important;
        border-radius: {RADIUS['lg']} !important;
        overflow: hidden !important;
    }}

    .stDataFrame [data-testid="stDataFrameResizable"] {{
        background: {COLORS['bg_secondary']} !important;
    }}

    /* ============================================================
       告警框样式
       ============================================================ */
    .stAlert {{
        border-radius: {RADIUS['lg']} !important;
        border: none !important;
    }}

    [data-testid="stAlert"][data-baseweb="notification"] {{
        background: {COLORS['bg_secondary']} !important;
    }}

    /* ============================================================
       Expander 样式
       ============================================================ */
    .streamlit-expanderHeader {{
        background: {COLORS['bg_secondary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: {RADIUS['lg']} !important;
        color: {COLORS['text_primary']} !important;
    }}

    .streamlit-expanderContent {{
        background: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-top: none !important;
        border-radius: 0 0 {RADIUS['lg']} {RADIUS['lg']} !important;
    }}

    /* ============================================================
       自定义组件类
       ============================================================ */

    /* 发光卡片 */
    .glow-card {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['lg']};
        padding: 1.5rem;
        transition: all 0.3s ease;
    }}

    .glow-card:hover {{
        border-color: {COLORS['accent_cyan']};
        box-shadow: {SHADOWS['glow_cyan']};
    }}

    .glow-card.profit {{
        border-color: {COLORS['profit']};
    }}

    .glow-card.profit:hover {{
        box-shadow: {SHADOWS['glow_green']};
    }}

    .glow-card.loss {{
        border-color: {COLORS['loss']};
    }}

    .glow-card.loss:hover {{
        box-shadow: {SHADOWS['glow_red']};
    }}

    /* 大数字显示 */
    .metric-value {{
        font-family: {FONTS['mono']};
        font-size: 2.5rem;
        font-weight: 600;
        line-height: 1.2;
    }}

    .metric-value.profit {{
        color: {COLORS['profit']};
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }}

    .metric-value.loss {{
        color: {COLORS['loss']};
        text-shadow: 0 0 20px rgba(255, 59, 92, 0.5);
    }}

    .metric-label {{
        color: {COLORS['text_secondary']};
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }}

    /* 等级徽章 */
    .grade-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: {FONTS['mono']};
        font-weight: 700;
        font-size: 1.5rem;
        width: 3rem;
        height: 3rem;
        border-radius: {RADIUS['lg']};
        text-shadow: 0 0 10px currentColor;
    }}

    .grade-badge.grade-a {{
        color: {COLORS['grade_a']};
        background: rgba(0, 255, 136, 0.1);
        border: 2px solid {COLORS['grade_a']};
    }}
    .grade-badge.grade-b {{
        color: {COLORS['grade_b']};
        background: rgba(0, 217, 255, 0.1);
        border: 2px solid {COLORS['grade_b']};
    }}
    .grade-badge.grade-c {{
        color: {COLORS['grade_c']};
        background: rgba(255, 184, 0, 0.1);
        border: 2px solid {COLORS['grade_c']};
    }}
    .grade-badge.grade-d {{
        color: {COLORS['grade_d']};
        background: rgba(255, 140, 0, 0.1);
        border: 2px solid {COLORS['grade_d']};
    }}
    .grade-badge.grade-f {{
        color: {COLORS['grade_f']};
        background: rgba(255, 59, 92, 0.1);
        border: 2px solid {COLORS['grade_f']};
    }}

    /* 盈亏徽章 */
    .pnl-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        border-radius: {RADIUS['full']};
        font-family: {FONTS['mono']};
        font-weight: 600;
        font-size: 0.875rem;
    }}

    .pnl-badge.profit {{
        color: {COLORS['profit']};
        background: rgba(0, 255, 136, 0.15);
    }}

    .pnl-badge.loss {{
        color: {COLORS['loss']};
        background: rgba(255, 59, 92, 0.15);
    }}

    /* 指标卡片 */
    .indicator-card {{
        background: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['lg']};
        padding: 1rem;
        text-align: center;
    }}

    .indicator-card .indicator-name {{
        color: {COLORS['text_secondary']};
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }}

    .indicator-card .indicator-value {{
        font-family: {FONTS['mono']};
        font-size: 1.5rem;
        font-weight: 600;
        color: {COLORS['text_primary']};
    }}

    .indicator-card .indicator-status {{
        font-size: 0.75rem;
        margin-top: 0.25rem;
        padding: 0.125rem 0.5rem;
        border-radius: {RADIUS['full']};
        display: inline-block;
    }}

    .indicator-card .indicator-status.bullish {{
        color: {COLORS['profit']};
        background: rgba(0, 255, 136, 0.15);
    }}

    .indicator-card .indicator-status.bearish {{
        color: {COLORS['loss']};
        background: rgba(255, 59, 92, 0.15);
    }}

    .indicator-card .indicator-status.neutral {{
        color: {COLORS['text_secondary']};
        background: {COLORS['bg_tertiary']};
    }}

    /* 环形进度条 */
    .progress-ring {{
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }}

    .progress-ring .ring-value {{
        position: absolute;
        font-family: {FONTS['mono']};
        font-weight: 600;
        color: {COLORS['text_primary']};
    }}

    /* 分隔线 */
    .section-divider {{
        height: 1px;
        background: linear-gradient(90deg,
            transparent 0%,
            {COLORS['border']} 20%,
            {COLORS['border']} 80%,
            transparent 100%
        );
        margin: 2rem 0;
    }}

    /* Hero Section */
    .hero-section {{
        background: linear-gradient(135deg,
            {COLORS['bg_secondary']} 0%,
            {COLORS['bg_tertiary']} 100%
        );
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['xl']};
        padding: 2rem;
        margin-bottom: 2rem;
    }}

    /* 股票代码显示 */
    .symbol-display {{
        font-family: {FONTS['mono']};
        font-size: 2rem;
        font-weight: 700;
        color: {COLORS['text_primary']};
        letter-spacing: -0.02em;
    }}

    .symbol-name {{
        color: {COLORS['text_secondary']};
        font-size: 1rem;
        margin-top: 0.25rem;
    }}

    /* 动画 */
    @keyframes glow-pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.7; }}
    }}

    .glow-pulse {{
        animation: glow-pulse 2s ease-in-out infinite;
    }}

    @keyframes fade-in {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .fade-in {{
        animation: fade-in 0.3s ease-out;
    }}

    </style>
    """


def inject_global_css():
    """注入全局 CSS 到 Streamlit 应用"""
    st.markdown(get_global_css(), unsafe_allow_html=True)
