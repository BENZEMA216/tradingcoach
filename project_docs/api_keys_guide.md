# API Keys 申请和配置指南

## 概述

本文档列出交易复盘系统所需的所有API服务及其申请方法。

## 需要申请的API Keys

### 1. Alpha Vantage（必需 - P1）

**用途**: 市场数据备用源，美股/港股历史OHLCV数据

**免费额度**:
- 500次请求/天
- 5次请求/分钟
- 完整历史数据

**申请步骤**:
1. 访问: https://www.alphavantage.co/support/#api-key
2. 填写邮箱地址
3. 立即获得API Key（无需等待）

**配置示例**:
```python
ALPHA_VANTAGE_API_KEY = "YOUR_KEY_HERE"
```

**优先级**: ⭐⭐⭐⭐⭐ 必需申请
**预计时间**: 2分钟

---

### 2. Polygon.io（推荐 - P2）

**用途**:
- 实时市场数据
- 期权Greeks数据（Delta, Gamma, Theta, Vega）
- 分钟级历史数据

**免费额度**:
- 5次请求/分钟
- 2年历史数据
- 实时股票报价（15分钟延迟）

**申请步骤**:
1. 访问: https://polygon.io/dashboard/signup
2. 使用邮箱注册账号
3. 在Dashboard中找到API Key

**配置示例**:
```python
POLYGON_API_KEY = "YOUR_KEY_HERE"
```

**优先级**: ⭐⭐⭐⭐ 推荐申请（期权Greeks需要）
**预计时间**: 3分钟

**付费计划**（可选）:
- Starter: $29/月 - 无限请求，实时数据
- Developer: $99/月 - 期权链完整数据

---

### 3. Tiingo（可选 - P3）

**用途**:
- 基本面数据（PE比率、市值、财务指标）
- 新闻数据
- 加密货币数据

**免费额度**:
- 500次请求/小时
- 每日新闻更新
- 50个独特ticker/月

**申请步骤**:
1. 访问: https://api.tiingo.com/account/signup
2. 注册账号
3. 在Account Settings中获取API Token

**配置示例**:
```python
TIINGO_API_KEY = "YOUR_KEY_HERE"
```

**优先级**: ⭐⭐⭐ 可选（基本面分析增强）
**预计时间**: 3分钟

---

### 4. NewsAPI（未来 - P4）

**用途**:
- 新闻情绪分析
- 事件时间线标记
- 财经新闻聚合

**免费额度**:
- 100次请求/天
- 历史数据1个月
- 80,000+新闻源

**申请步骤**:
1. 访问: https://newsapi.org/register
2. 填写基本信息
3. 邮箱验证后获得API Key

**配置示例**:
```python
NEWS_API_KEY = "YOUR_KEY_HERE"
```

**优先级**: ⭐⭐ 未来迭代使用
**预计时间**: 2分钟

---

### 5. IEX Cloud（可选 - P3）

**用途**:
- 实时股票报价
- 公司基本面数据
- 财务报表数据

**免费额度**:
- 50,000消息/月
- 实时股票报价
- 公司信息

**申请步骤**:
1. 访问: https://iexcloud.io/cloud-login#/register
2. 选择Free Plan
3. 在Console中获取Publishable Token和Secret Token

**配置示例**:
```python
IEX_CLOUD_TOKEN = "pk_YOUR_PUBLISHABLE_TOKEN"
IEX_CLOUD_SECRET = "sk_YOUR_SECRET_TOKEN"
```

**优先级**: ⭐⭐ 可选
**预计时间**: 3分钟

---

## 无需API Key的服务

### yfinance（主数据源）

**说明**:
- 完全免费，无需API Key
- 非官方Yahoo Finance API
- 覆盖全球股票、期权、ETF、加密货币

**限流**:
- 约2000次请求/小时
- 建议使用缓存机制

**使用方式**:
```python
import yfinance as yf
ticker = yf.Ticker("AAPL")
df = ticker.history(period="1y")
```

---

## 配置文件设置

### 方式1: config.py（推荐）

创建 `config.py` 文件:

```python
"""
配置文件
注意: 不要提交此文件到Git，请使用config_local.py
"""

# 数据库配置
DATABASE_PATH = "data/tradingcoach.db"
CACHE_DIR = "cache"

# API Keys配置
ALPHA_VANTAGE_API_KEY = "YOUR_KEY_HERE"  # 必需
POLYGON_API_KEY = "YOUR_KEY_HERE"        # 推荐
TIINGO_API_KEY = ""                      # 可选
NEWS_API_KEY = ""                        # 可选
IEX_CLOUD_TOKEN = ""                     # 可选

# 数据源优先级
USE_YFINANCE = True  # 主数据源
USE_ALPHA_VANTAGE = True  # 备用数据源（当yfinance失败时）
USE_POLYGON = False  # 仅用于期权Greeks

# 时区配置
DEFAULT_TIMEZONE = "UTC"
US_MARKET_TIMEZONE = "America/New_York"
HK_MARKET_TIMEZONE = "Asia/Hong_Kong"

# 缓存配置
CACHE_TTL_DAYS = 7  # 磁盘缓存有效期
MEMORY_CACHE_SIZE_MB = 100  # 内存缓存大小限制

# API限流配置
YFINANCE_RATE_LIMIT = 2000  # 请求/小时
ALPHA_VANTAGE_RATE_LIMIT = 5  # 请求/分钟
POLYGON_RATE_LIMIT = 5  # 请求/分钟（免费版）

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "logs/tradingcoach.log"
```

### 方式2: .env文件（替代方案）

创建 `.env` 文件:

```bash
# API Keys
ALPHA_VANTAGE_API_KEY=YOUR_KEY_HERE
POLYGON_API_KEY=YOUR_KEY_HERE
TIINGO_API_KEY=YOUR_KEY_HERE
NEWS_API_KEY=YOUR_KEY_HERE

# Database
DATABASE_PATH=data/tradingcoach.db
```

使用python-dotenv加载:
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
```

---

## .gitignore配置

**重要**: 确保不要将API Keys提交到Git仓库！

在 `.gitignore` 中添加:

```gitignore
# 配置文件（包含API Keys）
config.py
config_local.py
.env
.env.local

# API Keys文本文件
api_keys.txt
*.key

# 数据库和缓存
data/*.db
data/*.sqlite
cache/
*.pkl

# 日志
logs/
*.log
```

---

## 申请清单和时间规划

### 立即申请（必需）
- [ ] Alpha Vantage - 2分钟

### 推荐申请（增强功能）
- [ ] Polygon.io - 3分钟

### 可选申请（未来迭代）
- [ ] Tiingo - 3分钟
- [ ] NewsAPI - 2分钟
- [ ] IEX Cloud - 3分钟

**总耗时**: 必需2分钟，全部申请13分钟

---

## API使用优先级策略

### 市场数据获取策略

```python
def get_market_data(symbol, start_date, end_date):
    """
    数据获取优先级:
    1. yfinance (免费，无限制)
    2. Alpha Vantage (备用，限流5次/分钟)
    3. Polygon.io (付费，仅在需要分钟级数据时使用)
    """

    # 第一选择: yfinance
    try:
        data = fetch_from_yfinance(symbol, start_date, end_date)
        if data is not None:
            return data
    except Exception as e:
        logger.warning(f"yfinance failed: {e}")

    # 备用: Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        try:
            data = fetch_from_alpha_vantage(symbol)
            return data
        except Exception as e:
            logger.error(f"Alpha Vantage failed: {e}")

    # 最后选择: Polygon.io
    if POLYGON_API_KEY:
        return fetch_from_polygon(symbol, start_date, end_date)

    raise DataSourceError("All data sources failed")
```

### 期权Greeks获取策略

```python
def get_option_greeks(option_symbol, date):
    """
    期权Greeks优先级:
    1. Polygon.io (最准确，有完整Greeks)
    2. yfinance (免费，但Greeks不完整)
    3. 本地计算 (Black-Scholes模型估算)
    """

    if POLYGON_API_KEY:
        return fetch_greeks_from_polygon(option_symbol, date)

    # 从yfinance获取部分数据 + 本地计算
    return calculate_greeks_local(option_symbol, date)
```

---

## 成本分析

### MVP阶段（免费方案）

| 服务 | 成本 | 限制 |
|------|------|------|
| yfinance | $0 | ~2000次/小时 |
| Alpha Vantage | $0 | 5次/分钟 |
| Polygon.io | $0 | 5次/分钟，15分钟延迟 |
| **总计** | **$0/月** | 适合个人使用 |

### 扩展阶段（付费方案）

| 服务 | 成本 | 收益 |
|------|------|------|
| yfinance | $0 | 主数据源 |
| Alpha Vantage Premium | $50/月 | 500次/分钟 |
| Polygon.io Starter | $29/月 | 实时数据，无限请求 |
| Tiingo Power | $30/月 | 新闻+基本面 |
| **总计** | **$109/月** | 专业级数据质量 |

---

## 故障排查

### 常见问题

**Q1: Alpha Vantage返回"Thank you for using Alpha Vantage"错误**
- 原因: 超过限流（5次/分钟）
- 解决: 使用`time.sleep(12)`间隔请求，或启用缓存

**Q2: yfinance无法获取港股数据**
- 原因: symbol格式错误
- 解决: 港股需要添加后缀，如 `1810.HK`

**Q3: Polygon.io返回403错误**
- 原因: API Key未激活或超出免费额度
- 解决: 检查Dashboard中的使用情况

**Q4: 期权Greeks数据缺失**
- 原因: 免费API通常不提供完整Greeks
- 解决: 升级到Polygon.io付费版，或使用Black-Scholes本地计算

---

## 下一步

1. ✅ 申请必需的API Keys（Alpha Vantage）
2. ✅ 创建 `config.py` 并配置API Keys
3. ✅ 测试API连接
4. ✅ 实现数据源客户端代码

---

**文档版本**: v1.0
**创建日期**: 2025-11-16
**最后更新**: 2025-11-16
