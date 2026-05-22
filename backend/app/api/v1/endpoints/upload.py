"""
CSV上传API

input: UploadFile (CSV文件)
output: 预检结果或导入结果JSON (成功/新增数/跳过数/配对数/评分数)
pos: 后端上传端点 - 接收CSV、预检格式、调用增量导入器、触发后续处理

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

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.base import init_database, get_session, create_all_tables
from src.importers.english_csv_parser import detect_csv_language, EnglishCSVParser
from src.importers.csv_parser import CSVParser
from src.importers.incremental_importer import IncrementalImporter
from src.importers.import_preflight import preview_import_file
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

    # 模式："incremental"（与已有数据合并去重）或 "replace"（先清空再导入）
    mode: str = "incremental"
    cleared_existing: bool = False  # 本次上传是否清空了旧数据

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


class UploadPreflightResponse(BaseModel):
    """上传前预检响应"""
    can_import: bool
    file_name: str
    file_hash: str
    broker_id: Optional[str] = None
    broker_name: Optional[str] = None
    detection_confidence: float = 0.0
    total_rows: int = 0
    completed_trades: int = 0
    skipped_rows: int = 0
    detected_columns: list[str] = Field(default_factory=list)
    error_messages: list[str] = Field(default_factory=list)
    warning_messages: list[str] = Field(default_factory=list)


def clear_all_trading_data(session):
    """清除所有交易数据，为新一批数据导入做准备"""
    from sqlalchemy import text

    # 按顺序删除（注意外键依赖）
    tables_to_clear = [
        'positions',      # 持仓记录
        'trades',         # 交易记录
        'import_history', # 导入历史
    ]

    for table in tables_to_clear:
        try:
            session.execute(text(f"DELETE FROM {table}"))
            logger.info(f"Cleared table: {table}")
        except Exception as e:
            logger.warning(f"Failed to clear {table}: {e}")

    session.commit()
    logger.info("All trading data cleared for fresh import")


@router.post("/trades/preview", response_model=UploadPreflightResponse)
async def preview_trades_upload(file: UploadFile = File(...)):
    """上传前只读预检交易 CSV，不写入数据库。"""
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    tmp_path = None
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = preview_import_file(tmp_path, file_name=file.filename)
        return UploadPreflightResponse(**result.to_dict())

    except UnicodeDecodeError as e:
        logger.warning(f"Upload preview not UTF-8 decodable: {e}")
        raise HTTPException(
            status_code=400,
            detail="File is not a valid text CSV. Please export from your broker as CSV.",
        )
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="CSV file is empty or has no parseable columns.",
        )
    except pd.errors.ParserError as e:
        logger.warning(f"CSV preview parse error: {e}")
        raise HTTPException(
            status_code=400,
            detail="CSV file is malformed and could not be parsed.",
        )
    except Exception as e:
        logger.error(f"Upload preview failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Upload preview failed. Check server logs for details.",
        )
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.post("/trades", response_model=UploadResponse)
async def upload_trades(
    file: UploadFile = File(...),
    replace_mode: bool = False,  # 默认增量去重；replace=True 才会清空旧数据
):
    """
    上传交易记录CSV文件

    支持富途证券导出的中文/英文CSV格式

    - replace_mode=False (默认): 增量导入，按 trade_fingerprint 与现有数据去重
    - replace_mode=True: 先清空所有旧 trades/positions/import_history 再导入

    注意：旧版默认是 replace_mode=True，会在每次上传时静默清空整库。
    现在改为默认增量，避免重复上传同一文件时数据被反复清空、
    "duplicates_skipped" 字段始终为 0 的误导性表现。
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

        # 替换模式：先清除所有旧数据
        if replace_mode:
            logger.info("Replace mode enabled - clearing all existing data")
            engine = init_database(config.DATABASE_URL, echo=False)
            session = get_session()
            try:
                clear_all_trading_data(session)
            finally:
                session.close()

        # 导入（替换模式下相当于全新导入）
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
                match_result = matcher.match_all_trades()
                positions_matched = match_result.get('positions_created', 0)

                # 评分
                logger.info("Running quality scoring...")
                scorer = QualityScorer()
                score_result = scorer.score_all_positions(session, update_db=True)
                positions_scored = score_result.get('scored', 0)
                logger.info(f"Scoring completed: {positions_scored} positions scored")

                session.commit()

            except Exception as e:
                logger.error(f"Matching/scoring error: {e}")
                session.rollback()
            finally:
                session.close()

        # 计算处理时间
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        mode_label = "replace" if replace_mode else "incremental"
        if replace_mode:
            human_msg = (
                f"Replaced existing data; imported {result.new_trades} trades "
                f"from {file.filename}"
            )
        else:
            human_msg = (
                f"Imported {result.new_trades} new trades, "
                f"skipped {result.duplicates_skipped} duplicates"
            )
        return UploadResponse(
            success=True,
            message=human_msg,
            file_name=file.filename,
            file_hash=file_hash[:16],
            language=language,
            mode=mode_label,
            cleared_existing=replace_mode,
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
    except UnicodeDecodeError as e:
        # 上传的不是 UTF-8 文本（典型：把图片/二进制当 CSV 上传）
        logger.warning(f"Upload not UTF-8 decodable: {e}")
        raise HTTPException(
            status_code=400,
            detail="File is not a valid UTF-8 text CSV. Please export from your broker as CSV.",
        )
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="CSV file is empty or has no parseable columns.",
        )
    except pd.errors.ParserError as e:
        logger.warning(f"CSV parse error: {e}")
        raise HTTPException(
            status_code=400,
            detail="CSV file is malformed and could not be parsed.",
        )
    except Exception as e:
        logger.error(f"Upload processing failed: {e}", exc_info=True)
        # 不把内部异常细节抛给客户端，避免栈/路径泄漏
        raise HTTPException(
            status_code=500,
            detail="Upload processing failed. Check server logs for details.",
        )

    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
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
        except Exception:
            pass
