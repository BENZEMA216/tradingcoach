# news_adapters

一旦我所属的文件夹有所变化，请更新我

## 架构说明

新闻搜索适配器模块，提供统一接口对接多个新闻搜索后端。**默认使用 DDGS（免费无需配置）**，根据网络环境自动选择最佳提供商。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 适配器工厂、网络检测、配置加载 |
| `base.py` | 基类 | NewsAdapter 抽象基类、MockNewsAdapter |
| `ddgs_adapter.py` | DDGS 适配器 | **默认首选**，免费多引擎搜索 |
| `tavily_adapter.py` | Tavily 适配器 | 备选，LLM 友好 |
| `polygon_adapter.py` | Polygon 适配器 | 专业金融新闻 |

## 提供商对比

| 提供商 | API Key | 价格 | 引擎支持 | 推荐度 |
|-------|---------|------|---------|--------|
| **DDGS** | 不需要 | 免费 | DuckDuckGo/Bing/Yahoo | ⭐⭐⭐⭐⭐ |
| Tavily | 需要 | 1000次/月免费 | 自有 | ⭐⭐⭐⭐ |
| Polygon | 需要 | 5次/分钟 | 金融专用 | ⭐⭐⭐ |

## 网络区域支持

| 网络环境 | 默认提供商 | 优先级 |
|---------|-----------|--------|
| **国际网络** | DDGS | ddgs > tavily > polygon |
| **中国网络** | DDGS | ddgs > polygon |

## 快速开始

### 零配置使用（推荐）

DDGS 无需任何 API Key，开箱即用：

```bash
pip install -U ddgs
```

```python
from src.analyzers.news_adapters import DDGSAdapter

# 直接使用，无需配置
adapter = DDGSAdapter()
results = adapter.search("NVDA stock news")
```

### 自动获取适配器

```python
from src.analyzers.news_adapters import get_adapter_from_config

# 从配置自动选择最佳适配器（默认使用 DDGS）
adapter = get_adapter_from_config()
if adapter:
    results = adapter.search("NVDA stock news")
```

### 注入到 NewsSearcher

```python
from src.analyzers.news_adapters import create_search_func_from_config
from src.analyzers.news_searcher import NewsSearcher

# 创建搜索函数
search_func = create_search_func_from_config()

# 注入到 NewsSearcher
searcher = NewsSearcher(search_func=search_func)
result = searcher.search("NVDA", trade_date)
```

## 配置选项 (config.py)

```python
# 网络区域设置
NEWS_NETWORK_REGION = "auto"  # auto / international / china

# 提供商优先级 (DDGS 为默认首选)
NEWS_PROVIDERS_INTERNATIONAL = ["ddgs", "tavily", "polygon"]
NEWS_PROVIDERS_CHINA = ["ddgs", "polygon"]

# 备用 API Keys（可选，DDGS 不需要）
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
```

## 返回数据格式

所有适配器返回统一格式：

```python
[
    {
        "title": "NVIDIA Announces Record Q4 Revenue",
        "snippet": "NVIDIA reported record revenue of $22.1 billion...",
        "source": "reuters.com",
        "url": "https://...",
        "date": "2024-02-21"
    },
    ...
]
```

## DDGS 高级用法

```python
from src.analyzers.news_adapters import DDGSAdapter

# 指定区域
adapter = DDGSAdapter(region="cn-zh")  # 中文区域

# 新闻搜索
news = adapter.search("NVIDIA 财报", days_range=7)

# 通用文本搜索
results = adapter.search_text("Python tutorial", max_results=20)
```

## 添加新适配器

1. 创建新文件 `xxx_adapter.py`
2. 继承 `NewsAdapter` 基类
3. 实现 `search()` 方法
4. 在 `__init__.py` 中注册

```python
from .base import NewsAdapter

class XxxAdapter(NewsAdapter):
    name = "xxx"
    requires_api_key = False  # 或 True

    def search(self, query, search_date=None, days_range=3):
        # 实现搜索逻辑
        # 返回标准化结果
        pass
```

## 相关链接

| 资源 | 链接 |
|-----|------|
| DDGS GitHub | https://github.com/deedy5/duckduckgo_search |
| Tavily | https://tavily.com |
| Polygon.io | https://polygon.io |
