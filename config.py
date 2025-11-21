"""
配置文件

注意:
- 请勿将此文件提交到Git（已在.gitignore中排除）
- API Keys请在本地修改
- 使用config_template.py作为模板
"""

import os
from pathlib import Path

# ==================== 路径配置 ====================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = PROJECT_ROOT / "cache"
LOG_DIR = PROJECT_ROOT / "logs"
ORIGINAL_DATA_DIR = PROJECT_ROOT / "original_data"

# 数据库路径
DATABASE_PATH = DATA_DIR / "tradingcoach.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


# ==================== API Keys配置 ====================

# Alpha Vantage (必需)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "AASBPCXAMYZWZAIL")

# Polygon.io (推荐 - 期权Greeks)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "VzesuPYgrbf1vrfpfpphbuca5wwoJ92g")

# Tiingo (可选 - 基本面数据)
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY", "1eefe51e4f11ec58626799e90e809abcd4598f1c")

# NewsAPI (可选 - 新闻数据)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "b898425538174d088544fee3691e626b")

# IEX Cloud (可选)
IEX_CLOUD_TOKEN = os.getenv("IEX_CLOUD_TOKEN", "")


# ==================== 数据源配置 ====================

# 数据源优先级
USE_YFINANCE = True  # 主数据源
USE_ALPHA_VANTAGE = bool(ALPHA_VANTAGE_API_KEY)  # 备用数据源
USE_POLYGON = bool(POLYGON_API_KEY)  # 期权Greeks

# 数据源切换策略
DATA_SOURCE_PRIORITY = [
    "yfinance",  # 优先使用yfinance
    "alpha_vantage",  # yfinance失败时使用
    "polygon"  # 最后选择（付费）
]


# ==================== 时区配置 ====================

# 默认时区（数据库存储）
DEFAULT_TIMEZONE = "UTC"

# 市场时区
US_MARKET_TIMEZONE = "America/New_York"  # 美东时间
HK_MARKET_TIMEZONE = "Asia/Hong_Kong"    # 香港时间
CN_MARKET_TIMEZONE = "Asia/Shanghai"     # 中国时间

# 时区映射
MARKET_TIMEZONES = {
    "美股": US_MARKET_TIMEZONE,
    "港股": HK_MARKET_TIMEZONE,
    "沪深": CN_MARKET_TIMEZONE,
}


# ==================== 缓存配置 ====================

# 缓存有效期
CACHE_TTL_DAYS = 7  # 磁盘缓存有效期（天）
CACHE_TTL_SECONDS = CACHE_TTL_DAYS * 24 * 3600

# 内存缓存大小限制
MEMORY_CACHE_SIZE_MB = 100

# 缓存清理策略
AUTO_CLEAN_CACHE = True  # 自动清理过期缓存
CACHE_CLEAN_INTERVAL_HOURS = 24  # 清理间隔（小时）


# ==================== API限流配置 ====================

# yfinance限流（非官方限制，保守估计）
YFINANCE_RATE_LIMIT_CALLS = 2000
YFINANCE_RATE_LIMIT_PERIOD = 3600  # 秒

# Alpha Vantage限流
ALPHA_VANTAGE_RATE_LIMIT_CALLS = 5
ALPHA_VANTAGE_RATE_LIMIT_PERIOD = 60  # 秒

# Polygon.io限流（免费版）
POLYGON_RATE_LIMIT_CALLS = 5
POLYGON_RATE_LIMIT_PERIOD = 60  # 秒

# 重试配置
MAX_RETRIES = 3  # 最大重试次数
RETRY_WAIT_MIN = 2  # 重试最小等待时间（秒）
RETRY_WAIT_MAX = 10  # 重试最大等待时间（秒）


# ==================== 日志配置 ====================

# 日志级别
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 日志文件
LOG_FILE = LOG_DIR / "tradingcoach.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志文件大小限制
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5  # 保留5个备份


# ==================== 数据库配置 ====================

# SQLAlchemy配置
SQLALCHEMY_ECHO = False  # 是否打印SQL语句（调试时设为True）
SQLALCHEMY_POOL_SIZE = 5
SQLALCHEMY_POOL_RECYCLE = 3600  # 连接回收时间（秒）


# ==================== 数据处理配置 ====================

# CSV编码
CSV_ENCODING = "utf-8-sig"  # UTF-8 with BOM

# 数据精度
PRICE_DECIMAL_PLACES = 4  # 价格小数位数
PERCENTAGE_DECIMAL_PLACES = 2  # 百分比小数位数

# 技术指标计算参数
INDICATOR_LOOKBACK_DAYS = 200  # 计算技术指标需要的历史天数（MA200需要）

# 交易配对
USE_FIFO = True  # 使用先进先出算法
HANDLE_PARTIAL_FILLS = True  # 处理部分成交


# ==================== 质量评分配置 ====================

# 评分权重
SCORE_WEIGHT_ENTRY = 0.30  # 入场质量权重
SCORE_WEIGHT_EXIT = 0.25   # 出场质量权重
SCORE_WEIGHT_TREND = 0.25  # 趋势质量权重
SCORE_WEIGHT_RISK = 0.20   # 风险管理权重

# RSI阈值
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# 布林带标准差
BBANDS_STD = 2.0

# ATR周期
ATR_PERIOD = 14

# ADX阈值
ADX_STRONG_TREND = 25


# ==================== 调试配置 ====================

# 调试模式
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# 性能分析
ENABLE_PROFILING = False

# 打印详细错误信息
VERBOSE_ERRORS = DEBUG


# ==================== 环境变量优先级 ====================

# 尝试从.env文件加载环境变量
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
except ImportError:
    pass


# ==================== 配置验证 ====================

def validate_config():
    """验证配置是否正确"""
    errors = []

    # 检查必需的API Key
    if USE_ALPHA_VANTAGE and not ALPHA_VANTAGE_API_KEY:
        errors.append("Alpha Vantage API key is required but not set")

    # 检查目录权限
    for directory in [DATA_DIR, CACHE_DIR, LOG_DIR]:
        if not os.access(directory, os.W_OK):
            errors.append(f"No write permission for directory: {directory}")

    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))

    return True


if __name__ == "__main__":
    # 配置验证
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
