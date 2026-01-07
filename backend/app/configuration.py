from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Trading Coach"
    APP_VERSION: str = "0.5.0"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:8501",
        "http://localhost:8502",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:8502",
    ]
    DATABASE_URL: str = "sqlite:////Users/bytedance/trading/tradingcoach/data/tradingcoach.db"
    DEBUG: bool = False

    class Config:
        case_sensitive = True

settings = Settings()
