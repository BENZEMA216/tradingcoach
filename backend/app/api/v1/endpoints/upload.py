"""
CSV上传API

input: UploadFile (CSV文件)
output: 导入结果JSON (成功/新增数/跳过数/配对数/评分数)
pos: 后端上传端点 - 接收CSV、调用增量导入器、触发后续处理

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import os
import sys
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.base import init_database, get_session, create_all_tables
from src.importers.english_csv_parser import detect_csv_language, EnglishCSVParser
from src.importers.csv_parser import CSVParser
from src.importers.incremental_importer import IncrementalImporter
from src.matchers.fifo_matcher import FIFOMatcher
from src.analyzers.quality_scorer import QualityScorer

logger = logging.getLogger(__name__)

router = APIRouter()


class UploadResponse(BaseModel):
    """上传响应"""
    success: bool
    message: str
    file_name: str
    file_hash: str
    language: str

    # 处理结果
    total_rows: int = 0
    completed_trades: int = 0
    new_trades: int = 0
    duplicates_skipped: int = 0
    positions_matched: int = 0
    positions_scored: int = 0

    # 耗时
    processing_time_ms: int = 0

    # 错误
    errors: int = 0
    error_messages: list = []


class UploadHistoryItem(BaseModel):
    """导入历史项"""
    id: int
    import_time: str
    file_name: str
    file_type: str
    total_rows: int
    new_trades: int
    duplicates_skipped: int
    status: str


@router.post("/trades", response_model=UploadResponse)
async def upload_trades(file: UploadFile = File(...)):
    """
    上传交易记录CSV文件

    支持富途证券导出的中文/英文CSV格式
    自动去重，只导入新交易
    """
    start_time = datetime.now()

    # 验证文件类型
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # 保存临时文件
    try:
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        logger.info(f"Uploaded file saved to {tmp_path}, size={len(content)} bytes")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        # 检测语言
        language = detect_csv_language(tmp_path)
        logger.info(f"Detected language: {language}")

        if language == 'unknown':
            raise HTTPException(
                status_code=400,
                detail="Unsupported CSV format. Please use Futu Securities export."
            )

        # 增量导入
        importer = IncrementalImporter(tmp_path, dry_run=False)
        result = importer.run()

        # 如果有新交易，执行配对和评分
        positions_matched = 0
        positions_scored = 0

        if result.new_trades > 0:
            engine = init_database(config.DATABASE_URL, echo=False)
            session = get_session()

            try:
                # FIFO配对
                logger.info("Running FIFO matching...")
                matcher = FIFOMatcher(session)
                match_result = matcher.match_all()
                positions_matched = match_result.get('positions_created', 0)

                # 评分
                logger.info("Running quality scoring...")
                scorer = QualityScorer()

                # 获取未评分的持仓
                from sqlalchemy import text
                unscored = session.execute(text("""
                    SELECT id FROM positions
                    WHERE overall_score IS NULL OR overall_score = 0
                """)).fetchall()

                for (pos_id,) in unscored:
                    try:
                        scorer.score_position(pos_id, session)
                        positions_scored += 1
                    except Exception as e:
                        logger.warning(f"Failed to score position {pos_id}: {e}")

                session.commit()

            except Exception as e:
                logger.error(f"Matching/scoring error: {e}")
                session.rollback()
            finally:
                session.close()

        # 计算处理时间
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return UploadResponse(
            success=True,
            message=f"Successfully processed {result.new_trades} new trades",
            file_name=file.filename,
            file_hash=file_hash[:16],
            language=language,
            total_rows=result.total_rows,
            completed_trades=result.completed_trades,
            new_trades=result.new_trades,
            duplicates_skipped=result.duplicates_skipped,
            positions_matched=positions_matched,
            positions_scored=positions_scored,
            processing_time_ms=processing_time,
            errors=result.errors,
            error_messages=result.error_messages[:10],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass


@router.get("/history", response_model=list[UploadHistoryItem])
async def get_upload_history(limit: int = 20):
    """获取导入历史"""
    engine = init_database(config.DATABASE_URL, echo=False)
    session = get_session()

    try:
        from sqlalchemy import text
        result = session.execute(text("""
            SELECT id, import_time, file_name, file_type,
                   total_rows, new_trades, duplicates_skipped, status
            FROM import_history
            ORDER BY import_time DESC
            LIMIT :limit
        """), {'limit': limit})

        items = []
        for row in result.fetchall():
            items.append(UploadHistoryItem(
                id=row[0],
                import_time=str(row[1]),
                file_name=row[2] or '',
                file_type=row[3] or '',
                total_rows=row[4] or 0,
                new_trades=row[5] or 0,
                duplicates_skipped=row[6] or 0,
                status=row[7] or '',
            ))

        return items

    finally:
        session.close()


@router.post("/snapshot")
async def upload_position_snapshot(file: UploadFile = File(...)):
    """
    上传持仓快照CSV文件

    用于与系统计算的持仓进行对账
    """
    # 验证文件类型
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # 保存临时文件
    try:
        content = await file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        # 执行对账
        from src.reconciler.position_reconciler import PositionReconciler

        reconciler = PositionReconciler(tmp_path)
        report = reconciler.reconcile()

        return {
            "success": True,
            "message": "Reconciliation completed",
            "snapshot_date": str(report.snapshot_date),
            "summary": {
                "total_positions": report.total_positions,
                "matched": report.matched_count,
                "quantity_mismatch": report.quantity_mismatch_count,
                "missing_in_system": report.missing_in_system_count,
                "missing_in_broker": report.missing_in_broker_count,
            },
            "items": [item.to_dict() for item in report.items],
        }

    except Exception as e:
        logger.error(f"Reconciliation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass
