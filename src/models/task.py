"""
分析任务模型

input: SQLAlchemy Base
output: Task 模型类
pos: 数据层 - 存储异步分析任务状态

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from src.models.base import Base


class TaskStatus:
    """任务状态枚举"""
    PENDING = "pending"          # 等待处理
    RUNNING = "running"          # 正在处理
    COMPLETED = "completed"      # 处理完成
    FAILED = "failed"            # 处理失败
    CANCELLED = "cancelled"      # 已取消


class TaskType:
    """任务类型枚举"""
    CSV_ANALYSIS = "csv_analysis"  # CSV 导入分析


class Task(Base):
    """
    异步分析任务

    用于追踪 CSV 导入和分析的进度状态
    """
    __tablename__ = 'tasks'

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 任务标识
    task_id = Column(String(64), unique=True, nullable=False, index=True)  # UUID
    task_type = Column(String(32), nullable=False, default=TaskType.CSV_ANALYSIS)

    # 状态
    status = Column(String(20), nullable=False, default=TaskStatus.PENDING)
    progress = Column(Float, default=0.0)  # 0.0 - 100.0
    current_step = Column(String(100))     # 当前步骤描述

    # 文件信息
    file_name = Column(String(255))
    file_hash = Column(String(64))
    file_size = Column(Integer)

    # 通知设置
    email = Column(String(255))  # 用户邮箱（可选）

    # 处理结果
    result = Column(JSON)  # 存储完整处理结果

    # 错误信息
    error_message = Column(Text)

    # 日志
    logs = Column(JSON)  # 处理过程日志列表

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<Task {self.task_id} [{self.status}] {self.progress:.1f}%>"

    def to_dict(self):
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "file_name": self.file_name,
            "file_hash": self.file_hash,
            "email": self.email,
            "result": self.result,
            "error_message": self.error_message,
            "logs": self.logs or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def add_log(self, message: str, level: str = "info"):
        """添加日志条目"""
        if self.logs is None:
            self.logs = []

        self.logs.append({
            "time": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        })

    def update_progress(self, progress: float, step: str = None):
        """更新进度"""
        self.progress = min(100.0, max(0.0, progress))
        if step:
            self.current_step = step
            self.add_log(step)
