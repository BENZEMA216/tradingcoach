"""
配置模板文件

使用方法:
1. 复制此文件为 config.py
   cp config_template.py config.py

2. 在 config.py 中填入你的API Keys

3. config.py 已被.gitignore排除，不会被提交到Git
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
# 请在config.py中填入实际的API Keys

ALPHA_VANTAGE_API_KEY = ""  # 在此填入Alpha Vantage API Key
POLYGON_API_KEY = ""  # 可选
TIINGO_API_KEY = ""  # 可选
NEWS_API_KEY = ""  # 可选
IEX_CLOUD_TOKEN = ""  # 可选


# ==================== 其他配置 ====================
# 以下配置通常不需要修改

USE_YFINANCE = True
USE_ALPHA_VANTAGE = bool(ALPHA_VANTAGE_API_KEY)
USE_POLYGON = bool(POLYGON_API_KEY)

DEFAULT_TIMEZONE = "UTC"
US_MARKET_TIMEZONE = "America/New_York"
HK_MARKET_TIMEZONE = "Asia/Hong_Kong"
CN_MARKET_TIMEZONE = "Asia/Shanghai"

CACHE_TTL_DAYS = 7
MEMORY_CACHE_SIZE_MB = 100

LOG_LEVEL = "INFO"
LOG_FILE = LOG_DIR / "tradingcoach.log"

# 更多配置请参考 config.py 完整版本
