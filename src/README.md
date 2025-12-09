# src - 源代码目录

Trading Coach 核心源代码，采用分层架构设计。

## 目录结构

```
src/
├── models/          # 数据模型层 - SQLAlchemy ORM 定义
├── importers/       # 数据导入层 - CSV 解析和清洗
├── matchers/        # 配对引擎层 - FIFO 交易配对算法
├── data_sources/    # 数据源层 - 市场数据获取和缓存
├── indicators/      # 指标计算层 - 技术指标计算
├── analyzers/       # 分析引擎层 - 质量评分和期权分析
├── reports/         # 报告生成层 - 交易复盘报告
└── utils/           # 工具函数层 - 通用辅助功能
```

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    报告生成层 (reports/)                      │
│                  生成交易复盘和分析报告                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    分析引擎层 (analyzers/)                    │
│          质量评分 │ 期权分析 │ 策略分类 │ 复盘生成            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    指标计算层 (indicators/)                   │
│            RSI │ MACD │ 布林带 │ ATR │ MA │ ADX             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    配对引擎层 (matchers/)                     │
│              FIFO配对 │ Symbol匹配 │ 数量追踪                │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    数据源层 (data_sources/)                   │
│           YFinance客户端 │ 三级缓存 │ 批量获取器              │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    数据导入层 (importers/)                    │
│                  CSV解析器 │ 数据清洗器                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    数据模型层 (models/)                       │
│           Trade │ Position │ MarketData │ 市场环境           │
└─────────────────────────────────────────────────────────────┘
```

## 数据流

1. **导入阶段**: CSV → CSVParser → DataCleaner → Trade 表
2. **配对阶段**: Trade → FIFOMatcher → Position 表
3. **数据补充**: Position → YFinanceClient → CacheManager → MarketData 表
4. **指标计算**: MarketData → IndicatorCalculator → MarketData (更新指标字段)
5. **质量评分**: Position + MarketData → QualityScorer → Position (更新评分字段)
6. **期权分析**: Position (期权) → OptionTradeAnalyzer → Position (更新期权分析)
7. **报告生成**: Position → OptionTradeReport → 分析报告

## 模块依赖关系

```
models (基础，无依赖)
    ↑
importers (依赖 models)
    ↑
matchers (依赖 models)
    ↑
data_sources (依赖 models)
    ↑
indicators (依赖 models, data_sources)
    ↑
analyzers (依赖 models, indicators, data_sources)
    ↑
reports (依赖 models, analyzers)
```

## 使用示例

```python
# 初始化数据库
from src.models.base import init_database, get_session
init_database('sqlite:///tradingcoach.db')
session = get_session()

# 导入交易数据
from src.importers.csv_parser import CSVParser
from src.importers.data_cleaner import DataCleaner
parser = CSVParser('trades.csv')
df = parser.parse()
cleaner = DataCleaner()
trades = cleaner.clean_and_save(df, session)

# FIFO配对
from src.matchers.fifo_matcher import FIFOMatcher
matcher = FIFOMatcher(session)
result = matcher.match_all_trades()

# 获取市场数据
from src.data_sources.yfinance_client import YFinanceClient
client = YFinanceClient()
ohlcv = client.get_ohlcv('AAPL', start_date, end_date)

# 计算技术指标
from src.indicators.calculator import IndicatorCalculator
calculator = IndicatorCalculator()
df_with_indicators = calculator.calculate_all_indicators(ohlcv)

# 质量评分
from src.analyzers.quality_scorer import QualityScorer
scorer = QualityScorer()
score = scorer.calculate_overall_score(session, position)

# 期权分析
from src.analyzers.option_analyzer import OptionTradeAnalyzer
analyzer = OptionTradeAnalyzer(session)
analysis = analyzer.analyze_position(option_position)
```

## 技术栈

| 组件 | 技术 |
|------|------|
| ORM | SQLAlchemy 2.0 |
| 数据处理 | pandas, numpy |
| 市场数据 | yfinance |
| 重试机制 | tenacity |
| 日志 | Python logging |
