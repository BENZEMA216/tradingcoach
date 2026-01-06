"""
配置文件模板

使用说明:
1. 复制此文件为 config.py
2. 填入您的真实API密钥
3. config.py会被.gitignore自动排除
"""

import os
from pathlib import Path

# ==================== 路径配置 ====================

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = PROJECT_ROOT / "cache"
LOG_DIR = PROJECT_ROOT / "logs"
ORIGINAL_DATA_DIR = PROJECT_ROOT / "original_data"

DATABASE_PATH = DATA_DIR / "tradingcoach.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ==================== API Keys配置 ====================

# Alpha Vantage (必需)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "YOUR_API_KEY_HERE")

# Polygon.io (推荐 - 期权Greeks)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "YOUR_API_KEY_HERE")

# Tiingo (可选 - 基本面数据)
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY", "YOUR_API_KEY_HERE")

# NewsAPI (可选 - 新闻数据)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "YOUR_API_KEY_HERE")

# IEX Cloud (可选)
IEX_CLOUD_TOKEN = os.getenv("IEX_CLOUD_TOKEN", "")

# ==================== 数据源配置 ====================

USE_YFINANCE = True
USE_ALPHA_VANTAGE = bool(ALPHA_VANTAGE_API_KEY)
USE_POLYGON = bool(POLYGON_API_KEY)

DATA_SOURCE_PRIORITY = ["yfinance", "alpha_vantage", "polygon"]

# ==================== 其他配置 ====================
# (保持与config.py相同的其他配置...)

DEFAULT_TIMEZONE = "UTC"
US_MARKET_TIMEZONE = "America/New_York"
HK_MARKET_TIMEZONE = "Asia/Hong_Kong"
CN_MARKET_TIMEZONE = "Asia/Shanghai"

CACHE_TTL_DAYS = 7
MEMORY_CACHE_SIZE_MB = 100
AUTO_CLEAN_CACHE = True
CACHE_CLEAN_INTERVAL_HOURS = 24

YFINANCE_RATE_LIMIT_CALLS = 2000
YFINANCE_RATE_LIMIT_PERIOD = 3600

ALPHA_VANTAGE_RATE_LIMIT_CALLS = 5
ALPHA_VANTAGE_RATE_LIMIT_PERIOD = 60

POLYGON_RATE_LIMIT_CALLS = 5
POLYGON_RATE_LIMIT_PERIOD = 60

MAX_RETRIES = 3
RETRY_WAIT_MIN = 2
RETRY_WAIT_MAX = 10

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "tradingcoach.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

SQLALCHEMY_ECHO = False
SQLALCHEMY_POOL_SIZE = 5
SQLALCHEMY_POOL_RECYCLE = 3600

CSV_ENCODING = "utf-8-sig"
PRICE_DECIMAL_PLACES = 4
PERCENTAGE_DECIMAL_PLACES = 2
INDICATOR_LOOKBACK_DAYS = 200
USE_FIFO = True
HANDLE_PARTIAL_FILLS = True

SCORE_WEIGHT_ENTRY = 0.30
SCORE_WEIGHT_EXIT = 0.25
SCORE_WEIGHT_TREND = 0.25
SCORE_WEIGHT_RISK = 0.20

RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
BBANDS_STD = 2.0
ATR_PERIOD = 14
ADX_STRONG_TREND = 25

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENABLE_PROFILING = False
VERBOSE_ERRORS = DEBUG

# 尝试从.env文件加载环境变量
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass
