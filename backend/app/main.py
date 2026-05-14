"""
FastAPI Application Entry Point

input: config.py配置, api/v1/router路由
output: FastAPI实例, CORS中间件, API文档
pos: 后端服务入口 - 创建应用实例，挂载路由和中间件

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .configuration import settings
from .api.v1.router import api_router

# ==================== 日志配置 ====================
# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "backend.log"

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 配置根日志器
def setup_logging():
    """配置日志系统"""
    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 控制台处理器 (INFO级别)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # 文件处理器 (DEBUG级别, 轮转)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info(f"日志系统已初始化，日志文件: {LOG_FILE}")

# 初始化日志
setup_logging()

# Create FastAPI app
# 生产环境 (DEBUG=false) 关闭交互式 Swagger / Redoc UI — 这些 UI 暴露在
# 公网相当于给攻击者递地图。openapi.json 保留（SDK 生成 / 内部测试需要），
# 想完全锁死的话再单独关。
_is_debug = settings.DEBUG
_docs_url = f"{settings.API_V1_PREFIX}/docs" if _is_debug else None
_redoc_url = f"{settings.API_V1_PREFIX}/redoc" if _is_debug else None

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# CORS middleware
# 注意：allow_origins 不能包含 "*" 同时 allow_credentials=True
# （浏览器会拒绝此组合）。生产环境通过 CORS_ORIGINS 环境变量传入真实域名。
_cors_origins = [o for o in settings.CORS_ORIGINS if o != "*"]
if "*" in settings.CORS_ORIGINS:
    logging.getLogger(__name__).warning(
        "CORS wildcard '*' was supplied — stripped because combining it with "
        "allow_credentials=True is unsafe (lets any site call sensitive "
        "endpoints with the user's cookies). Set CORS_ORIGINS env to your real "
        "frontend origin instead, e.g. CORS_ORIGINS=https://tradingcoach.vercel.app"
    )
# 生产环境若只剩 localhost，Vercel 等真实前端会被 CORS 挡住 → 大声提示
if not _is_debug and not any("vercel.app" in o or "railway.app" in o or "https://" in o for o in _cors_origins):
    logging.getLogger(__name__).warning(
        "Running with DEBUG=false but CORS_ORIGINS contains no https:// origin. "
        "If this is production, set CORS_ORIGINS env to your real frontend URL."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
