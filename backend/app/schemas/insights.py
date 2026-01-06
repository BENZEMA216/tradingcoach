"""
Trading Insights API schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum


class InsightType(str, Enum):
    """Insight type - indicates severity/nature"""
    PROBLEM = "problem"      # 🔴 问题 - Issues that need attention
    STRENGTH = "strength"    # 🟢 优势 - Positive patterns to maintain
    REMINDER = "reminder"    # 🟡 提醒 - Observations and suggestions


class InsightCategory(str, Enum):
    """Insight category - the dimension being analyzed"""
    TIME = "time"            # 时间维度 - Weekday effect, month patterns
    HOLDING = "holding"      # 持仓时间 - Holding period analysis
    SYMBOL = "symbol"        # 标的分析 - Symbol performance
    DIRECTION = "direction"  # 方向策略 - Long/short, strategy effectiveness
    RISK = "risk"            # 风险管理 - Risk management issues
    BEHAVIOR = "behavior"    # 行为模式 - Trading behavior patterns
    FEES = "fees"            # 费用效率 - Fee impact analysis
    OPTIONS = "options"      # 期权特定 - Options-specific insights
    BENCHMARK = "benchmark"  # 基准对比 - Benchmark comparison
    TREND = "trend"          # 趋势变化 - Performance trends


class TradingInsight(BaseModel):
    """Single trading insight/observation"""
    id: str                          # Rule ID, e.g. "T01", "H04"
    type: InsightType                # problem/strength/reminder
    category: InsightCategory        # Analysis dimension
    priority: int                    # 0-100, higher = more important
    title: str                       # Short title
    description: str                 # Detailed description
    suggestion: str                  # Actionable suggestion
    data_points: Dict[str, Any]      # Supporting data


class InsightsResponse(BaseModel):
    """Response containing multiple insights"""
    insights: List[TradingInsight]
    total_positions: int
    date_range: Optional[Dict[str, str]] = None
