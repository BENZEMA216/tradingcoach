"""
后端配置

input: 环境变量 / .env
output: settings 单例，被 main.py / database.py / endpoints 使用
pos: 后端配置层 - 通过 pydantic-settings 解析

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# 计算本地默认数据库路径
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_LOCAL_DB_PATH = _PROJECT_ROOT / "data" / "tradingcoach.db"
_DEFAULT_DB_URL = f"sqlite:///{_LOCAL_DB_PATH}"

# 默认允许的来源：本地开发 + 已知的 Vercel production 域名。
# 任何额外环境（staging、预览部署、新域名等）通过 CORS_ORIGINS env 追加。
# 这样部署 Railway 时哪怕忘了配 CORS_ORIGINS，主前端也不会被 CORS 挡掉。
_DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:8501",
    "http://localhost:8502",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8501",
    "http://127.0.0.1:8502",
    "https://tradingcoach.vercel.app",
]


class Settings(BaseSettings):
    APP_NAME: str = "Trading Coach"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # 接受逗号分隔字符串，避免 pydantic 把 env 值当 JSON 数组解析。
    # 生产部署示例：CORS_ORIGINS=https://tradingcoach.vercel.app,https://...
    # 不要使用 "*"（与 allow_credentials=True 同用会让任意网站借 cookie
    # 调用敏感端点，例如 DELETE /system/data/reset）。
    CORS_ORIGINS_RAW: str = Field(default="", alias="CORS_ORIGINS")

    # 从环境变量读取，默认使用本地项目路径
    DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """返回合并后的来源白名单：默认 localhost + env 传入的真实域名。"""
        env_origins = [
            o.strip() for o in self.CORS_ORIGINS_RAW.split(",") if o.strip()
        ]
        return _DEFAULT_ALLOWED_ORIGINS + env_origins


settings = Settings()
