"""
任务管理器

input: Task 模型, 配置, EventDetector, optional workspace database URL
output: 任务创建、执行、状态追踪
pos: 后端服务层 - 管理异步分析任务的执行，支持匿名 workspace 隔离

功能:
- 异步任务执行 (ThreadPoolExecutor)
- 详细处理日志 (每条交易/持仓/评分/事件)
- 进度追踪 (0-100%)
- 市场数据源不可用时降级继续分析
- 事件检测 (财报/价格异常/成交量异常)
- 完成通知 (邮件)

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
import uuid
import logging
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor
import threading

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.base import init_database, get_session, create_all_tables
from src.models.task import Task, TaskStatus, TaskType

logger = logging.getLogger(__name__)

# 日志配置
MAX_LOGS = 1000  # 最大日志条数（增加以容纳更多日志）
LOG_BATCH_SIZE = 1  # 每条都记录，让日志更频繁
import time  # 用于添加小延迟让动画更明显


class TaskManager:
    """
    任务管理器（单例模式）

    使用线程池执行异步任务，任务状态存储在 SQLite 中
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 获取配置
        max_workers = getattr(config, 'TASK_MAX_CONCURRENT', 3)

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks = {}  # task_id -> Future
        self._task_database_urls = {}  # task_id -> database_url
        self._initialized = True

        logger.info(f"TaskManager initialized with {max_workers} workers")

    def create_task(
        self,
        file_name: str,
        file_hash: str,
        file_size: int,
        file_path: str,
        email: Optional[str] = None,
        replace_mode: bool = True,
        database_url: Optional[str] = None,
    ) -> str:
        """
        创建新任务

        Args:
            file_name: 文件名
            file_hash: 文件哈希
            file_size: 文件大小
            file_path: 临时文件路径
            email: 通知邮箱（可选）
            replace_mode: 是否替换现有数据
            database_url: 目标数据库 URL（默认使用全局数据库）

        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid.uuid4())[:8]  # 使用短UUID
        db_url = database_url or config.DATABASE_URL
        self._task_database_urls[task_id] = db_url

        # 初始化数据库
        init_database(db_url, echo=False)
        create_all_tables()

        session = get_session()
        try:
            task = Task(
                task_id=task_id,
                task_type=TaskType.CSV_ANALYSIS,
                status=TaskStatus.PENDING,
                progress=0.0,
                current_step="任务已创建，等待处理",
                file_name=file_name,
                file_hash=file_hash,
                file_size=file_size,
                email=email,
                logs=[]
            )
            task.add_log("任务已创建")

            session.add(task)
            session.commit()

            logger.info(f"Task created: {task_id}")

        finally:
            session.close()

        # 提交到线程池执行
        future = self._executor.submit(
            self._run_csv_analysis,
            task_id,
            file_path,
            replace_mode,
            db_url,
        )
        self._tasks[task_id] = future

        return task_id

    def get_task(self, task_id: str, database_url: Optional[str] = None) -> Optional[dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，不存在返回 None
        """
        init_database(self._database_url_for_task(task_id, database_url), echo=False)
        session = get_session()

        try:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if task:
                return task.to_dict()
            return None
        finally:
            session.close()

    def cancel_task(self, task_id: str, database_url: Optional[str] = None) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        if task_id in self._tasks:
            future = self._tasks[task_id]
            if future.cancel():
                self._update_task_status(
                    task_id,
                    TaskStatus.CANCELLED,
                    database_url=database_url,
                )
                logger.info(f"Task cancelled: {task_id}")
                return True

        return False

    def _update_task_status(
        self,
        task_id: str,
        status: str,
        progress: float = None,
        step: str = None,
        result: dict = None,
        error: str = None,
        database_url: Optional[str] = None,
    ):
        """更新任务状态"""
        init_database(self._database_url_for_task(task_id, database_url), echo=False)
        session = get_session()

        try:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if not task:
                logger.error(f"Task not found: {task_id}")
                return

            task.status = status

            if progress is not None:
                task.progress = progress

            if step:
                task.current_step = step
                task.add_log(step)

            if result:
                task.result = result

            if error:
                task.error_message = error
                task.add_log(error, level="error")

            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.utcnow()

            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task.completed_at = datetime.utcnow()

            session.commit()

        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            session.rollback()
        finally:
            session.close()

    # 日志写入锁（SQLite 不支持并发写入）
    _log_lock = threading.Lock()

    def _add_log(
        self,
        task_id: str,
        message: str,
        level: str = "info",
        category: str = None,
        database_url: Optional[str] = None,
    ):
        """
        添加日志条目（不更新进度）

        Args:
            task_id: 任务ID
            message: 日志消息
            level: 日志级别 (info/success/warning/error)
            category: 日志分类 (import/match/score/system)
        """
        with self._log_lock:  # 串行化数据库写入
            init_database(self._database_url_for_task(task_id, database_url), echo=False)
            session = get_session()

            try:
                task = session.query(Task).filter(Task.task_id == task_id).first()
                if not task:
                    return

                log_entry = {
                    "time": datetime.utcnow().isoformat(),
                    "level": level,
                    "message": message,
                }
                if category:
                    log_entry["category"] = category

                if task.logs is None:
                    task.logs = []

                # 限制日志数量
                if len(task.logs) >= MAX_LOGS:
                    task.logs = task.logs[-(MAX_LOGS - 1):]

                task.logs = task.logs + [log_entry]  # 创建新列表触发SQLAlchemy更新
                session.commit()

            except Exception as e:
                logger.error(f"Failed to add log for task {task_id}: {e}")
                session.rollback()
            finally:
                session.close()

    def _database_url_for_task(
        self,
        task_id: str,
        database_url: Optional[str] = None,
    ) -> str:
        return database_url or self._task_database_urls.get(task_id) or config.DATABASE_URL

    def _run_csv_analysis(
        self,
        task_id: str,
        file_path: str,
        replace_mode: bool,
        database_url: str,
    ):
        """
        执行 CSV 分析任务（带详细日志）

        分为4个阶段：
        1. 数据导入 (0-40%)
        2. FIFO配对 (40-70%)
        3. 质量评分 (70-95%)
        4. 完成 (95-100%)
        """
        logger.info(f"Starting CSV analysis task: {task_id}")

        self._update_task_status(
            task_id,
            TaskStatus.RUNNING,
            progress=5.0,
            step="开始处理文件..."
        )
        self._add_log(task_id, "任务开始执行", "info", "system")

        try:
            # 导入必要的模块
            from src.importers.english_csv_parser import detect_csv_language
            from src.importers.incremental_importer import IncrementalImporter
            from src.matchers.fifo_matcher import FIFOMatcher
            from src.analyzers.quality_scorer import QualityScorer
            from src.models.trade import Trade
            from src.models.position import Position
            from sqlalchemy import text

            # ==================== 阶段 1: 数据导入 (0-40%) ====================
            self._update_task_status(
                task_id,
                TaskStatus.RUNNING,
                progress=10.0,
                step="正在检测文件格式..."
            )
            self._add_log(task_id, "正在检测 CSV 文件格式...", "info", "import")

            # 检测语言 - 添加更多步骤日志
            self._add_log(task_id, "读取文件头信息...", "info", "import")
            time.sleep(0.1)
            self._add_log(task_id, "分析字段名称...", "info", "import")
            time.sleep(0.1)

            language = detect_csv_language(file_path)
            logger.info(f"[{task_id}] Detected language: {language}")

            if language == 'unknown':
                self._add_log(task_id, "无法识别的文件格式", "error", "import")
                raise ValueError("不支持的CSV格式，请使用富途证券导出的CSV文件")

            # 格式识别成功
            format_name = "富途英文格式" if language == 'english' else "富途中文格式"
            self._add_log(task_id, f"✓ 检测到格式: {format_name}", "success", "import")
            time.sleep(0.05)

            # 替换模式：先清除所有旧数据
            if replace_mode:
                self._update_task_status(
                    task_id,
                    TaskStatus.RUNNING,
                    progress=15.0,
                    step="清除旧数据..."
                )
                self._add_log(task_id, "正在清除旧数据...", "info", "import")
                self._add_log(task_id, "清除交易记录表...", "info", "import")
                time.sleep(0.05)
                self._add_log(task_id, "清除持仓记录表...", "info", "import")
                time.sleep(0.05)
                self._clear_all_trading_data(database_url)
                self._add_log(task_id, "清除导入历史表...", "info", "import")
                time.sleep(0.05)
                self._add_log(task_id, "✓ 旧数据已清除", "success", "import")

            # 执行导入
            self._update_task_status(
                task_id,
                TaskStatus.RUNNING,
                progress=20.0,
                step="正在导入交易数据..."
            )
            self._add_log(task_id, "开始解析 CSV 文件...", "info", "import")
            self._add_log(task_id, "初始化解析器...", "info", "import")
            time.sleep(0.05)
            self._add_log(task_id, "读取文件内容...", "info", "import")
            time.sleep(0.05)

            importer = IncrementalImporter(
                file_path,
                dry_run=False,
                database_url=database_url,
            )

            self._add_log(task_id, "解析 CSV 列结构...", "info", "import")
            time.sleep(0.05)
            self._add_log(task_id, "映射字段到标准格式...", "info", "import")
            time.sleep(0.05)

            import_result = importer.run()

            # 添加导入详情日志 - 更详细
            self._add_log(task_id, f"文件解析完成: 共 {import_result.total_rows} 行数据", "info", "import")
            time.sleep(0.03)
            self._add_log(task_id, f"已成交订单: {import_result.completed_trades} 笔", "info", "import")
            time.sleep(0.03)

            if import_result.duplicates_skipped > 0:
                self._add_log(task_id, f"⚠ 跳过重复记录: {import_result.duplicates_skipped} 笔", "warning", "import")

            if import_result.errors > 0:
                self._add_log(task_id, f"⚠ 解析错误: {import_result.errors} 笔", "warning", "import")
                for err_msg in import_result.error_messages[:5]:
                    self._add_log(task_id, f"  └ {err_msg}", "warning", "import")
                    time.sleep(0.02)

            # 添加导入的每条交易详情 - 全部记录！
            self._log_all_imported_trades(task_id, database_url)

            self._update_task_status(
                task_id,
                TaskStatus.RUNNING,
                progress=40.0,
                step=f"已导入 {import_result.new_trades} 条交易记录"
            )
            self._add_log(
                task_id,
                f"✓ 导入完成: {import_result.new_trades} 条新交易已入库",
                "success",
                "import"
            )

            # ==================== 阶段 2: FIFO配对 (40-70%) ====================
            positions_matched = 0
            positions_scored = 0

            if import_result.new_trades > 0:
                self._update_task_status(
                    task_id,
                    TaskStatus.RUNNING,
                    progress=45.0,
                    step="正在进行持仓配对..."
                )
                self._add_log(task_id, "开始 FIFO 持仓配对算法...", "info", "match")
                time.sleep(0.05)
                self._add_log(task_id, "初始化配对引擎...", "info", "match")
                time.sleep(0.05)
                self._add_log(task_id, "按标的分组交易记录...", "info", "match")
                time.sleep(0.05)

                init_database(database_url, echo=False)
                session = get_session()

                try:
                    matcher = FIFOMatcher(session)

                    self._add_log(task_id, "排序买入/卖出队列...", "info", "match")
                    time.sleep(0.05)

                    match_result = matcher.match_all_trades()
                    positions_matched = match_result.get('positions_created', 0)
                    open_positions = match_result.get('open_positions', 0)
                    closed_positions = match_result.get('closed_positions', 0)

                    # 添加配对详情日志
                    self._add_log(task_id, f"处理交易数: {match_result.get('total_trades', 0)} 笔", "info", "match")
                    time.sleep(0.03)
                    self._add_log(task_id, f"涉及标的数: {match_result.get('symbols_processed', 0)} 个", "info", "match")
                    time.sleep(0.03)

                    # 记录每个持仓的配对结果 - 全部！
                    self._log_all_matched_positions(task_id, session)

                    self._add_log(
                        task_id,
                        f"✓ 配对完成: {positions_matched} 个持仓 (已平仓: {closed_positions}, 未平仓: {open_positions})",
                        "success",
                        "match"
                    )

                    self._update_task_status(
                        task_id,
                        TaskStatus.RUNNING,
                        progress=70.0,
                        step=f"已配对 {positions_matched} 个持仓"
                    )

                    # ==================== 阶段 3: 市场数据获取 (70-82%) ====================
                    self._update_task_status(
                        task_id,
                        TaskStatus.RUNNING,
                        progress=70.0,
                        step="正在获取市场数据..."
                    )
                    self._add_log(task_id, "开始获取市场数据...", "info", "data")

                    # 获取股票数据
                    market_data_result = self._fetch_market_data_with_logs(task_id, session)

                    # 根据结果显示不同的日志
                    symbols_fetched = market_data_result.get('symbols_fetched', 0)
                    symbols_analyzed = market_data_result.get('symbols_analyzed', 0)
                    failed_symbols = market_data_result.get('failed_symbols', [])

                    if symbols_fetched == 0 and symbols_analyzed > 0:
                        # 完全失败
                        self._add_log(
                            task_id,
                            f"⚠ 市场数据获取失败，将使用有限数据完成评分",
                            "warning",
                            "data"
                        )
                    elif len(failed_symbols) > 0:
                        # 部分失败
                        failed_count = len(failed_symbols)
                        self._add_log(
                            task_id,
                            f"⚠ 部分标的获取失败: {failed_count} 个 (已成功 {symbols_fetched} 个)",
                            "warning",
                            "data"
                        )
                    else:
                        # 全部成功
                        self._add_log(
                            task_id,
                            f"✓ 市场数据获取完成: {symbols_fetched} 个标的",
                            "success",
                            "data"
                        )

                    # ==================== 阶段 4: 质量评分 (82-95%) ====================
                    self._update_task_status(
                        task_id,
                        TaskStatus.RUNNING,
                        progress=85.0,
                        step="正在计算质量评分..."
                    )
                    self._add_log(task_id, "开始计算质量评分 (V2 九维度)...", "info", "score")
                    time.sleep(0.05)
                    self._add_log(task_id, "初始化评分引擎...", "info", "score")
                    time.sleep(0.05)
                    self._add_log(task_id, "加载评分规则配置...", "info", "score")
                    time.sleep(0.05)
                    self._add_log(task_id, "评分维度: 技术/行为/风控/执行/市场环境...", "info", "score")
                    time.sleep(0.05)

                    scorer = QualityScorer()
                    score_result = scorer.score_all_positions(session, update_db=True)
                    positions_scored = score_result.get('scored', 0)

                    # 记录每个持仓的评分 - 全部！
                    self._log_all_scored_positions(task_id, session)

                    session.commit()

                    self._add_log(
                        task_id,
                        f"✓ 评分完成: {positions_scored} 个持仓已评分",
                        "success",
                        "score"
                    )

                    self._update_task_status(
                        task_id,
                        TaskStatus.RUNNING,
                        progress=90.0,
                        step=f"已评分 {positions_scored} 个持仓"
                    )

                    # ==================== 阶段 4.5: 事件检测 (90-95%) ====================
                    self._update_task_status(
                        task_id,
                        TaskStatus.RUNNING,
                        progress=90.0,
                        step="正在检测市场事件..."
                    )
                    self._add_log(task_id, "开始检测市场事件 (财报/价格异常/成交量异常)...", "info", "events")
                    time.sleep(0.05)

                    events_detected = self._detect_events_with_logs(task_id, session)

                    self._update_task_status(
                        task_id,
                        TaskStatus.RUNNING,
                        progress=95.0,
                        step=f"已检测 {events_detected} 个事件"
                    )

                except Exception as e:
                    logger.error(f"[{task_id}] Matching/scoring error: {e}")
                    self._add_log(task_id, f"处理错误: {str(e)}", "error", "system")
                    session.rollback()
                    raise

                finally:
                    session.close()

            else:
                self._add_log(task_id, "无新交易，跳过配对和评分", "info", "system")

            # ==================== 阶段 5: 完成 (100%) ====================
            # 如果没有运行market_data_result，初始化为空
            if 'market_data_result' not in locals():
                market_data_result = {'symbols_fetched': 0, 'records_fetched': 0}
            if 'events_detected' not in locals():
                events_detected = 0

            result = {
                "language": language,
                "total_rows": import_result.total_rows,
                "completed_trades": import_result.completed_trades,
                "new_trades": import_result.new_trades,
                "duplicates_skipped": import_result.duplicates_skipped,
                "positions_matched": positions_matched,
                "positions_scored": positions_scored,
                "events_detected": events_detected,
                "symbols_fetched": market_data_result.get('symbols_fetched', 0),
                "market_data_records": market_data_result.get('records_fetched', 0),
                "errors": import_result.errors,
                "error_messages": import_result.error_messages[:10] if import_result.error_messages else [],
                "broker_name": getattr(import_result, 'broker_name', format_name),
            }

            self._add_log(task_id, "分析完成！", "success", "system")
            self._update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                progress=100.0,
                step="分析完成！",
                result=result
            )

            logger.info(f"[{task_id}] Task completed successfully")

            # 发送邮件通知
            self._send_completion_email(task_id, result, database_url)

        except Exception as e:
            logger.error(f"[{task_id}] Task failed: {e}", exc_info=True)
            self._add_log(task_id, f"任务失败: {str(e)}", "error", "system")
            self._update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=str(e)
            )

        finally:
            # 清理临时文件
            try:
                Path(file_path).unlink()
            except Exception:
                pass

    def _log_all_imported_trades(self, task_id: str, database_url: str):
        """记录所有导入的交易 - 每条都记录！"""
        from src.models.trade import Trade

        init_database(database_url, echo=False)
        session = get_session()

        try:
            # 获取所有交易（按日期排序）
            trades = session.query(Trade).order_by(Trade.trade_date.asc()).all()

            if not trades:
                return

            self._add_log(task_id, f"正在记录 {len(trades)} 条交易明细...", "info", "import")
            time.sleep(0.03)

            for i, trade in enumerate(trades, 1):
                direction = "买入" if trade.direction == "BUY" else "卖出"
                direction_icon = "📈" if trade.direction == "BUY" else "📉"

                # 格式化价格
                price_str = f"${trade.price:.2f}" if trade.price else "N/A"

                self._add_log(
                    task_id,
                    f"{direction_icon} #{i} {trade.symbol} {direction} {trade.quantity}股 @ {price_str}",
                    "info",
                    "import"
                )

                # 每5条加一点延迟，让动画更明显
                if i % 5 == 0:
                    time.sleep(0.02)

            self._add_log(task_id, f"✓ 已记录 {len(trades)} 条交易明细", "success", "import")

        except Exception as e:
            logger.warning(f"Failed to log trades: {e}")
        finally:
            session.close()

    def _log_all_matched_positions(self, task_id: str, session):
        """记录所有配对的持仓 - 每个都记录！"""
        from src.models.position import Position

        try:
            # 获取所有持仓
            positions = session.query(Position).order_by(Position.open_date.asc()).all()

            if not positions:
                return

            self._add_log(task_id, f"正在记录 {len(positions)} 个持仓配对结果...", "info", "match")
            time.sleep(0.03)

            for i, pos in enumerate(positions, 1):
                direction = "多头" if pos.direction == "LONG" else "空头"
                direction_icon = "🔺" if pos.direction == "LONG" else "🔻"
                status = "已平仓" if pos.status == "CLOSED" else "持仓中"
                status_icon = "✅" if pos.status == "CLOSED" else "⏳"

                # 盈亏信息
                if pos.realized_pnl is not None and pos.realized_pnl != 0:
                    pnl_icon = "💰" if pos.realized_pnl > 0 else "💸"
                    pnl_str = f"{pnl_icon} ${pos.realized_pnl:+,.2f}"
                    level = "success" if pos.realized_pnl > 0 else "warning"
                else:
                    pnl_str = ""
                    level = "info"

                self._add_log(
                    task_id,
                    f"{direction_icon} #{i} {pos.symbol} {direction} {pos.quantity}股 {status_icon}{status} {pnl_str}",
                    level,
                    "match"
                )

                # 每3个持仓加一点延迟
                if i % 3 == 0:
                    time.sleep(0.02)

            self._add_log(task_id, f"✓ 已记录 {len(positions)} 个持仓", "success", "match")

        except Exception as e:
            logger.warning(f"Failed to log positions: {e}")

    def _log_all_scored_positions(self, task_id: str, session):
        """记录所有持仓的评分 - 每个都记录！"""
        from src.models.position import Position

        try:
            # 获取所有已评分的持仓
            positions = session.query(Position).filter(
                Position.overall_score.isnot(None)
            ).order_by(Position.overall_score.desc()).all()

            if not positions:
                return

            self._add_log(task_id, f"正在记录 {len(positions)} 个持仓评分...", "info", "score")
            time.sleep(0.03)

            for i, pos in enumerate(positions, 1):
                grade = pos.score_grade or "?"
                score = pos.overall_score or 0

                # 根据等级选择图标
                grade_icons = {
                    'A': '🏆',
                    'B': '⭐',
                    'C': '📊',
                    'D': '⚠️',
                    'F': '❌'
                }
                icon = grade_icons.get(grade, '📋')

                # 根据等级选择日志级别
                if grade in ['A', 'B']:
                    level = "success"
                elif grade in ['D', 'F']:
                    level = "warning"
                else:
                    level = "info"

                self._add_log(
                    task_id,
                    f"{icon} #{i} {pos.symbol} → {grade}级 (分数: {score:.1f})",
                    level,
                    "score"
                )

                # 每3个评分加一点延迟
                if i % 3 == 0:
                    time.sleep(0.02)

            # 统计各等级数量
            grade_counts = {}
            for pos in positions:
                g = pos.score_grade or "?"
                grade_counts[g] = grade_counts.get(g, 0) + 1

            grade_summary = " | ".join([f"{g}级:{c}个" for g, c in sorted(grade_counts.items())])
            self._add_log(task_id, f"📊 评分分布: {grade_summary}", "info", "score")

        except Exception as e:
            logger.warning(f"Failed to log scores: {e}")

    def _fetch_market_data_with_logs(self, task_id: str, session) -> dict:
        """
        获取市场数据并记录日志（逐 symbol 日志）

        Args:
            task_id: 任务ID
            session: 数据库会话

        Returns:
            dict with fetch statistics
        """
        try:
            from src.data_sources.batch_fetcher import BatchFetcher
            from src.data_sources.cache_manager import CacheManager
            from src.models.trade import Trade

            self._add_log(task_id, "初始化数据获取引擎...", "info", "data")
            time.sleep(0.05)

            # 获取所有交易标的
            symbols = session.query(Trade.symbol).distinct().all()
            symbol_list = [s[0] for s in symbols]

            if not symbol_list:
                self._add_log(task_id, "⚠ 没有找到需要获取数据的标的", "warning", "data")
                return {'symbols_fetched': 0, 'records_fetched': 0}

            self._add_log(task_id, f"发现 {len(symbol_list)} 个需要获取数据的标的", "info", "data")
            time.sleep(0.03)

            # 显示部分标的
            sample_symbols = symbol_list[:5]
            self._add_log(task_id, f"标的预览: {', '.join(sample_symbols)}...", "info", "data")
            time.sleep(0.03)

            # 初始化 BatchFetcher
            self._add_log(task_id, "初始化数据路由器 (YFinance + AKShare)...", "info", "data")
            time.sleep(0.05)

            cache_manager = CacheManager(db_session=session)
            fetcher = BatchFetcher(
                cache_manager=cache_manager,
                use_router=True,
                max_workers=1,  # 串行模式避免线程挂起问题
                request_delay=0.1
            )

            self._add_log(task_id, "开始批量获取市场数据...", "info", "data")
            time.sleep(0.05)

            # 更新进度
            self._update_task_status(
                task_id,
                TaskStatus.RUNNING,
                progress=72.0,
                step="正在获取市场数据..."
            )

            # 创建逐 symbol 日志回调函数
            # 注意：使用线程安全的列表收集日志，完成后批量写入
            # 避免在多线程回调中直接写数据库导致 SQLite 死锁
            from threading import Lock
            fetch_count = [0]  # 使用列表以便在闭包中修改
            total_symbols = len(symbol_list)
            pending_logs = []  # 待写入的日志
            log_collect_lock = Lock()  # 日志收集锁
            last_progress_update = [0]  # 上次进度更新时的 count

            def on_symbol_fetched(symbol: str, success: bool, records: int, error_msg: str):
                """每个 symbol 获取完成后的回调 - 只收集日志，谨慎更新进度"""
                # 在锁内快速收集日志
                with log_collect_lock:
                    fetch_count[0] += 1
                    current_count = fetch_count[0]

                    if success:
                        pending_logs.append({
                            "message": f"✓ {symbol} 获取成功 ({records}条K线)",
                            "level": "success",
                            "category": "data"
                        })
                    else:
                        # 精简错误信息
                        short_error = error_msg[:50] if len(error_msg) > 50 else error_msg
                        pending_logs.append({
                            "message": f"✗ {symbol} 获取失败: {short_error}",
                            "level": "warning",
                            "category": "data"
                        })

                # 每20个标的更新一次进度（在锁外执行，减少持锁时间）
                # 使用 try/except 防止数据库错误阻塞主流程
                if current_count % 20 == 0 or current_count == total_symbols:
                    try:
                        progress = 72.0 + (current_count / total_symbols) * 10.0
                        self._update_task_status(
                            task_id,
                            TaskStatus.RUNNING,
                            progress=min(progress, 82.0),
                            step=f"正在获取市场数据 ({current_count}/{total_symbols})..."
                        )
                    except Exception as e:
                        # 进度更新失败不影响主流程
                        logger.warning(f"Progress update failed: {e}")

            # 执行批量获取（传入回调）
            print(f">>> 开始批量获取 {len(symbol_list)} 个标的...")
            stats = fetcher.fetch_required_data(session, progress_callback=on_symbol_fetched)
            print(f">>> 批量获取完成！成功: {stats.get('symbols_fetched', 0)}, 失败: {len(stats.get('failed_symbols', []))}")

            # 批量写入收集的日志
            print(f">>> 写入 {len(pending_logs)} 条日志...")
            for log_entry in pending_logs:
                self._add_log(task_id, log_entry["message"], log_entry["level"], log_entry["category"])

            # 记录汇总结果
            self._add_log(task_id, f"分析标的数: {stats.get('symbols_analyzed', 0)}", "info", "data")
            time.sleep(0.02)
            self._add_log(task_id, f"成功获取: {stats.get('symbols_fetched', 0)} 个标的", "info", "data")
            time.sleep(0.02)
            self._add_log(task_id, f"缓存命中: {stats.get('cached_symbols', 0)} 个标的", "info", "data")
            time.sleep(0.02)
            self._add_log(task_id, f"数据记录数: {stats.get('records_fetched', 0)}", "info", "data")
            time.sleep(0.02)

            duration = stats.get('duration_seconds', 0)
            self._add_log(task_id, f"获取耗时: {duration:.1f} 秒", "info", "data")

            # 更新进度
            self._update_task_status(
                task_id,
                TaskStatus.RUNNING,
                progress=82.0,
                step=f"已获取 {stats.get('symbols_fetched', 0)} 个标的的市场数据"
            )

            return stats

        except ModuleNotFoundError as e:
            logger.warning(f"[{task_id}] Market data dependency missing: {e}")
            self._add_log(
                task_id,
                f"⚠ 市场数据获取不可用: 缺少依赖 {e.name or str(e)}，将使用有限数据继续评分",
                "warning",
                "data",
            )
            return {
                'symbols_fetched': 0,
                'records_fetched': 0,
                'symbols_analyzed': 0,
                'failed_symbols': [],
                'error': str(e),
            }
        except Exception as e:
            logger.error(f"[{task_id}] Market data fetch error: {e}", exc_info=True)
            self._add_log(task_id, f"⚠ 市场数据获取异常: {str(e)}", "error", "data")
            # 不抛出异常，继续评分流程（返回详细信息供调用方判断）
            return {
                'symbols_fetched': 0,
                'records_fetched': 0,
                'symbols_analyzed': 0,
                'failed_symbols': [],
                'error': str(e)
            }

    def _clear_all_trading_data(self, database_url: str):
        """清除所有交易数据"""
        from sqlalchemy import text

        init_database(database_url, echo=False)
        session = get_session()

        tables_to_clear = ['positions', 'trades', 'import_history']

        try:
            for table in tables_to_clear:
                try:
                    session.execute(text(f"DELETE FROM {table}"))
                    logger.info(f"Cleared table: {table}")
                except Exception as e:
                    logger.warning(f"Failed to clear {table}: {e}")

            session.commit()
        finally:
            session.close()

    def _detect_events_with_logs(self, task_id: str, session) -> int:
        """
        为新配对的持仓检测市场事件

        Args:
            task_id: 任务ID
            session: 数据库会话

        Returns:
            检测到的事件数量
        """
        from src.analyzers.event_detector import EventDetector
        from src.models.position import Position, PositionStatus

        try:
            self._add_log(task_id, "初始化事件检测器...", "info", "events")
            time.sleep(0.03)

            detector = EventDetector(session)

            # 获取需要检测事件的持仓（已平仓且没有关联事件的）
            positions = session.query(Position).filter(
                Position.status == PositionStatus.CLOSED
            ).all()

            if not positions:
                self._add_log(task_id, "⚠ 没有需要检测事件的持仓", "warning", "events")
                return 0

            self._add_log(task_id, f"发现 {len(positions)} 个已平仓持仓需要检测事件", "info", "events")
            time.sleep(0.03)

            total_events = 0
            symbols_processed = set()

            for i, position in enumerate(positions, 1):
                try:
                    # 检测该持仓的事件
                    events = detector.detect_events_for_position(
                        position,
                        include_earnings=True,
                        include_anomalies=True
                    )

                    if events:
                        saved = detector.save_events(events, deduplicate=True)
                        total_events += saved

                        if saved > 0:
                            symbols_processed.add(position.symbol)
                            self._add_log(
                                task_id,
                                f"📊 {position.symbol}: 检测到 {saved} 个事件",
                                "info",
                                "events"
                            )

                    # 每10个持仓更新一次进度
                    if i % 10 == 0:
                        progress = 90.0 + (i / len(positions)) * 5.0
                        self._update_task_status(
                            task_id,
                            TaskStatus.RUNNING,
                            progress=min(progress, 95.0),
                            step=f"正在检测事件 ({i}/{len(positions)})..."
                        )

                except Exception as e:
                    # 单个持仓检测失败不影响其他
                    logger.warning(f"Event detection failed for position {position.id}: {e}")
                    continue

            # 汇总日志
            self._add_log(
                task_id,
                f"✓ 事件检测完成: {total_events} 个事件，涉及 {len(symbols_processed)} 个标的",
                "success",
                "events"
            )

            return total_events

        except Exception as e:
            logger.error(f"[{task_id}] Event detection error: {e}", exc_info=True)
            self._add_log(task_id, f"⚠ 事件检测异常: {str(e)}", "warning", "events")
            # 不抛出异常，事件检测失败不影响整体流程
            return 0

    def _send_completion_email(
        self,
        task_id: str,
        result: dict,
        database_url: Optional[str] = None,
    ):
        """发送完成通知邮件"""
        init_database(self._database_url_for_task(task_id, database_url), echo=False)
        session = get_session()

        try:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if not task or not task.email:
                return

            # 导入邮件服务并发送
            try:
                from backend.app.services.email_service import EmailService
                email_service = EmailService()
                email_service.send_analysis_complete(
                    to_email=task.email,
                    task_id=task_id,
                    file_name=task.file_name,
                    result=result
                )
                logger.info(f"[{task_id}] Email notification sent to {task.email}")
            except Exception as e:
                logger.error(f"[{task_id}] Failed to send email: {e}")

        finally:
            session.close()


# 全局任务管理器实例
task_manager = TaskManager()
