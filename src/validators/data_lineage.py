"""
Data Lineage Tracker - 数据血缘追踪

input: SQLite database, import history
output: Data lineage graph, traceability reports
pos: 数据质量保障 - 追踪数据来源和转换历史

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import sqlite3
import hashlib
import json


class TransformationType(Enum):
    """数据转换类型"""
    IMPORT = "import"              # 原始导入
    CLEAN = "clean"                # 数据清洗
    MATCH = "match"                # 持仓配对
    SCORE = "score"                # 评分计算
    INDICATOR = "indicator"        # 指标计算
    MERGE = "merge"                # 数据合并
    FIX = "fix"                    # 数据修复
    DELETE = "delete"              # 数据删除


@dataclass
class LineageNode:
    """血缘节点"""
    node_id: str
    table: str
    record_id: int
    created_at: datetime
    source_file: Optional[str] = None
    source_row: Optional[int] = None
    transformation: TransformationType = TransformationType.IMPORT
    parent_nodes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LineageEvent:
    """血缘事件"""
    event_id: str
    event_type: TransformationType
    timestamp: datetime
    affected_table: str
    affected_ids: List[int]
    source_info: Dict[str, Any]
    user: str = "system"
    description: str = ""
    rollback_sql: Optional[str] = None


class DataLineageTracker:
    """数据血缘追踪器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_lineage_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_lineage_tables(self):
        """确保血缘追踪表存在"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建血缘事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_lineage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                affected_table TEXT NOT NULL,
                affected_ids TEXT,  -- JSON array
                source_info TEXT,   -- JSON object
                user TEXT DEFAULT 'system',
                description TEXT,
                rollback_sql TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建记录级血缘表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_lineage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_table TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                source_file TEXT,
                source_row INTEGER,
                import_batch_id TEXT,
                transformation_chain TEXT,  -- JSON array of event_ids
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(record_table, record_id)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lineage_events_table
            ON data_lineage_events(affected_table)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lineage_records_table
            ON data_lineage_records(record_table, record_id)
        """)

        conn.commit()
        conn.close()

    # =========================================================================
    # 事件记录
    # =========================================================================

    def record_import_event(
        self,
        file_path: str,
        file_hash: str,
        trade_ids: List[int],
        row_mapping: Dict[int, int],  # trade_id -> source_row
        broker_id: str = "unknown",
    ) -> str:
        """记录导入事件"""
        event_id = self._generate_event_id("import", file_hash)

        event = LineageEvent(
            event_id=event_id,
            event_type=TransformationType.IMPORT,
            timestamp=datetime.now(),
            affected_table="trades",
            affected_ids=trade_ids,
            source_info={
                "file_path": file_path,
                "file_hash": file_hash,
                "broker_id": broker_id,
                "total_rows": len(trade_ids),
            },
            description=f"Imported {len(trade_ids)} trades from {file_path}",
        )

        self._save_event(event)

        # 记录每条交易的来源
        conn = self._get_connection()
        cursor = conn.cursor()

        for trade_id in trade_ids:
            source_row = row_mapping.get(trade_id)
            cursor.execute("""
                INSERT OR REPLACE INTO data_lineage_records
                (record_table, record_id, source_file, source_row, import_batch_id, transformation_chain)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "trades",
                trade_id,
                file_path,
                source_row,
                event_id,
                json.dumps([event_id]),
            ))

        conn.commit()
        conn.close()

        return event_id

    def record_matching_event(
        self,
        position_ids: List[int],
        trade_mappings: Dict[int, List[int]],  # position_id -> trade_ids
        algorithm: str = "FIFO",
    ) -> str:
        """记录配对事件"""
        event_id = self._generate_event_id("match", str(position_ids[:5]))

        event = LineageEvent(
            event_id=event_id,
            event_type=TransformationType.MATCH,
            timestamp=datetime.now(),
            affected_table="positions",
            affected_ids=position_ids,
            source_info={
                "algorithm": algorithm,
                "total_positions": len(position_ids),
                "trade_mappings": trade_mappings,
            },
            description=f"Matched {len(position_ids)} positions using {algorithm}",
        )

        self._save_event(event)

        # 记录持仓的血缘
        conn = self._get_connection()
        cursor = conn.cursor()

        for position_id in position_ids:
            trade_ids = trade_mappings.get(position_id, [])
            # 获取关联交易的来源
            parent_events = []
            for trade_id in trade_ids:
                cursor.execute("""
                    SELECT transformation_chain FROM data_lineage_records
                    WHERE record_table = 'trades' AND record_id = ?
                """, (trade_id,))
                row = cursor.fetchone()
                if row and row['transformation_chain']:
                    parent_events.extend(json.loads(row['transformation_chain']))

            cursor.execute("""
                INSERT OR REPLACE INTO data_lineage_records
                (record_table, record_id, transformation_chain)
                VALUES (?, ?, ?)
            """, (
                "positions",
                position_id,
                json.dumps(list(set(parent_events)) + [event_id]),
            ))

        conn.commit()
        conn.close()

        return event_id

    def record_scoring_event(
        self,
        position_ids: List[int],
        scorer_version: str = "v2",
    ) -> str:
        """记录评分事件"""
        event_id = self._generate_event_id("score", str(position_ids[:5]))

        event = LineageEvent(
            event_id=event_id,
            event_type=TransformationType.SCORE,
            timestamp=datetime.now(),
            affected_table="positions",
            affected_ids=position_ids,
            source_info={
                "scorer_version": scorer_version,
                "total_scored": len(position_ids),
            },
            description=f"Scored {len(position_ids)} positions with {scorer_version}",
        )

        self._save_event(event)
        self._append_transformation(position_ids, "positions", event_id)

        return event_id

    def record_fix_event(
        self,
        table: str,
        record_ids: List[int],
        fix_type: str,
        changes: Dict[str, Any],
        rollback_sql: Optional[str] = None,
    ) -> str:
        """记录修复事件"""
        event_id = self._generate_event_id("fix", fix_type)

        event = LineageEvent(
            event_id=event_id,
            event_type=TransformationType.FIX,
            timestamp=datetime.now(),
            affected_table=table,
            affected_ids=record_ids,
            source_info={
                "fix_type": fix_type,
                "changes": changes,
            },
            description=f"Fixed {len(record_ids)} records in {table}: {fix_type}",
            rollback_sql=rollback_sql,
        )

        self._save_event(event)
        self._append_transformation(record_ids, table, event_id)

        return event_id

    # =========================================================================
    # 查询方法
    # =========================================================================

    def trace_record(self, table: str, record_id: int) -> Dict[str, Any]:
        """追踪单条记录的完整血缘"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 获取记录血缘
        cursor.execute("""
            SELECT * FROM data_lineage_records
            WHERE record_table = ? AND record_id = ?
        """, (table, record_id))
        lineage_record = cursor.fetchone()

        if not lineage_record:
            return {"error": "No lineage found for this record"}

        # 获取所有相关事件
        event_ids = json.loads(lineage_record['transformation_chain'] or '[]')
        events = []

        for event_id in event_ids:
            cursor.execute("""
                SELECT * FROM data_lineage_events WHERE event_id = ?
            """, (event_id,))
            event = cursor.fetchone()
            if event:
                events.append({
                    "event_id": event['event_id'],
                    "type": event['event_type'],
                    "timestamp": event['timestamp'],
                    "description": event['description'],
                    "source_info": json.loads(event['source_info'] or '{}'),
                })

        conn.close()

        return {
            "table": table,
            "record_id": record_id,
            "source_file": lineage_record['source_file'],
            "source_row": lineage_record['source_row'],
            "import_batch": lineage_record['import_batch_id'],
            "transformation_history": events,
        }

    def get_import_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取导入历史"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM data_lineage_events
            WHERE event_type = 'import'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        history = []
        for row in cursor.fetchall():
            source_info = json.loads(row['source_info'] or '{}')
            history.append({
                "event_id": row['event_id'],
                "timestamp": row['timestamp'],
                "file_path": source_info.get('file_path'),
                "file_hash": source_info.get('file_hash'),
                "broker_id": source_info.get('broker_id'),
                "total_records": source_info.get('total_rows'),
                "description": row['description'],
            })

        conn.close()
        return history

    def get_affected_records(self, event_id: str) -> Dict[str, Any]:
        """获取某事件影响的所有记录"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM data_lineage_events WHERE event_id = ?
        """, (event_id,))
        event = cursor.fetchone()

        if not event:
            return {"error": "Event not found"}

        affected_ids = json.loads(event['affected_ids'] or '[]')

        conn.close()

        return {
            "event_id": event_id,
            "type": event['event_type'],
            "table": event['affected_table'],
            "affected_count": len(affected_ids),
            "affected_ids": affected_ids,
            "source_info": json.loads(event['source_info'] or '{}'),
            "rollback_sql": event['rollback_sql'],
        }

    def find_records_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """查找来自特定文件的所有记录"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM data_lineage_records
            WHERE source_file = ?
        """, (file_path,))

        records = []
        for row in cursor.fetchall():
            records.append({
                "table": row['record_table'],
                "record_id": row['record_id'],
                "source_row": row['source_row'],
                "import_batch": row['import_batch_id'],
            })

        conn.close()
        return records

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def _generate_event_id(self, event_type: str, seed: str) -> str:
        """生成事件 ID"""
        content = f"{event_type}:{seed}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _save_event(self, event: LineageEvent):
        """保存事件"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO data_lineage_events
            (event_id, event_type, timestamp, affected_table, affected_ids,
             source_info, user, description, rollback_sql)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            event.event_type.value,
            event.timestamp.isoformat(),
            event.affected_table,
            json.dumps(event.affected_ids),
            json.dumps(event.source_info),
            event.user,
            event.description,
            event.rollback_sql,
        ))

        conn.commit()
        conn.close()

    def _append_transformation(self, record_ids: List[int], table: str, event_id: str):
        """追加转换事件到记录血缘"""
        conn = self._get_connection()
        cursor = conn.cursor()

        for record_id in record_ids:
            cursor.execute("""
                SELECT transformation_chain FROM data_lineage_records
                WHERE record_table = ? AND record_id = ?
            """, (table, record_id))
            row = cursor.fetchone()

            if row:
                chain = json.loads(row['transformation_chain'] or '[]')
                chain.append(event_id)
                cursor.execute("""
                    UPDATE data_lineage_records
                    SET transformation_chain = ?
                    WHERE record_table = ? AND record_id = ?
                """, (json.dumps(chain), table, record_id))
            else:
                cursor.execute("""
                    INSERT INTO data_lineage_records
                    (record_table, record_id, transformation_chain)
                    VALUES (?, ?, ?)
                """, (table, record_id, json.dumps([event_id])))

        conn.commit()
        conn.close()


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/tradingcoach.db"

    tracker = DataLineageTracker(db_path)

    # 示例：获取导入历史
    history = tracker.get_import_history()
    print("Import History:")
    print(json.dumps(history, indent=2, ensure_ascii=False))
