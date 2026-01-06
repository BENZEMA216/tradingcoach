# 开发者指南

本文档面向想要参与开发或理解代码的技术人员，详细介绍如何搭建开发环境、理解项目架构、以及使用各个核心模块。

---

## 目录

1. [项目概述](#1-项目概述)
2. [开发环境搭建](#2-开发环境搭建)
3. [核心模块说明](#3-核心模块说明)
4. [常用脚本使用](#4-常用脚本使用)
5. [测试指南](#5-测试指南)
6. [可视化Dashboard](#6-可视化dashboard)
7. [Git工作流](#7-git工作流)
8. [常见问题FAQ](#8-常见问题faq)

---

## 1. 项目概述

### 1.1 架构设计

Trading Coach 采用分层架构设计：

```
┌─────────────────────────────────────────────────────────┐
│                  可视化层 (Streamlit)                    │
│   Dashboard  │  数据概览  │  质量评分  │  技术指标       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  分析引擎层                              │
│   质量评分器  │  指标计算器  │  FIFO配对器              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  数据层                                  │
│   数据模型  │  数据源客户端  │  缓存管理器              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│               持久化层 (SQLite)                          │
│   trades  │  positions  │  market_data  │  ...          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.9+ |
| 数据库 | SQLite |
| ORM | SQLAlchemy 2.0+ |
| 数据处理 | pandas, numpy |
| 市场数据 | yfinance |
| Web框架 | Streamlit |
| 可视化 | Plotly |
| 测试 | pytest, pytest-cov |

### 1.3 目录结构

```
tradingcoach/
├── src/                      # 源代码
│   ├── models/              # 数据模型 (SQLAlchemy ORM)
│   │   ├── base.py          # 数据库连接管理
│   │   ├── trade.py         # 交易记录模型
│   │   ├── position.py      # 持仓记录模型
│   │   └── market_data.py   # 市场数据模型
│   ├── importers/           # 数据导入
│   │   ├── csv_parser.py    # CSV解析器
│   │   └── data_cleaner.py  # 数据清洗器
│   ├── matchers/            # 交易配对
│   │   └── fifo_matcher.py  # FIFO配对算法
│   ├── data_sources/        # 市场数据获取
│   │   ├── base_client.py   # 抽象基类
│   │   ├── yfinance_client.py  # yfinance客户端
│   │   ├── cache_manager.py # 三级缓存管理
│   │   └── batch_fetcher.py # 批量获取器
│   ├── indicators/          # 技术指标
│   │   └── calculator.py    # 指标计算器
│   ├── analyzers/           # 分析器
│   │   ├── quality_scorer.py # 质量评分器
│   │   └── option_analyzer.py # 期权分析器
│   ├── reports/             # 报告生成
│   │   └── option_report.py  # 期权交易报告
│   └── utils/               # 工具函数
│       ├── timezone.py      # 时区转换
│       └── symbol_parser.py # 代码解析
├── scripts/                 # 脚本工具
│   ├── init_db.py          # 初始化数据库
│   ├── import_trades.py    # 导入交易数据
│   ├── run_matching.py     # 运行FIFO配对
│   ├── preload_market_data.py  # 预加载市场数据
│   ├── calculate_indicators.py # 计算技术指标
│   └── score_positions.py  # 交易质量评分
├── visualization/           # 可视化模块
│   ├── dashboard.py        # 主入口
│   ├── pages/              # 页面组件
│   └── components/         # 可复用组件
├── tests/                   # 测试
│   └── unit/               # 单元测试
│       ├── test_quality_scorer.py
│       ├── test_option_analyzer.py  # 期权分析测试
│       └── ...
├── project_docs/            # 项目文档
├── original_data/           # 原始数据
├── data/                    # 处理后数据
├── cache/                   # 缓存文件
├── logs/                    # 日志文件
├── config.py               # 配置文件（不提交）
├── config_template.py      # 配置模板
├── requirements.txt        # 依赖列表
└── tradingcoach.db         # SQLite数据库
```

---

## 2. 开发环境搭建

### 2.1 系统要求

- Python 3.9 或更高版本
- pip 包管理器
- Git

### 2.2 克隆仓库

```bash
git clone https://github.com/BENZEMA216/tradingcoach.git
cd tradingcoach
```

### 2.3 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2.4 安装依赖

```bash
pip install -r requirements.txt
```

### 2.5 配置文件设置

```bash
# 复制配置模板
cp config_template.py config.py
```

编辑 `config.py`，主要配置项：

```python
# 数据库路径
DATABASE_URL = 'sqlite:///tradingcoach.db'

# 市场数据API（如果需要）
ALPHA_VANTAGE_API_KEY = 'your_key_here'

# 评分权重
SCORE_WEIGHT_ENTRY = 0.30  # 进场质量权重
SCORE_WEIGHT_EXIT = 0.25   # 出场质量权重
SCORE_WEIGHT_TREND = 0.25  # 趋势把握权重
SCORE_WEIGHT_RISK = 0.20   # 风险管理权重
```

### 2.6 初始化数据库

```bash
python3 scripts/init_db.py
```

这将创建 `tradingcoach.db` 文件和所有必要的表结构。

---

## 3. 核心模块说明

### 3.1 数据模型 (`src/models/`)

#### Trade 模型 (`trade.py`)
存储原始交易记录：

```python
class Trade:
    id: int                    # 主键
    symbol: str               # 股票代码
    direction: str            # 交易方向 (buy/sell/sell_short/buy_to_cover)
    order_price: Decimal      # 订单价格
    filled_price: Decimal     # 成交价格
    order_quantity: int       # 订单数量
    filled_quantity: int      # 成交数量
    order_time: datetime      # 下单时间
    filled_time: datetime     # 成交时间
    total_fees: Decimal       # 总费用
    market_type: str          # 市场类型 (US_STOCK/HK_STOCK/OPTION)
```

#### Position 模型 (`position.py`)
存储配对后的持仓记录：

```python
class Position:
    id: int                   # 主键
    symbol: str               # 股票代码
    direction: str            # 方向 (long/short)
    open_price: Decimal       # 开仓价格
    close_price: Decimal      # 平仓价格
    quantity: int             # 数量
    open_time: datetime       # 开仓时间
    close_time: datetime      # 平仓时间
    realized_pnl: Decimal     # 已实现盈亏
    holding_period_days: int  # 持仓天数

    # 质量评分字段
    entry_quality_score: float    # 进场质量分
    exit_quality_score: float     # 出场质量分
    trend_quality_score: float    # 趋势把握分
    risk_mgmt_score: float        # 风险管理分
    overall_score: float          # 综合评分
    score_grade: str              # 等级 (A+/A/A-/B+/B/B-/C+/C/C-/D/F)

    # 期权相关字段 (is_option=1 时有效)
    underlying_symbol: str        # 标的股票代码
    is_option: int                # 是否为期权 (0/1)
    option_type: str              # 期权类型 (call/put)
    strike_price: Decimal         # 行权价
    expiry_date: date             # 到期日
    entry_moneyness: float        # 入场时Moneyness百分比
    entry_dte: int                # 入场时剩余天数(DTE)
    exit_dte: int                 # 出场时剩余天数(DTE)
    option_entry_score: float     # 期权入场评分
    option_exit_score: float      # 期权出场评分
    option_strategy_score: float  # 期权策略评分
    option_analysis: JSON         # 期权分析详情
```

#### MarketData 模型 (`market_data.py`)
存储市场数据和技术指标：

```python
class MarketData:
    id: int                   # 主键
    symbol: str               # 股票代码
    date: date                # 日期
    open: Decimal             # 开盘价
    high: Decimal             # 最高价
    low: Decimal              # 最低价
    close: Decimal            # 收盘价
    volume: int               # 成交量

    # 技术指标
    rsi_14: float             # RSI(14)
    macd: float               # MACD
    macd_signal: float        # MACD信号线
    macd_hist: float          # MACD柱状图
    bb_upper: float           # 布林带上轨
    bb_middle: float          # 布林带中轨
    bb_lower: float           # 布林带下轨
    atr_14: float             # ATR(14)
    ma_5/10/20/50/200: float  # 移动平均线
```

### 3.2 数据导入 (`src/importers/`)

#### CSV解析器 (`csv_parser.py`)
负责解析券商导出的CSV文件：

```python
from src.importers.csv_parser import CSVParser

parser = CSVParser()
trades_df = parser.parse('original_data/交易记录.csv')
```

支持的CSV格式：
- UTF-8 BOM 编码
- 中文字段名
- 自动字段映射

#### 数据清洗器 (`data_cleaner.py`)
负责数据清洗和标准化：

```python
from src.importers.data_cleaner import DataCleaner

cleaner = DataCleaner()
cleaned_df = cleaner.clean(trades_df)
```

清洗功能：
- 过滤撤单/失败订单
- 标准化交易方向
- 处理部分成交
- 数字格式转换

### 3.3 FIFO配对 (`src/matchers/`)

#### FIFO配对器 (`fifo_matcher.py`)
实现先进先出配对算法：

```python
from src.matchers.fifo_matcher import FIFOMatcher

matcher = FIFOMatcher(session)
positions = matcher.match_all_trades()
```

支持的配对场景：
- 标准做多 (buy → sell)
- 做空 (sell_short → buy_to_cover)
- 部分成交配对
- 期权配对

### 3.4 市场数据 (`src/data_sources/`)

#### YFinance客户端 (`yfinance_client.py`)
获取市场数据：

```python
from src.data_sources.yfinance_client import YFinanceClient
from datetime import date

client = YFinanceClient()
df = client.get_ohlcv('AAPL', date(2024, 1, 1), date(2024, 12, 31))
```

特性：
- 限流控制 (2000请求/小时)
- 指数退避重试
- 多市场支持 (US/HK/CN)

#### 缓存管理器 (`cache_manager.py`)
三级缓存系统：

```python
from src.data_sources.cache_manager import CacheManager

cache = CacheManager(session)
data = cache.get('AAPL', date(2024, 1, 1), date(2024, 12, 31))
```

缓存层级：
- L1: 内存缓存 (LRU, 100条目)
- L2: 数据库缓存 (持久化)
- L3: 磁盘缓存 (pickle文件)

### 3.5 技术指标 (`src/indicators/`)

#### 指标计算器 (`calculator.py`)
纯pandas实现的技术指标计算：

```python
from src.indicators.calculator import IndicatorCalculator

calculator = IndicatorCalculator()
df = calculator.calculate_all(ohlcv_df)
```

支持的指标：
- RSI (14天)
- MACD (12, 26, 9)
- 布林带 (20天, 2σ)
- ATR (14天)
- MA系列 (5, 10, 20, 50, 200天)

### 3.6 质量评分 (`src/analyzers/`)

#### 质量评分器 (`quality_scorer.py`)
四维度交易质量评分：

```python
from src.analyzers.quality_scorer import QualityScorer

scorer = QualityScorer()
result = scorer.calculate_overall_score(session, position)
```

评分维度：
- **进场质量 (30%)**: 技术指标配合度、支撑阻力位置
- **出场质量 (25%)**: 出场时机、止盈止损执行
- **趋势把握 (25%)**: 方向一致性、趋势强度
- **风险管理 (20%)**: RR比、MAE/MFE分析

评分等级：
- A+/A/A-: 85-100分 (优秀)
- B+/B/B-: 70-84分 (良好)
- C+/C/C-: 55-69分 (一般)
- D: 50-54分 (较差)
- F: 0-49分 (很差)

### 3.7 期权分析 (`src/analyzers/option_analyzer.py`)

#### 期权交易分析器 (`OptionTradeAnalyzer`)
基于正股数据的期权交易分析，无需期权本身的OHLCV数据：

```python
from src.analyzers.option_analyzer import OptionTradeAnalyzer

analyzer = OptionTradeAnalyzer(session)
analysis = analyzer.analyze_position(position)
```

**核心功能**:

1. **期权合约解析** (`parse_option_symbol`):
   - 从期权代码解析：标的、到期日、Call/Put、行权价
   - 示例: `AAPL250404C227500` → AAPL, 2025-04-04, Call, $227.50

2. **入场环境分析** (`analyze_entry_context`):
   - Moneyness计算 (ITM/ATM/OTM百分比)
   - DTE分类 (short<7天, medium 7-30天, long 30-90天, LEAPS>90天)
   - 技术指标配合度
   - 趋势一致性检查 (Call配合上涨趋势, Put配合下跌趋势)

3. **正股走势分析** (`analyze_underlying_movement`):
   - 持有期间价格变动
   - 是否触及/越过行权价
   - 波动率分析

4. **Greeks影响估算** (`estimate_greeks_impact`):
   - Delta估算 (基于Moneyness)
   - Theta估算 (基于DTE和时间流逝)
   - 无需实际Greeks数据

5. **策略评估** (`evaluate_option_strategy`):
   - 到期日选择是否合理
   - 行权价选择是否合理
   - 时机评估

**Moneyness计算公式**:
```python
# Call期权
moneyness = (stock_price - strike) / strike * 100

# Put期权
moneyness = (strike - stock_price) / strike * 100
```

**DTE分类**:
| DTE范围 | 分类 | 说明 |
|---------|------|------|
| < 7天 | short | 高Theta衰减风险 |
| 7-30天 | medium | 常规交易周期 |
| 30-90天 | long | 适合趋势交易 |
| > 90天 | leaps | 长期投资/对冲 |

### 3.8 期权评分 (QualityScorer扩展)

QualityScorer已扩展支持期权特有的评分维度：

```python
from src.analyzers.quality_scorer import QualityScorer

scorer = QualityScorer()
# 期权入场评分
entry_score = scorer.score_option_entry(position, entry_md, option_info)
# 期权出场评分
exit_score = scorer.score_option_exit(position, entry_md, exit_md, option_info)
# 期权策略评分
strategy_score = scorer.score_option_strategy(position, entry_md, option_info)
# 综合评分 (股票60% + 期权40%)
overall = scorer.calculate_option_overall_score(position, entry_md, exit_md, option_info)
```

**期权入场评分维度** (各25%):
| 维度 | 说明 | 最优条件 |
|------|------|----------|
| Moneyness | 虚值/平值/实值 | ATM附近最佳 |
| 趋势一致性 | 方向与技术面匹配 | Call配多头, Put配空头 |
| 波动率 | IV/HV环境 | 中等波动率 |
| 时间价值 | DTE合理性 | 30-60天 |

**期权出场评分维度**:
| 维度 | 权重 | 说明 |
|------|------|------|
| 方向正确 | 30% | 正股走向是否符合预期 |
| 时间剩余 | 25% | 避免最后几天的Theta加速 |
| 盈利捕获 | 25% | 止盈执行度 |
| 止损纪律 | 20% | 止损是否及时 |

**期权策略评分维度**:
| 维度 | 权重 | 说明 |
|------|------|------|
| 到期日选择 | 30% | DTE是否适合策略 |
| 行权价选择 | 30% | Moneyness是否合理 |
| 方向选择 | 20% | Call/Put是否正确 |
| 资金效率 | 20% | 杠杆使用是否恰当 |

**综合评分计算**:
```python
# 股票基础评分 (60%)
stock_score = (entry_score + exit_score + trend_score + risk_score) / 4

# 期权专属评分 (40%)
option_score = (option_entry + option_exit + option_strategy) / 3

# 最终综合评分
overall_score = stock_score * 0.6 + option_score * 0.4
```

### 3.9 期权报告 (`src/reports/option_report.py`)

生成期权交易复盘报告：

```python
from src.reports.option_report import OptionTradeReport

report = OptionTradeReport(session)

# 汇总统计
summary = report.generate_summary(option_positions)

# 单个持仓详情
detail = report.generate_position_detail(position)

# 策略洞察
insights = report.generate_strategy_insights(option_positions)
```

**汇总统计** (`generate_summary`):
```python
{
    'total_count': 64,           # 期权交易总数
    'total_pnl': -1234.56,       # 总盈亏
    'win_rate': 0.35,            # 胜率
    'by_type': {                 # 按类型分组
        'call': {'count': 40, 'pnl': -800, 'win_rate': 0.30},
        'put': {'count': 24, 'pnl': -434, 'win_rate': 0.42}
    },
    'by_moneyness': {            # 按Moneyness分组
        'itm': {...},
        'atm': {...},
        'otm': {...}
    },
    'by_dte': {                  # 按DTE分组
        'short': {...},
        'medium': {...},
        'long': {...}
    }
}
```

**持仓详情** (`generate_position_detail`):
```python
{
    'basic_info': {...},         # 基本信息
    'entry_analysis': {...},     # 入场分析
    'exit_analysis': {...},      # 出场分析
    'greeks_impact': {...},      # Greeks影响
    'scores': {...},             # 评分详情
    'suggestions': [             # 改进建议
        "考虑选择更长的到期日以减少Theta损耗",
        "入场时Moneyness较高，可考虑更接近ATM的行权价"
    ]
}
```

**策略洞察** (`generate_strategy_insights`):
```python
{
    'best_strategies': [...],    # 最佳策略组合
    'loss_patterns': [...],      # 亏损模式识别
    'optimal_params': {          # 最优参数
        'best_dte_range': '30-60天',
        'best_moneyness': 'ATM ± 5%',
        'best_holding_period': '5-15天'
    }
}
```

---

## 4. 常用脚本使用

### 4.1 初始化数据库

```bash
python3 scripts/init_db.py
```

创建数据库和所有表结构。如果数据库已存在，会提示是否重建。

### 4.2 导入交易数据

```bash
# 基本用法
python3 scripts/import_trades.py --file original_data/交易记录.csv

# 预览模式（不实际导入）
python3 scripts/import_trades.py --file 交易记录.csv --dry-run

# 指定批次大小
python3 scripts/import_trades.py --file 交易记录.csv --batch-size 100
```

### 4.3 运行FIFO配对

```bash
# 配对所有未配对的交易
python3 scripts/run_matching.py --all

# 配对指定symbol
python3 scripts/run_matching.py --symbol AAPL
```

### 4.4 预加载市场数据

```bash
# 预加载所有交易相关的市场数据
python3 scripts/preload_market_data.py --all

# 仅预热Top N个symbol
python3 scripts/preload_market_data.py --warmup-only --top-n 10
```

### 4.5 计算技术指标

```bash
# 计算所有市场数据的技术指标
python3 scripts/calculate_indicators.py --all

# 计算指定symbol
python3 scripts/calculate_indicators.py --symbols AAPL,TSLA,TSLL
```

### 4.6 交易质量评分

```bash
# 评分所有已平仓交易
python3 scripts/score_positions.py --all

# 评分指定position
python3 scripts/score_positions.py --positions 1,2,3

# 仅查看已有评分
python3 scripts/score_positions.py --show-only --limit 50
```

---

## 5. 测试指南

### 5.1 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试文件
python3 -m pytest tests/unit/test_quality_scorer.py -v

# 运行特定测试类
python3 -m pytest tests/unit/test_quality_scorer.py::TestEntryScoring -v

# 显示测试覆盖率
python3 -m pytest tests/ --cov=src --cov-report=html
```

### 5.2 测试结构

```
tests/
└── unit/
    ├── test_csv_parser.py        # CSV解析测试
    ├── test_data_cleaner.py      # 数据清洗测试
    ├── test_fifo_matcher.py      # FIFO配对测试
    ├── test_yfinance_client.py   # yfinance客户端测试
    ├── test_cache_manager.py     # 缓存管理测试
    ├── test_indicator_calculator.py  # 指标计算测试
    ├── test_quality_scorer.py    # 质量评分测试
    ├── test_option_analyzer.py   # 期权分析测试 (24个用例)
    └── ...
```

### 5.3 添加新测试

测试文件命名规范：`test_<module_name>.py`

测试类命名规范：`Test<FeatureName>`

```python
import pytest
from src.analyzers.quality_scorer import QualityScorer

class TestMyFeature:
    """测试我的新功能"""

    @pytest.fixture
    def scorer(self):
        """创建评分器实例"""
        return QualityScorer()

    def test_basic_functionality(self, scorer):
        """测试基本功能"""
        result = scorer.some_method()
        assert result is not None
```

---

## 6. 可视化Dashboard

### 6.1 启动Dashboard

```bash
streamlit run visualization/dashboard.py
```

浏览器自动打开 `http://localhost:8501`

### 6.2 页面功能

| 页面 | 功能 |
|------|------|
| 数据概览 | 查看交易统计、数据覆盖率、识别数据缺失 |
| 质量评分 | 四维度评分分析、评分分布、盈亏关系 |
| FIFO验证 | 可视化匹配过程、验证系统逻辑 |
| 技术指标 | K线图、RSI/MACD/BB、交易点位标注 |

### 6.3 开发新页面

在 `visualization/pages/` 目录下创建新文件：

```python
# visualization/pages/5_新页面.py
import streamlit as st
from visualization.utils.data_loader import DataLoader

st.set_page_config(page_title="新页面", layout="wide")
st.title("新页面标题")

# 加载数据
loader = DataLoader()
positions = loader.get_positions()

# 展示内容
st.dataframe(positions)
```

---

## 7. Git工作流

### 7.1 分支命名规范

```bash
main           # 主分支，稳定版本
dev/feature    # 功能开发分支
fix/bug-name   # Bug修复分支
docs/doc-name  # 文档更新分支
```

### 7.2 提交信息格式

```bash
feat(module): 新功能描述     # 新功能
fix(module): Bug修复描述     # Bug修复
docs(module): 文档更新描述   # 文档更新
refactor(module): 重构描述   # 代码重构
test(module): 测试相关       # 测试
chore(module): 杂项更新      # 其他
```

示例：
```bash
git commit -m "feat(analyzer): 添加四维度质量评分系统"
git commit -m "fix(parser): 修复中文字段名解析问题"
git commit -m "docs(readme): 更新开发进度"
```

### 7.3 开发流程

1. 从 `main` 创建功能分支
2. 开发并测试
3. 运行所有测试确保通过
4. 提交代码
5. 创建 Pull Request
6. 代码审查后合并

---

## 8. 常见问题FAQ

### Q1: 数据库报错 "table already exists"
**A**: 运行 `python3 scripts/init_db.py`，选择重建数据库。

### Q2: yfinance获取数据失败
**A**:
- 检查网络连接
- 确认股票代码正确
- 可能触发限流，等待几分钟后重试

### Q3: 技术指标计算返回NaN
**A**: 技术指标需要足够的历史数据。例如MA200需要至少200天数据。

### Q4: 评分结果都是C级
**A**:
- 检查是否有足够的市场数据
- 确认技术指标已计算
- 部分交易可能缺少MAE/MFE数据

### Q5: 如何添加新的数据源
**A**:
1. 在 `src/data_sources/` 创建新客户端
2. 继承 `BaseDataClient` 抽象类
3. 实现 `get_ohlcv()` 等方法
4. 添加单元测试

### Q6: 如何修改评分权重
**A**: 编辑 `config.py` 中的权重配置：
```python
SCORE_WEIGHT_ENTRY = 0.30
SCORE_WEIGHT_EXIT = 0.25
SCORE_WEIGHT_TREND = 0.25
SCORE_WEIGHT_RISK = 0.20
```

---

## 更新日志

- **2025-12-04**: 添加期权分析框架文档 (3.7-3.9节)
- **2025-11-27**: 创建开发者指南文档
- **2025-11-20**: Phase 6 完成，技术指标计算
- **2025-11-18**: Phase 5 完成，市场数据缓存系统
- **2025-11-16**: Phase 4 完成，FIFO配对算法
- **2025-11-14**: Phase 3 完成，CSV导入模块

---

如有问题，请在 GitHub Issues 中提出：https://github.com/BENZEMA216/tradingcoach/issues
