"""
FilterContext - 全局筛选状态管理

解决问题: 各页面筛选器独立，切换页面丢失筛选状态
方案: 使用 st.session_state 统一管理筛选状态
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any


class FilterContext:
    """
    全局筛选状态管理器

    使用 st.session_state 存储筛选条件，确保跨页面持久化
    """

    # Session state 键名
    KEYS = {
        'date_start': 'filter_date_start',
        'date_end': 'filter_date_end',
        'symbols': 'filter_symbols',
        'score_min': 'filter_score_min',
        'score_max': 'filter_score_max',
        'pnl_type': 'filter_pnl_type',  # 'all', 'profit', 'loss'
        'strategies': 'filter_strategies',
        'grades': 'filter_grades',
    }

    # 默认值
    DEFAULTS = {
        'date_start': None,  # None 表示不限制
        'date_end': None,
        'symbols': [],  # 空列表表示全部
        'score_min': 0,
        'score_max': 100,
        'pnl_type': 'all',
        'strategies': [],
        'grades': [],
    }

    @classmethod
    def initialize(cls) -> None:
        """初始化筛选状态（如果尚未初始化）"""
        for key, default in cls.DEFAULTS.items():
            session_key = cls.KEYS[key]
            if session_key not in st.session_state:
                st.session_state[session_key] = default

    @classmethod
    def get(cls, key: str) -> Any:
        """获取单个筛选值"""
        cls.initialize()
        session_key = cls.KEYS.get(key)
        if session_key:
            return st.session_state.get(session_key, cls.DEFAULTS.get(key))
        return None

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """设置单个筛选值"""
        cls.initialize()
        session_key = cls.KEYS.get(key)
        if session_key:
            st.session_state[session_key] = value

    @classmethod
    def get_filters(cls) -> Dict[str, Any]:
        """获取所有筛选条件"""
        cls.initialize()
        return {
            'date_range': (
                st.session_state.get(cls.KEYS['date_start']),
                st.session_state.get(cls.KEYS['date_end'])
            ),
            'symbols': st.session_state.get(cls.KEYS['symbols'], []),
            'score_range': (
                st.session_state.get(cls.KEYS['score_min'], 0),
                st.session_state.get(cls.KEYS['score_max'], 100)
            ),
            'pnl_type': st.session_state.get(cls.KEYS['pnl_type'], 'all'),
            'strategies': st.session_state.get(cls.KEYS['strategies'], []),
            'grades': st.session_state.get(cls.KEYS['grades'], []),
        }

    @classmethod
    def clear(cls) -> None:
        """清除所有筛选条件（恢复默认值）"""
        for key, default in cls.DEFAULTS.items():
            session_key = cls.KEYS[key]
            st.session_state[session_key] = default

    @classmethod
    def has_active_filters(cls) -> bool:
        """检查是否有活动的筛选条件"""
        filters = cls.get_filters()

        # 检查日期范围
        if filters['date_range'][0] is not None or filters['date_range'][1] is not None:
            return True

        # 检查股票筛选
        if filters['symbols']:
            return True

        # 检查评分范围
        if filters['score_range'] != (0, 100):
            return True

        # 检查盈亏类型
        if filters['pnl_type'] != 'all':
            return True

        # 检查策略
        if filters['strategies']:
            return True

        # 检查等级
        if filters['grades']:
            return True

        return False

    @classmethod
    def get_active_filter_count(cls) -> int:
        """获取活动筛选条件数量"""
        count = 0
        filters = cls.get_filters()

        if filters['date_range'][0] is not None or filters['date_range'][1] is not None:
            count += 1
        if filters['symbols']:
            count += 1
        if filters['score_range'] != (0, 100):
            count += 1
        if filters['pnl_type'] != 'all':
            count += 1
        if filters['strategies']:
            count += 1
        if filters['grades']:
            count += 1

        return count

    @classmethod
    def apply_to_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        将筛选条件应用到 DataFrame

        Args:
            df: 包含 positions 数据的 DataFrame
                需要的列: close_date/close_time, symbol, overall_score, net_pnl,
                         strategy_type, score_grade

        Returns:
            筛选后的 DataFrame
        """
        if df is None or df.empty:
            return df

        filters = cls.get_filters()
        filtered_df = df.copy()

        # 1. 日期范围筛选
        date_start, date_end = filters['date_range']
        date_col = 'close_date' if 'close_date' in filtered_df.columns else 'close_time'

        if date_col in filtered_df.columns:
            if date_start is not None:
                if isinstance(date_start, date) and not isinstance(date_start, datetime):
                    date_start = datetime.combine(date_start, datetime.min.time())
                filtered_df = filtered_df[filtered_df[date_col] >= date_start]

            if date_end is not None:
                if isinstance(date_end, date) and not isinstance(date_end, datetime):
                    date_end = datetime.combine(date_end, datetime.max.time())
                filtered_df = filtered_df[filtered_df[date_col] <= date_end]

        # 2. 股票筛选
        if filters['symbols'] and 'symbol' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['symbol'].isin(filters['symbols'])]

        # 3. 评分范围筛选
        score_min, score_max = filters['score_range']
        if 'overall_score' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['overall_score'] >= score_min) &
                (filtered_df['overall_score'] <= score_max)
            ]

        # 4. 盈亏类型筛选
        if filters['pnl_type'] != 'all' and 'net_pnl' in filtered_df.columns:
            if filters['pnl_type'] == 'profit':
                filtered_df = filtered_df[filtered_df['net_pnl'] >= 0]
            elif filters['pnl_type'] == 'loss':
                filtered_df = filtered_df[filtered_df['net_pnl'] < 0]

        # 5. 策略筛选
        if filters['strategies'] and 'strategy_type' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['strategy_type'].isin(filters['strategies'])]

        # 6. 等级筛选
        if filters['grades'] and 'score_grade' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['score_grade'].isin(filters['grades'])]

        return filtered_df

    @classmethod
    def get_summary_text(cls) -> str:
        """获取筛选条件摘要文本"""
        if not cls.has_active_filters():
            return "显示全部数据"

        filters = cls.get_filters()
        parts = []

        # 日期
        date_start, date_end = filters['date_range']
        if date_start and date_end:
            parts.append(f"{date_start.strftime('%Y-%m-%d')} ~ {date_end.strftime('%Y-%m-%d')}")
        elif date_start:
            parts.append(f"{date_start.strftime('%Y-%m-%d')} 起")
        elif date_end:
            parts.append(f"至 {date_end.strftime('%Y-%m-%d')}")

        # 股票
        if filters['symbols']:
            if len(filters['symbols']) <= 3:
                parts.append(', '.join(filters['symbols']))
            else:
                parts.append(f"{len(filters['symbols'])} 只股票")

        # 盈亏
        pnl_labels = {'profit': '仅盈利', 'loss': '仅亏损'}
        if filters['pnl_type'] in pnl_labels:
            parts.append(pnl_labels[filters['pnl_type']])

        # 评分
        score_min, score_max = filters['score_range']
        if score_min > 0 or score_max < 100:
            parts.append(f"评分 {score_min}-{score_max}")

        return ' | '.join(parts) if parts else "显示全部数据"
