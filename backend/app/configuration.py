"""
后端配置

input: 环境变量 / .env
output: settings 单例，被 main.py / database.py / endpoints 使用
pos: 后端配置层 - 通过 pydantic-settings 解析

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

# 计算本地默认数据库路径
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_LOCAL_DB_PATH = _PROJECT_ROOT / "data" / "tradingcoach.db"
_DEFAULT_DB_URL = f"sqlite:///{_LOCAL_DB_PATH}"

# 默认开发环境允许的来源
_DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:8501",
    "http://localhost:8502",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8501",
    "http://127.0.0.1:8502",
]


def _parse_cors_env() -> List[str]:
    """从 CORS_ORIGINS 环境变量解析逗号分隔的来源列表。

    生产部署（Railway/Vercel）通过环境变量传入实际域名，例如：
        CORS_ORIGINS=https://tradingcoach.vercel.app,https://tc-staging.vercel.app
    """
    raw = os.getenv("CORS_ORIGINS", "")
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


class Settings(BaseSettings):
    APP_NAME: str = "Trading Coach"
    APP_VERSION: str = "0.5.0"
    API_V1_PREFIX: str = "/api/v1"

    # 显式来源列表 — 不再使用 "*"。
    # 任何 "*" 与 allow_credentials=True 同用都是 CORS 规范禁止的组合，
    # 并且会让任意网站调用 DELETE /system/data/reset 等敏感端点。
    CORS_ORIGINS: List[str] = _DEFAULT_ALLOWED_ORIGINS + _parse_cors_env()

    # 从环境变量读取，默认使用本地项目路径
    DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)
    DEBUG: bool = False

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars like API keys


settings = Settings()
