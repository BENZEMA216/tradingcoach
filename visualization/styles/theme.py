"""
Terminal Finance Theme - 色彩、字体、间距定义
深蓝黑主题，霓虹色点缀
"""

# ============================================================
# 色彩系统
# ============================================================

COLORS = {
    # 主色调 - 深蓝黑背景 (GitHub Dark 风格)
    'bg_primary': '#0D1117',      # 主背景
    'bg_secondary': '#161B22',    # 卡片背景
    'bg_tertiary': '#21262D',     # 悬浮/高亮背景
    'bg_hover': '#30363D',        # 悬浮状态

    # 边框
    'border': '#30363D',          # 默认边框
    'border_light': '#21262D',    # 淡边框
    'border_focus': '#58A6FF',    # 聚焦边框

    # 文字
    'text_primary': '#E6EDF3',    # 主文字
    'text_secondary': '#8B949E',  # 次要文字
    'text_muted': '#484F58',      # 弱化文字
    'text_link': '#58A6FF',       # 链接

    # 强调色
    'accent_cyan': '#00D9FF',     # 主强调色 - 霓虹青
    'accent_purple': '#A855F7',   # 次强调色 - 霓虹紫
    'accent_blue': '#58A6FF',     # 蓝色强调

    # 语义色 - 霓虹风格
    'profit': '#00FF88',          # 盈利 - 霓虹绿
    'profit_dim': '#00CC6A',      # 盈利 - 暗绿
    'loss': '#FF3B5C',            # 亏损 - 霓虹红
    'loss_dim': '#CC2E4A',        # 亏损 - 暗红
    'warning': '#FFB800',         # 警告 - 金色
    'warning_dim': '#CC9300',     # 警告 - 暗金
    'info': '#3B82F6',            # 信息 - 蓝色
    'neutral': '#8B949E',         # 中性

    # 评分等级色
    'grade_a': '#00FF88',         # A级 - 霓虹绿
    'grade_b': '#00D9FF',         # B级 - 霓虹青
    'grade_c': '#FFB800',         # C级 - 金色
    'grade_d': '#FF8C00',         # D级 - 橙色
    'grade_f': '#FF3B5C',         # F级 - 霓虹红

    # 策略类型色
    'strategy_trend': '#3B82F6',       # 趋势跟踪 - 蓝色
    'strategy_reversion': '#00FF88',   # 均值回归 - 绿色
    'strategy_breakout': '#FF3B5C',    # 突破交易 - 红色
    'strategy_range': '#FFB800',       # 震荡交易 - 金色
    'strategy_momentum': '#A855F7',    # 动量交易 - 紫色

    # 图表专用
    'chart_up': '#00FF88',        # K线涨
    'chart_down': '#FF3B5C',      # K线跌
    'chart_grid': '#21262D',      # 网格线
    'chart_text': '#8B949E',      # 图表文字
}

# ============================================================
# 字体系统
# ============================================================

FONTS = {
    # 数字显示 - 等宽字体 (使用单引号避免HTML属性冲突)
    'mono': "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
    # 标题
    'heading': "'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
    # 正文
    'body': "'Inter', 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif",
}

# 字体大小
FONT_SIZES = {
    'xs': '0.75rem',      # 12px
    'sm': '0.875rem',     # 14px
    'base': '1rem',       # 16px
    'lg': '1.125rem',     # 18px
    'xl': '1.25rem',      # 20px
    '2xl': '1.5rem',      # 24px
    '3xl': '1.875rem',    # 30px
    '4xl': '2.25rem',     # 36px
    '5xl': '3rem',        # 48px
}

# ============================================================
# 间距系统
# ============================================================

SPACING = {
    'xs': '0.25rem',      # 4px
    'sm': '0.5rem',       # 8px
    'md': '1rem',         # 16px
    'lg': '1.5rem',       # 24px
    'xl': '2rem',         # 32px
    '2xl': '3rem',        # 48px
    '3xl': '4rem',        # 64px
}

# ============================================================
# 阴影系统
# ============================================================

SHADOWS = {
    'sm': '0 1px 2px rgba(0, 0, 0, 0.3)',
    'md': '0 4px 6px rgba(0, 0, 0, 0.4)',
    'lg': '0 10px 15px rgba(0, 0, 0, 0.5)',
    'xl': '0 20px 25px rgba(0, 0, 0, 0.6)',
    # 霓虹发光
    'glow_green': '0 0 20px rgba(0, 255, 136, 0.3)',
    'glow_red': '0 0 20px rgba(255, 59, 92, 0.3)',
    'glow_cyan': '0 0 20px rgba(0, 217, 255, 0.3)',
    'glow_purple': '0 0 20px rgba(168, 85, 247, 0.3)',
}

# ============================================================
# 圆角系统
# ============================================================

RADIUS = {
    'sm': '4px',
    'md': '8px',
    'lg': '12px',
    'xl': '16px',
    'full': '9999px',
}

# ============================================================
# 辅助函数
# ============================================================

def get_pnl_color(value: float, dim: bool = False) -> str:
    """根据盈亏值返回颜色"""
    if value >= 0:
        return COLORS['profit_dim'] if dim else COLORS['profit']
    return COLORS['loss_dim'] if dim else COLORS['loss']


def get_grade_color(grade: str) -> str:
    """根据评分等级返回颜色"""
    grade_map = {
        'A+': COLORS['grade_a'],
        'A': COLORS['grade_a'],
        'A-': COLORS['grade_a'],
        'B+': COLORS['grade_b'],
        'B': COLORS['grade_b'],
        'B-': COLORS['grade_b'],
        'C+': COLORS['grade_c'],
        'C': COLORS['grade_c'],
        'C-': COLORS['grade_c'],
        'D+': COLORS['grade_d'],
        'D': COLORS['grade_d'],
        'D-': COLORS['grade_d'],
        'F': COLORS['grade_f'],
    }
    return grade_map.get(grade, COLORS['neutral'])


def get_strategy_color(strategy_type: str) -> str:
    """根据策略类型返回颜色"""
    strategy_map = {
        'trend': COLORS['strategy_trend'],
        'mean_reversion': COLORS['strategy_reversion'],
        'breakout': COLORS['strategy_breakout'],
        'range': COLORS['strategy_range'],
        'momentum': COLORS['strategy_momentum'],
    }
    return strategy_map.get(strategy_type, COLORS['neutral'])
