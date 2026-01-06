"""
System API endpoints

input: 无
output: 系统状态、统计信息、数据重置
pos: 系统管理端点 - 健康检查、数据统计、数据重置

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from ....database import get_db, Position, Trade, MarketData

logger = logging.getLogger(__name__)

router = APIRouter()


class DataResetResponse(BaseModel):
    """数据重置响应"""
    success: bool
    message: str
    deleted_counts: dict
    timestamp: str


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
):
    """
    Get system statistics (database counts, etc.).
    """
    # Count records in each table
    position_count = db.query(func.count(Position.id)).scalar()
    trade_count = db.query(func.count(Trade.id)).scalar()
    market_data_count = db.query(func.count(MarketData.id)).scalar()

    # Get date ranges
    position_dates = db.query(
        func.min(Position.open_date),
        func.max(Position.close_date),
    ).first()

    trade_dates = db.query(
        func.min(Trade.trade_date),
        func.max(Trade.trade_date),
    ).first()

    market_data_dates = db.query(
        func.min(MarketData.date),
        func.max(MarketData.date),
    ).first()

    # Get unique symbols
    position_symbols = db.query(func.count(func.distinct(Position.symbol))).scalar()
    market_data_symbols = db.query(func.count(func.distinct(MarketData.symbol))).scalar()

    return {
        "database": {
            "positions": {
                "count": position_count,
                "symbols": position_symbols,
                "date_range": {
                    "start": position_dates[0].isoformat() if position_dates[0] else None,
                    "end": position_dates[1].isoformat() if position_dates[1] else None,
                },
            },
            "trades": {
                "count": trade_count,
                "date_range": {
                    "start": trade_dates[0].isoformat() if trade_dates[0] else None,
                    "end": trade_dates[1].isoformat() if trade_dates[1] else None,
                },
            },
            "market_data": {
                "count": market_data_count,
                "symbols": market_data_symbols,
                "date_range": {
                    "start": market_data_dates[0].isoformat() if market_data_dates[0] else None,
                    "end": market_data_dates[1].isoformat() if market_data_dates[1] else None,
                },
            },
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/symbols")
async def list_all_symbols(
    db: Session = Depends(get_db),
):
    """
    Get list of all symbols in the system.
    """
    # Get symbols from positions
    position_symbols = (
        db.query(Position.symbol, Position.symbol_name)
        .distinct()
        .order_by(Position.symbol)
        .all()
    )

    # Get symbols from market data
    market_data_symbols = (
        db.query(MarketData.symbol)
        .distinct()
        .order_by(MarketData.symbol)
        .all()
    )

    # Combine and dedupe
    symbols = {}
    for symbol, name in position_symbols:
        symbols[symbol] = {
            "symbol": symbol,
            "name": name,
            "has_positions": True,
            "has_market_data": False,
        }

    for (symbol,) in market_data_symbols:
        if symbol in symbols:
            symbols[symbol]["has_market_data"] = True
        else:
            symbols[symbol] = {
                "symbol": symbol,
                "name": None,
                "has_positions": False,
                "has_market_data": True,
            }

    return {
        "symbols": list(symbols.values()),
        "total": len(symbols),
    }


@router.delete("/data/reset", response_model=DataResetResponse)
async def reset_all_data(
    db: Session = Depends(get_db),
):
    """
    重置所有交易数据，清空数据库准备重新上传。

    此操作将删除：
    - 所有持仓记录 (positions)
    - 所有交易记录 (trades)
    - 所有导入历史 (import_history)
    - 所有任务记录 (tasks)

    警告：此操作不可撤销！
    """
    deleted_counts = {}

    try:
        # 先统计各表记录数
        position_count = db.query(func.count(Position.id)).scalar() or 0
        trade_count = db.query(func.count(Trade.id)).scalar() or 0

        # 统计 import_history 和 tasks
        import_history_count = 0
        tasks_count = 0
        try:
            result = db.execute(text("SELECT COUNT(*) FROM import_history"))
            import_history_count = result.scalar() or 0
        except Exception:
            pass

        try:
            result = db.execute(text("SELECT COUNT(*) FROM tasks"))
            tasks_count = result.scalar() or 0
        except Exception:
            pass

        # 按顺序删除（注意外键依赖）
        tables_to_clear = [
            ('positions', position_count),
            ('trades', trade_count),
            ('import_history', import_history_count),
            ('tasks', tasks_count),
        ]

        for table, count in tables_to_clear:
            try:
                db.execute(text(f"DELETE FROM {table}"))
                deleted_counts[table] = count
                logger.info(f"Cleared table: {table} ({count} records)")
            except Exception as e:
                logger.warning(f"Failed to clear {table}: {e}")
                deleted_counts[table] = 0

        db.commit()
        logger.info("All trading data cleared for fresh import")

        total_deleted = sum(deleted_counts.values())

        return DataResetResponse(
            success=True,
            message=f"Successfully deleted {total_deleted} records",
            deleted_counts=deleted_counts,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reset data: {e}")
        return DataResetResponse(
            success=False,
            message=f"Failed to reset data: {str(e)}",
            deleted_counts=deleted_counts,
            timestamp=datetime.utcnow().isoformat(),
        )
