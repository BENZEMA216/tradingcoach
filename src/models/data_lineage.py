"""
数据血缘模型

input: SQLAlchemy Base
output: DataLineageEvent / DataLineageRecord 模型
pos: 数据层 - 追踪每条 trade/position 的来源（哪个文件、哪一行、哪个 import batch）。
     原本 src/validators/data_lineage.py 用 raw DDL 临时建，没纳入 ORM 导致
     create_all 不会创建。
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Index, UniqueConstraint,
)

from src.models.base import Base


class DataLineageEvent(Base):
    """数据血缘事件（一次 import / mutation 整体）"""

    __tablename__ = "data_lineage_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False, unique=True)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    affected_table = Column(String(50), nullable=False)
    affected_ids = Column(Text)  # JSON array
    source_info = Column(Text)   # JSON object
    user = Column(String(50), default="system")
    description = Column(Text)
    rollback_sql = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_lineage_events_table", "affected_table"),
    )


class DataLineageRecord(Base):
    """单条记录的血缘（指向哪些 events）"""

    __tablename__ = "data_lineage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_table = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    source_file = Column(String(255))
    source_row = Column(Integer)
    import_batch_id = Column(String(64))
    transformation_chain = Column(Text)  # JSON array of event_ids
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "record_table", "record_id", name="uq_lineage_record"
        ),
        Index("idx_lineage_records_table", "record_table", "record_id"),
    )
