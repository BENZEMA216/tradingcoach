import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

# 计算本地默认数据库路径
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_LOCAL_DB_PATH = _PROJECT_ROOT / "data" / "tradingcoach.db"
_DEFAULT_DB_URL = f"sqlite:///{_LOCAL_DB_PATH}"

class Settings(BaseSettings):
    APP_NAME: str = "Trading Coach"
    APP_VERSION: str = "0.5.0"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:8501",
        "http://localhost:8502",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:8502",
        "*",  # 允许所有来源（Railway 部署需要）
    ]
    # 从环境变量读取，默认使用本地项目路径
    DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)
    DEBUG: bool = False

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars like API keys

settings = Settings()
