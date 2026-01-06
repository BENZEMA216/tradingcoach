"""
Data Quality Auto-Fixer - 数据质量自动修复工具

input: SQLite database, anomaly reports
output: Fixed data, rollback scripts
pos: 数据质量保障 - 自动修复常见数据问题

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import sqlite3
import json
import logging

from .data_lineage import DataLineageTracker, TransformationType


class FixAction(Enum):
    """修复动作类型"""
    DELETE = "delete"
    UPDATE = "update"
    INSERT = "insert"
    RECALCULATE = "recalculate"


@dataclass
class FixResult:
    """修复结果"""
    success: bool
    action: FixAction
    table: str
    affected_count: int
    rollback_sql: str
    message: str
    event_id: Optional[str] = None


class DataFixer:
    """数据质量修复器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lineage = DataLineageTracker(db_path)
        self.logger = logging.getLogger(__name__)
        self.fix_history: List[FixResult] = []

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # 交易数据修复
    # =========================================================================

    def fix_duplicate_trades(self, dry_run: bool = True) -> FixResult:
        """修复重复交易记录 (保留最早的)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 查找重复
        cursor.execute("""
            SELECT trade_fingerprint, GROUP_CONCAT(id) as ids, COUNT(*) as cnt
            FROM trades
            WHERE trade_fingerprint IS NOT NULL
            GROUP BY trade_fingerprint
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()

        if not duplicates:
            conn.close()
            return FixResult(
                success=True,
                action=FixAction.DELETE,
                table="trades",
                affected_count=0,
                rollback_sql="",
                message="No duplicate trades found",
            )

        # 收集要删除的 ID
        ids_to_delete = []
        for row in duplicates:
            ids = [int(i) for i in row['ids'].split(',')]
            ids.sort()  # 保留最小 ID (最早的)
            ids_to_delete.extend(ids[1:])  # 删除其他

        # 生成回滚 SQL
        cursor.execute(f"""
            SELECT * FROM trades WHERE id IN ({','.join(map(str, ids_to_delete))})
        """)
        deleted_records = cursor.fetchall()

        rollback_sql = self._generate_insert_sql("trades", deleted_records)

        if not dry_run:
            cursor.execute(f"""
                DELETE FROM trades WHERE id IN ({','.join(map(str, ids_to_delete))})
            """)
            conn.commit()

            # 记录血缘
            event_id = self.lineage.record_fix_event(
                table="trades",
                record_ids=ids_to_delete,
                fix_type="remove_duplicates",
                changes={"action": "delete", "count": len(ids_to_delete)},
                rollback_sql=rollback_sql,
            )
        else:
            event_id = None

        conn.close()

        result = FixResult(
            success=True,
            action=FixAction.DELETE,
            table="trades",
            affected_count=len(ids_to_delete),
            rollback_sql=rollback_sql,
            message=f"{'Would delete' if dry_run else 'Deleted'} {len(ids_to_delete)} duplicate trades",
            event_id=event_id,
        )
        self.fix_history.append(result)
        return result

    def fix_orphan_position_ids(self, dry_run: bool = True) -> FixResult:
        """修复无效的 position_id 外键"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 查找无效外键
        cursor.execute("""
            SELECT t.id, t.position_id
            FROM trades t
            LEFT JOIN positions p ON t.position_id = p.id
            WHERE t.position_id IS NOT NULL AND p.id IS NULL
        """)
        invalid_fks = cursor.fetchall()

        if not invalid_fks:
            conn.close()
            return FixResult(
                success=True,
                action=FixAction.UPDATE,
                table="trades",
                affected_count=0,
                rollback_sql="",
                message="No invalid position_id found",
            )

        ids_to_fix = [row['id'] for row in invalid_fks]
        old_values = {row['id']: row['position_id'] for row in invalid_fks}

        # 生成回滚 SQL
        rollback_parts = []
        for trade_id, old_pos_id in old_values.items():
            rollback_parts.append(f"UPDATE trades SET position_id = {old_pos_id} WHERE id = {trade_id};")
        rollback_sql = "\n".join(rollback_parts)

        if not dry_run:
            cursor.execute(f"""
                UPDATE trades SET position_id = NULL
                WHERE id IN ({','.join(map(str, ids_to_fix))})
            """)
            conn.commit()

            event_id = self.lineage.record_fix_event(
                table="trades",
                record_ids=ids_to_fix,
                fix_type="clear_invalid_position_id",
                changes={"old_values": old_values, "new_value": None},
                rollback_sql=rollback_sql,
            )
        else:
            event_id = None

        conn.close()

        result = FixResult(
            success=True,
            action=FixAction.UPDATE,
            table="trades",
            affected_count=len(ids_to_fix),
            rollback_sql=rollback_sql,
            message=f"{'Would fix' if dry_run else 'Fixed'} {len(ids_to_fix)} invalid position_id references",
            event_id=event_id,
        )
        self.fix_history.append(result)
        return result

    # =========================================================================
    # 持仓数据修复
    # =========================================================================

    def fix_position_scores_range(self, dry_run: bool = True) -> FixResult:
        """修复超出范围的评分 (限制在 0-100)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        score_fields = [
            'entry_quality_score', 'exit_quality_score',
            'trend_quality_score', 'risk_mgmt_score', 'overall_score'
        ]

        total_fixed = 0
        rollback_parts = []

        for field in score_fields:
            # 查找超出范围的
            cursor.execute(f"""
                SELECT id, {field} FROM positions
                WHERE {field} IS NOT NULL AND ({field} < 0 OR {field} > 100)
            """)
            invalid = cursor.fetchall()

            if invalid:
                for row in invalid:
                    old_value = row[field]
                    new_value = max(0, min(100, old_value))
                    rollback_parts.append(
                        f"UPDATE positions SET {field} = {old_value} WHERE id = {row['id']};"
                    )

                    if not dry_run:
                        cursor.execute(f"""
                            UPDATE positions SET {field} = ? WHERE id = ?
                        """, (new_value, row['id']))

                total_fixed += len(invalid)

        if not dry_run and total_fixed > 0:
            conn.commit()

        rollback_sql = "\n".join(rollback_parts)
        conn.close()

        result = FixResult(
            success=True,
            action=FixAction.UPDATE,
            table="positions",
            affected_count=total_fixed,
            rollback_sql=rollback_sql,
            message=f"{'Would fix' if dry_run else 'Fixed'} {total_fixed} out-of-range scores",
        )
        self.fix_history.append(result)
        return result

    def recalculate_net_pnl(self, position_ids: Optional[List[int]] = None, dry_run: bool = True) -> FixResult:
        """重新计算净盈亏 (net_pnl = realized_pnl - total_fees)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if position_ids:
            where_clause = f"WHERE id IN ({','.join(map(str, position_ids))})"
        else:
            where_clause = "WHERE realized_pnl IS NOT NULL AND total_fees IS NOT NULL"

        cursor.execute(f"""
            SELECT id, realized_pnl, total_fees, net_pnl
            FROM positions
            {where_clause}
        """)
        positions = cursor.fetchall()

        fixes = []
        rollback_parts = []

        for pos in positions:
            expected_net_pnl = pos['realized_pnl'] - (pos['total_fees'] or 0)
            if pos['net_pnl'] is None or abs(pos['net_pnl'] - expected_net_pnl) > 0.01:
                fixes.append((pos['id'], expected_net_pnl, pos['net_pnl']))
                rollback_parts.append(
                    f"UPDATE positions SET net_pnl = {pos['net_pnl']} WHERE id = {pos['id']};"
                )

        if not dry_run and fixes:
            for pos_id, new_value, _ in fixes:
                cursor.execute("""
                    UPDATE positions SET net_pnl = ? WHERE id = ?
                """, (new_value, pos_id))
            conn.commit()

            event_id = self.lineage.record_fix_event(
                table="positions",
                record_ids=[f[0] for f in fixes],
                fix_type="recalculate_net_pnl",
                changes={"formula": "net_pnl = realized_pnl - total_fees"},
                rollback_sql="\n".join(rollback_parts),
            )
        else:
            event_id = None

        conn.close()

        result = FixResult(
            success=True,
            action=FixAction.RECALCULATE,
            table="positions",
            affected_count=len(fixes),
            rollback_sql="\n".join(rollback_parts),
            message=f"{'Would recalculate' if dry_run else 'Recalculated'} net_pnl for {len(fixes)} positions",
            event_id=event_id,
        )
        self.fix_history.append(result)
        return result

    def recalculate_holding_period(self, dry_run: bool = True) -> FixResult:
        """重新计算持仓天数"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, open_time, close_time, holding_period_days
            FROM positions
            WHERE status = 'CLOSED' AND open_time IS NOT NULL AND close_time IS NOT NULL
        """)
        positions = cursor.fetchall()

        fixes = []
        rollback_parts = []

        for pos in positions:
            open_time = datetime.fromisoformat(pos['open_time'].replace('Z', '+00:00').replace(' ', 'T'))
            close_time = datetime.fromisoformat(pos['close_time'].replace('Z', '+00:00').replace(' ', 'T'))
            expected_days = (close_time - open_time).days

            if pos['holding_period_days'] != expected_days:
                fixes.append((pos['id'], expected_days, pos['holding_period_days']))
                rollback_parts.append(
                    f"UPDATE positions SET holding_period_days = {pos['holding_period_days']} WHERE id = {pos['id']};"
                )

        if not dry_run and fixes:
            for pos_id, new_value, _ in fixes:
                cursor.execute("""
                    UPDATE positions SET holding_period_days = ? WHERE id = ?
                """, (new_value, pos_id))
            conn.commit()

        conn.close()

        result = FixResult(
            success=True,
            action=FixAction.RECALCULATE,
            table="positions",
            affected_count=len(fixes),
            rollback_sql="\n".join(rollback_parts),
            message=f"{'Would recalculate' if dry_run else 'Recalculated'} holding_period_days for {len(fixes)} positions",
        )
        self.fix_history.append(result)
        return result

    # =========================================================================
    # 批量修复
    # =========================================================================

    def run_all_fixes(self, dry_run: bool = True) -> Dict[str, Any]:
        """运行所有自动修复"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "fixes": [],
            "total_affected": 0,
        }

        # 运行所有修复
        fix_methods = [
            ("Remove duplicate trades", self.fix_duplicate_trades),
            ("Fix invalid position_id", self.fix_orphan_position_ids),
            ("Fix out-of-range scores", self.fix_position_scores_range),
            ("Recalculate net_pnl", self.recalculate_net_pnl),
            ("Recalculate holding_period", self.recalculate_holding_period),
        ]

        for name, method in fix_methods:
            try:
                result = method(dry_run=dry_run)
                results["fixes"].append({
                    "name": name,
                    "success": result.success,
                    "affected_count": result.affected_count,
                    "message": result.message,
                })
                results["total_affected"] += result.affected_count
            except Exception as e:
                results["fixes"].append({
                    "name": name,
                    "success": False,
                    "error": str(e),
                })

        return results

    def rollback(self, event_id: str) -> FixResult:
        """回滚指定的修复事件"""
        affected = self.lineage.get_affected_records(event_id)

        if "error" in affected:
            return FixResult(
                success=False,
                action=FixAction.UPDATE,
                table="unknown",
                affected_count=0,
                rollback_sql="",
                message=f"Event not found: {event_id}",
            )

        if not affected.get('rollback_sql'):
            return FixResult(
                success=False,
                action=FixAction.UPDATE,
                table=affected['table'],
                affected_count=0,
                rollback_sql="",
                message="No rollback SQL available for this event",
            )

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            for sql in affected['rollback_sql'].split(';'):
                sql = sql.strip()
                if sql:
                    cursor.execute(sql)
            conn.commit()
            success = True
            message = f"Successfully rolled back event {event_id}"
        except Exception as e:
            conn.rollback()
            success = False
            message = f"Rollback failed: {str(e)}"

        conn.close()

        return FixResult(
            success=success,
            action=FixAction.UPDATE,
            table=affected['table'],
            affected_count=affected['affected_count'],
            rollback_sql=affected['rollback_sql'],
            message=message,
        )

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def _generate_insert_sql(self, table: str, rows: List[sqlite3.Row]) -> str:
        """生成 INSERT SQL 用于回滚"""
        if not rows:
            return ""

        columns = rows[0].keys()
        sql_parts = []

        for row in rows:
            values = []
            for col in columns:
                val = row[col]
                if val is None:
                    values.append("NULL")
                elif isinstance(val, str):
                    values.append(f"'{val}'")
                else:
                    values.append(str(val))

            sql_parts.append(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});"
            )

        return "\n".join(sql_parts)


def run_auto_fix(db_path: str, dry_run: bool = True) -> Dict[str, Any]:
    """运行自动修复"""
    fixer = DataFixer(db_path)
    return fixer.run_all_fixes(dry_run=dry_run)


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/tradingcoach.db"
    dry_run = "--apply" not in sys.argv

    print(f"Running data fixes (dry_run={dry_run})...")
    results = run_auto_fix(db_path, dry_run=dry_run)
    print(json.dumps(results, indent=2, ensure_ascii=False))
