"""
任务管理 API

input: 任务创建请求、文件上传
output: 任务状态、进度、结果
pos: 后端 API 层 - 提供异步任务管理接口

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import os
import sys
import tempfile
import hashlib
from pathlib import Path
from typing import Optional, List
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, EmailStr

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.task_manager import task_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 请求/响应模型 ====================

class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    email: Optional[str] = None  # 邮箱可选
    replace_mode: bool = True    # 默认替换模式


class TaskCreateResponse(BaseModel):
    """创建任务响应"""
    success: bool
    task_id: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: float
    current_step: Optional[str]
    file_name: Optional[str]
    email: Optional[str]
    result: Optional[dict]
    error_message: Optional[str]
    logs: List[dict]
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskStatusResponse]
    total: int


# ==================== API 端点 ====================

@router.post("/create", response_model=TaskCreateResponse)
async def create_analysis_task(
    file: UploadFile = File(...),
    email: Optional[str] = Query(None, description="通知邮箱（可选）"),
    replace_mode: bool = Query(True, description="替换模式（默认清除旧数据）")
):
    """
    创建 CSV 分析任务

    上传 CSV 文件并创建异步分析任务。
    任务会在后台执行：导入 → 配对 → 评分

    - **file**: CSV 文件（必需）
    - **email**: 完成后通知邮箱（可选）
    - **replace_mode**: 是否清除现有数据后再导入（默认 True）
    """
    # 验证文件类型
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="仅支持 CSV 文件格式"
        )

    try:
        # 读取文件内容
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        file_size = len(content)

        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        logger.info(f"File uploaded: {file.filename}, size={file_size}, hash={file_hash}")

        # 创建任务
        task_id = task_manager.create_task(
            file_name=file.filename,
            file_hash=file_hash,
            file_size=file_size,
            file_path=tmp_path,
            email=email,
            replace_mode=replace_mode
        )

        return TaskCreateResponse(
            success=True,
            task_id=task_id,
            message=f"任务已创建，正在后台处理"
        )

    except Exception as e:
        logger.error(f"Failed to create task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态

    查询任务的当前状态、进度和结果
    """
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    return TaskStatusResponse(**task)


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    取消任务

    取消正在等待或执行中的任务
    """
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    if task['status'] in ['completed', 'failed', 'cancelled']:
        raise HTTPException(
            status_code=400,
            detail=f"任务已结束，无法取消"
        )

    success = task_manager.cancel_task(task_id)

    if success:
        return {"success": True, "message": "任务已取消"}
    else:
        return {"success": False, "message": "无法取消任务（可能已在执行中）"}


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None, description="按状态筛选")
):
    """
    获取任务列表

    获取最近的任务列表，支持按状态筛选
    """
    import config
    from src.models.base import init_database, get_session
    from src.models.task import Task

    init_database(config.DATABASE_URL, echo=False)
    session = get_session()

    try:
        query = session.query(Task).order_by(Task.created_at.desc())

        if status:
            query = query.filter(Task.status == status)

        tasks = query.limit(limit).all()
        total = query.count()

        return TaskListResponse(
            tasks=[TaskStatusResponse(**t.to_dict()) for t in tasks],
            total=total
        )

    finally:
        session.close()
