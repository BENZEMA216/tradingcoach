"""
Position model - 持仓记录表
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date,
    ForeignKey, Index, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class PositionStatus(enum.Enum):
    """持仓状态枚举"""
    OPEN = "open"  # 持仓中
    CLOSED = "closed"  # 已平仓
    PARTIALLY_CLOSED = "partially_closed"  # 部分平仓


class Position(Base):
    """
    持仓记录表

    通过FIFO算法配对的一组买卖交易，代表一个完整的持仓周期
    """
    __tablename__ = 'positions'

    # ==================== 主键 ====================
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ==================== 基本信息 ====================
    symbol = Column(String(50), nullable=False, index=True, comment="股票代码")
    symbol_name = Column(String(200), comment="股票名称")

    # 持仓状态
    status = Column(
        SQLEnum(PositionStatus),
        nullable=False,
        default=PositionStatus.OPEN,
        comment="持仓状态"
    )

    # 持仓方向（long/short）
    direction = Column(String(10), nullable=False, comment="持仓方向（long/short）")

    # ==================== 时间信息 ====================
    open_time = Column(DateTime, nullable=False, index=True, comment="开仓时间（UTC）")
    close_time = Column(DateTime, index=True, comment="平仓时间（UTC）")

    open_date = Column(Date, nullable=False, index=True, comment="开仓日期")
    close_date = Column(Date, index=True, comment="平仓日期")

    holding_period_days = Column(Integer, comment="持仓天数")
    holding_period_hours = Column(Numeric(10, 2), comment="持仓小时数")

    # ==================== 价格和数量 ====================
    open_price = Column(Numeric(15, 4), nullable=False, comment="开仓价格")
    close_price = Column(Numeric(15, 4), comment="平仓价格")
    quantity = Column(Integer, nullable=False, comment="持仓数量")

    # ==================== 盈亏指标 ====================
    # 实现盈亏
    realized_pnl = Column(Numeric(20, 2), comment="实现盈亏（未扣除费用）")
    realized_pnl_pct = Column(Numeric(10, 4), comment="实现盈亏百分比")

    # 费用
    total_fees = Column(Numeric(15, 2), comment="总费用（开仓+平仓）")
    open_fee = Column(Numeric(15, 2), comment="开仓费用")
    close_fee = Column(Numeric(15, 2), comment="平仓费用")

    # 净盈亏（扣除费用后）
    net_pnl = Column(Numeric(20, 2), comment="净盈亏")
    net_pnl_pct = Column(Numeric(10, 4), comment="净盈亏百分比")

    # ==================== 风险指标 ====================
    # MAE: Maximum Adverse Excursion（最大不利偏移）
    mae = Column(Numeric(20, 2), comment="最大不利偏移（亏损最大时）")
    mae_pct = Column(Numeric(10, 4), comment="MAE百分比")
    mae_time = Column(DateTime, comment="MAE发生时间")

    # MFE: Maximum Favorable Excursion（最大有利偏移）
    mfe = Column(Numeric(20, 2), comment="最大有利偏移（盈利最大时）")
    mfe_pct = Column(Numeric(10, 4), comment="MFE百分比")
    mfe_time = Column(DateTime, comment="MFE发生时间")

    # 风险回报比
    risk_reward_ratio = Column(Numeric(10, 2), comment="风险回报比（R:R）")

    # ==================== 市场信息 ====================
    market = Column(String(20), comment="市场类型（美股/港股/沪深）")
    currency = Column(String(10), comment="币种")

    # ==================== 期权信息 ====================
    underlying_symbol = Column(String(50), index=True, comment="标的股票代码")
    is_option = Column(Integer, default=0, comment="是否为期权（0/1）")

    # ==================== 质量评分 ====================
    # 四维度评分
    entry_quality_score = Column(
        Numeric(5, 2),
        comment="入场质量评分（0-100）"
    )
    exit_quality_score = Column(
        Numeric(5, 2),
        comment="出场质量评分（0-100）"
    )
    trend_quality_score = Column(
        Numeric(5, 2),
        comment="趋势质量评分（0-100）"
    )
    risk_mgmt_score = Column(
        Numeric(5, 2),
        comment="风险管理评分（0-100）"
    )

    # 综合评分
    overall_score = Column(
        Numeric(5, 2),
        index=True,
        comment="综合质量评分（0-100）"
    )

    # 评分等级（A/B/C/D/F）
    score_grade = Column(String(2), comment="评分等级")

    # ==================== 市场环境关联 ====================
    entry_market_env_id = Column(
        Integer,
        ForeignKey('market_environment.id'),
        comment="入场时市场环境ID"
    )
    exit_market_env_id = Column(
        Integer,
        ForeignKey('market_environment.id'),
        comment="出场时市场环境ID"
    )

    # ==================== 分析结果 ====================
    analysis_notes = Column(JSON, comment="分析备注（JSON格式）")

    # 技术指标快照（开仓时）
    entry_indicators = Column(JSON, comment="开仓时技术指标")

    # 技术指标快照（平仓时）
    exit_indicators = Column(JSON, comment="平仓时技术指标")

    # ==================== 策略分类 ====================
    strategy_type = Column(
        String(50),
        comment="策略类型(trend/mean_reversion/breakout/range/momentum)"
    )
    strategy_confidence = Column(
        Numeric(5, 2),
        comment="策略置信度(0-100)"
    )

    # ==================== 复盘字段 ====================
    review_notes = Column(JSON, comment="用户复盘备注")
    emotion_tag = Column(
        String(20),
        comment="情绪标签(greedy/fearful/calm/impulsive)"
    )
    discipline_score = Column(
        Integer,
        comment="纪律执行评分(1-5)"
    )
    reviewed_at = Column(DateTime, comment="复盘时间")

    # ==================== 离场后走势 ====================
    post_exit_5d_pct = Column(
        Numeric(10, 4),
        comment="离场后5日涨跌幅"
    )
    post_exit_10d_pct = Column(
        Numeric(10, 4),
        comment="离场后10日涨跌幅"
    )
    post_exit_20d_pct = Column(
        Numeric(10, 4),
        comment="离场后20日涨跌幅"
    )

    # ==================== 时间戳 ====================
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        comment="记录创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="记录更新时间"
    )

    # ==================== 关系定义 ====================
    # 关联的交易记录（一对多）
    trades = relationship(
        "Trade",
        foreign_keys="Trade.position_id",
        back_populates="position",
        order_by="Trade.filled_time"
    )

    # 入场时市场环境
    entry_market_environment = relationship(
        "MarketEnvironment",
        foreign_keys=[entry_market_env_id],
        backref="entry_positions"
    )

    # 出场时市场环境
    exit_market_environment = relationship(
        "MarketEnvironment",
        foreign_keys=[exit_market_env_id],
        backref="exit_positions"
    )

    # ==================== 索引 ====================
    __table_args__ = (
        # 按symbol和时间查询
        Index('idx_pos_symbol_open_time', 'symbol', 'open_time'),
        Index('idx_pos_symbol_close_time', 'symbol', 'close_time'),

        # 按状态查询
        Index('idx_pos_status', 'status'),

        # 按评分查询
        Index('idx_pos_overall_score', 'overall_score'),
        Index('idx_pos_score_grade', 'score_grade'),

        # 按盈亏查询
        Index('idx_pos_net_pnl', 'net_pnl'),

        # 期权查询
        Index('idx_pos_underlying', 'underlying_symbol'),
    )

    def __repr__(self):
        return (
            f"<Position(id={self.id}, symbol={self.symbol}, "
            f"direction={self.direction}, "
            f"quantity={self.quantity}, "
            f"pnl={self.net_pnl}, "
            f"score={self.overall_score})>"
        )

    @property
    def is_winner(self):
        """是否盈利"""
        return self.net_pnl is not None and self.net_pnl > 0

    @property
    def is_loser(self):
        """是否亏损"""
        return self.net_pnl is not None and self.net_pnl < 0

    @property
    def is_closed(self):
        """是否已平仓"""
        return self.status == PositionStatus.CLOSED

    def calculate_holding_period(self):
        """计算持仓时长"""
        if self.close_time and self.open_time:
            delta = self.close_time - self.open_time
            self.holding_period_days = delta.days
            self.holding_period_hours = delta.total_seconds() / 3600
            return self.holding_period_days

    def calculate_pnl(self):
        """计算盈亏"""
        if self.close_price is None or self.open_price is None:
            return

        if self.direction == 'long':
            # 做多: (卖出价 - 买入价) * 数量
            self.realized_pnl = (self.close_price - self.open_price) * self.quantity
        elif self.direction == 'short':
            # 做空: (卖空价 - 买入回补价) * 数量
            self.realized_pnl = (self.open_price - self.close_price) * self.quantity

        # 计算盈亏百分比
        if self.open_price > 0:
            self.realized_pnl_pct = (self.realized_pnl / (self.open_price * self.quantity)) * 100

        # 计算净盈亏
        if self.total_fees:
            self.net_pnl = self.realized_pnl - self.total_fees
            self.net_pnl_pct = (self.net_pnl / (self.open_price * self.quantity)) * 100

    def assign_score_grade(self):
        """分配评分等级"""
        if self.overall_score is None:
            return

        score = float(self.overall_score)
        if score >= 90:
            self.score_grade = 'A'
        elif score >= 80:
            self.score_grade = 'B'
        elif score >= 70:
            self.score_grade = 'C'
        elif score >= 60:
            self.score_grade = 'D'
        else:
            self.score_grade = 'F'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'symbol_name': self.symbol_name,
            'status': self.status.value if self.status else None,
            'direction': self.direction,
            'open_time': self.open_time.isoformat() if self.open_time else None,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'open_price': float(self.open_price) if self.open_price else None,
            'close_price': float(self.close_price) if self.close_price else None,
            'quantity': self.quantity,
            'net_pnl': float(self.net_pnl) if self.net_pnl else None,
            'net_pnl_pct': float(self.net_pnl_pct) if self.net_pnl_pct else None,
            'overall_score': float(self.overall_score) if self.overall_score else None,
            'score_grade': self.score_grade,
            'holding_period_days': self.holding_period_days,
            # 策略分类
            'strategy_type': self.strategy_type,
            'strategy_confidence': float(self.strategy_confidence) if self.strategy_confidence else None,
            # 复盘字段
            'review_notes': self.review_notes,
            'emotion_tag': self.emotion_tag,
            'discipline_score': self.discipline_score,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            # 离场后走势
            'post_exit_5d_pct': float(self.post_exit_5d_pct) if self.post_exit_5d_pct else None,
            'post_exit_10d_pct': float(self.post_exit_10d_pct) if self.post_exit_10d_pct else None,
            'post_exit_20d_pct': float(self.post_exit_20d_pct) if self.post_exit_20d_pct else None,
        }
