"""
配置文件模板

使用说明:
1. 复制此文件为 config.py
2. 填入您的真实API密钥
3. config.py会被.gitignore自动排除

注意: 此文件也用于 Docker/Railway 部署
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
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# Polygon.io (推荐 - 期权Greeks)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")

# Tiingo (可选 - 基本面数据)
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY", "")

# NewsAPI (可选 - 新闻数据)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Tavily (备用 - LLM友好的新闻搜索)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# IEX Cloud (可选)
IEX_CLOUD_TOKEN = os.getenv("IEX_CLOUD_TOKEN", "")

# ==================== LLM 配置 (AI Coach) ====================

# Anthropic Claude (推荐)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-3-haiku-20240307"

# OpenAI GPT (备选)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

# LLM 选择策略
LLM_PROVIDER = "anthropic" if ANTHROPIC_API_KEY else ("openai" if OPENAI_API_KEY else None)

# ==================== 数据源配置 ====================

USE_YFINANCE = True
USE_ALPHA_VANTAGE = bool(ALPHA_VANTAGE_API_KEY)
USE_POLYGON = bool(POLYGON_API_KEY)

DATA_SOURCE_PRIORITY = ["yfinance", "alpha_vantage", "polygon"]

# ==================== 时区配置 ====================

DEFAULT_TIMEZONE = "UTC"
US_MARKET_TIMEZONE = "America/New_York"
HK_MARKET_TIMEZONE = "Asia/Hong_Kong"
CN_MARKET_TIMEZONE = "Asia/Shanghai"

MARKET_TIMEZONES = {
    "美股": US_MARKET_TIMEZONE,
    "港股": HK_MARKET_TIMEZONE,
    "沪深": CN_MARKET_TIMEZONE,
}

# ==================== 缓存配置 ====================

CACHE_TTL_DAYS = 7
CACHE_TTL_SECONDS = CACHE_TTL_DAYS * 24 * 3600
MEMORY_CACHE_SIZE_MB = 100
AUTO_CLEAN_CACHE = True
CACHE_CLEAN_INTERVAL_HOURS = 24

# ==================== API限流配置 ====================

YFINANCE_RATE_LIMIT_CALLS = 2000
YFINANCE_RATE_LIMIT_PERIOD = 3600

ALPHA_VANTAGE_RATE_LIMIT_CALLS = 5
ALPHA_VANTAGE_RATE_LIMIT_PERIOD = 60

POLYGON_RATE_LIMIT_CALLS = 5
POLYGON_RATE_LIMIT_PERIOD = 60

MAX_RETRIES = 3
RETRY_WAIT_MIN = 2
RETRY_WAIT_MAX = 10

# ==================== 日志配置 ====================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "tradingcoach.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

# ==================== 数据库配置 ====================

SQLALCHEMY_ECHO = False
SQLALCHEMY_POOL_SIZE = 5
SQLALCHEMY_POOL_RECYCLE = 3600

# ==================== 数据处理配置 ====================

CSV_ENCODING = "utf-8-sig"
PRICE_DECIMAL_PLACES = 4
PERCENTAGE_DECIMAL_PLACES = 2
INDICATOR_LOOKBACK_DAYS = 200
USE_FIFO = True
HANDLE_PARTIAL_FILLS = True

# ==================== 质量评分配置 ====================

SCORE_WEIGHT_ENTRY = 0.30
SCORE_WEIGHT_EXIT = 0.25
SCORE_WEIGHT_TREND = 0.25
SCORE_WEIGHT_RISK = 0.20

# 新闻契合度评分配置
# 注意: DDGS 无法获取历史新闻，只能获取当前新闻，导致事件日期错误
# 对于历史数据分析，应禁用新闻搜索，只使用 price_anomaly/volume_anomaly/earnings
NEWS_SEARCH_ENABLED = False
NEWS_SEARCH_RANGE_DAYS = 3
NEWS_SEARCH_CACHE_TTL_DAYS = 7
SCORE_WEIGHT_NEWS_ALIGNMENT = 0.07

# 新闻搜索网络区域配置
NEWS_NETWORK_REGION = os.getenv("NEWS_NETWORK_REGION", "auto")
NEWS_PROVIDERS_INTERNATIONAL = ["ddgs", "tavily", "polygon"]
NEWS_PROVIDERS_CHINA = ["ddgs", "polygon"]

# RSI阈值
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# 布林带标准差
BBANDS_STD = 2.0

# ATR周期
ATR_PERIOD = 14

# ADX趋势强度阈值
ADX_WEAK_TREND = 15
ADX_MODERATE_TREND = 25
ADX_STRONG_TREND = 40

# Stochastic阈值
STOCH_OVERSOLD = 20
STOCH_OVERBOUGHT = 80

# BB Width阈值 (波动率压缩/扩张)
BB_WIDTH_LOW = 4.0
BB_WIDTH_HIGH = 10.0

# VIX阈值 (市场恐慌指数)
VIX_LOW = 15
VIX_HIGH = 25
VIX_EXTREME = 35

# ==================== 邮件配置 ====================

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@tradingcoach.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "TradingCoach")
EMAIL_ENABLED = bool(SMTP_USER and SMTP_PASSWORD)

# ==================== 任务配置 ====================

TASK_MAX_CONCURRENT = int(os.getenv("TASK_MAX_CONCURRENT", "3"))
TASK_TIMEOUT_SECONDS = int(os.getenv("TASK_TIMEOUT_SECONDS", "600"))

# ==================== 调试配置 ====================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENABLE_PROFILING = False
VERBOSE_ERRORS = DEBUG

# ==================== 环境变量优先级 ====================

try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


# ==================== 配置验证 ====================

def validate_config():
    """验证配置是否正确"""
    errors = []

    if USE_ALPHA_VANTAGE and not ALPHA_VANTAGE_API_KEY:
        errors.append("Alpha Vantage API key is required but not set")

    for directory in [DATA_DIR, CACHE_DIR, LOG_DIR]:
        if not os.access(directory, os.W_OK):
            errors.append(f"No write permission for directory: {directory}")

    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))

    return True


if __name__ == "__main__":
    try:
        validate_config()
        print("✓ Configuration validated successfully")
        print(f"  Database: {DATABASE_PATH}")
        print(f"  Cache dir: {CACHE_DIR}")
        print(f"  Log dir: {LOG_DIR}")
        print(f"  Alpha Vantage: {'Enabled' if USE_ALPHA_VANTAGE else 'Disabled'}")
        print(f"  Polygon.io: {'Enabled' if USE_POLYGON else 'Disabled'}")
    except ValueError as e:
        print(f"✗ Configuration validation failed:\n{e}")
