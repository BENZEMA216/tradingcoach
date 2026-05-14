"""
导入历史模型

input: SQLAlchemy Base
output: ImportHistory / PositionSnapshot 模型
pos: 数据层 - 跟踪 CSV 增量导入与持仓快照

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Numeric, JSON, Index

from src.models.base import Base


class ImportHistory(Base):
    """CSV 增量导入历史记录"""

    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    file_name = Column(String(255))
    file_hash = Column(String(64))
    file_type = Column(String(20))
    total_rows = Column(Integer)
    new_trades = Column(Integer)
    duplicates_skipped = Column(Integer)
    errors = Column(Integer, default=0)
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    status = Column(String(20))
    error_message = Column(Text)
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_import_history_time", "import_time"),
        Index("idx_import_history_file_hash", "file_hash"),
    )


class PositionSnapshot(Base):
    """券商持仓快照（用于对账）"""

    __tablename__ = "position_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False)
    source = Column(String(50))
    account_id = Column(String(50))
    total_positions = Column(Integer)
    total_market_value = Column(Numeric(20, 2))
    total_unrealized_pnl = Column(Numeric(20, 2))
    positions_json = Column(JSON)
    status = Column(String(20))
    reconciliation_report = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_snapshot_date", "snapshot_date"),
    )
