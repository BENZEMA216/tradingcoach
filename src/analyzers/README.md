# analyzers/

一旦我所属的文件夹有所变化，请更新我

## 架构说明

交易质量分析和评分的核心模块。采用多维度评分体系，包含入场/出场质量评估、
技术指标配合分析、期权专属评分等。为交易复盘提供量化的评价标准。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出分析器类 |
| `quality_scorer.py` | 质量评分器 | V2.1评分系统：9维度评分（含新闻契合度） |
| `behavior_scorer.py` | 行为评分器 | 分析交易行为模式，识别冲动/纪律等特征 |
| `execution_scorer.py` | 执行评分器 | 评估交易执行质量，滑点/时机等 |
| `market_env_scorer.py` | 市场环境评分器 | 评估入场时的市场环境适配度 |
| `news_searcher.py` | 新闻搜索器 | 搜索交易日相关新闻，情感分析，类别标记 |
| `news_alignment_scorer.py` | 新闻契合度评分器 | 评估交易与新闻背景的契合程度 |
| `news_adapters/` | 新闻适配器模块 | 多提供商新闻搜索（Tavily/Bing/Polygon） |
| `option_analyzer.py` | 期权分析器 | 期权交易专属分析：Moneyness/DTE/Greeks |
| `option_strategy_detector.py` | 期权策略识别器 | 自动识别期权组合策略（Covered Call/Collar/Iron Condor等） |
| `strategy_classifier.py` | 策略分类器 | 自动识别交易策略类型 |
| `review_generator.py` | 复盘生成器 | 生成交易复盘文字总结 |
| `insight_generator.py` | 洞察生成器 | 生成交易模式洞察（含案例关联、模式统计、根因分析） |
| `root_cause_analyzer.py` | 根因分析器 | 亏损/盈利归因（时机/方向/仓位/事件/执行）、行为模式检测 |
| `event_detector.py` | 事件检测器 | 财报日历获取、价格/成交量异常检测、持仓事件关联 |

---

## 设计思路

### 核心理念

**问题**: 交易复盘缺乏量化标准，难以客观评估交易质量。

**解决方案**: 四维度评分体系 + 期权专属分析

```
综合评分 = 入场质量(30%) + 出场质量(25%) + 趋势把握(25%) + 风险管理(20%)
```

### 架构设计

```
QualityScorer (基础评分)
    ├── 入场质量评分
    ├── 出场质量评分
    ├── 趋势把握评分
    ├── 风险管理评分
    └── 期权专属评分 (扩展)

OptionTradeAnalyzer (期权分析)
    ├── 合约解析
    ├── 入场环境分析
    ├── 正股走势分析
    └── Greeks 影响估算

StrategyClassifier (策略分类)
ReviewGenerator (复盘生成)
```

## 文件说明

| 文件 | 说明 | 行数 |
|------|------|------|
| `quality_scorer.py` | 质量评分器 (含期权扩展) | ~2000 |
| `option_analyzer.py` | 期权交易分析器 | ~500 |
| `strategy_classifier.py` | 策略分类器 | ~300 |
| `review_generator.py` | 复盘生成器 | ~200 |

## QualityScorer

### 四维度评分

#### 1. 入场质量 (30%)

| 子维度 | 权重 | 评估内容 |
|--------|------|---------|
| 技术指标 | 30% | RSI、MACD 是否支持方向 |
| 支撑阻力 | 25% | 是否在关键位置入场 |
| 趋势配合 | 25% | 是否顺势交易 |
| 时机选择 | 20% | 入场点位是否精准 |

#### 2. 出场质量 (25%)

| 子维度 | 权重 | 评估内容 |
|--------|------|---------|
| 止盈执行 | 30% | 是否在目标位出场 |
| 止损纪律 | 30% | 是否及时止损 |
| 出场时机 | 20% | 是否抓住最佳出场点 |
| 持仓管理 | 20% | 持仓时间是否合理 |

#### 3. 趋势把握 (25%)

| 子维度 | 权重 | 评估内容 |
|--------|------|---------|
| 方向一致性 | 40% | 交易方向与趋势是否一致 |
| 趋势强度 | 30% | ADX 趋势强度指标 |
| 动量配合 | 30% | MACD、RSI 动量指标 |

#### 4. 风险管理 (20%)

| 子维度 | 权重 | 评估内容 |
|--------|------|---------|
| R:R 比率 | 40% | 风险回报比 |
| MAE 控制 | 30% | 最大不利偏移控制 |
| MFE 利用 | 30% | 最大有利偏移利用率 |

### 评分等级

| 分数 | 等级 | 说明 |
|------|------|------|
| 90-100 | A | 优秀 |
| 80-89 | B | 良好 |
| 70-79 | C | 一般 |
| 60-69 | D | 较差 |
| 0-59 | F | 很差 |

### 使用示例

```python
from src.analyzers.quality_scorer import QualityScorer

scorer = QualityScorer()

# 计算综合评分
result = scorer.calculate_overall_score(session, position)

print(f"入场质量: {result['entry_score']}")
print(f"出场质量: {result['exit_score']}")
print(f"趋势把握: {result['trend_score']}")
print(f"风险管理: {result['risk_score']}")
print(f"综合评分: {result['overall_score']}")
print(f"评分等级: {result['grade']}")
```

## 期权评分扩展

### 期权入场评分 (各25%)

| 维度 | 评估内容 | 最优条件 |
|------|---------|---------|
| Moneyness | 虚值/平值/实值程度 | ATM ± 5% |
| 趋势一致性 | Call配多头/Put配空头 | 方向匹配 |
| 波动率环境 | IV 是否合理 | 中等波动 |
| 时间价值 | DTE 是否合理 | 30-60天 |

### 期权出场评分

| 维度 | 权重 | 评估内容 |
|------|------|---------|
| 方向正确 | 30% | 正股走向符合预期 |
| 时间剩余 | 25% | 避免 Theta 加速 |
| 盈利捕获 | 25% | 止盈执行度 |
| 止损纪律 | 20% | 及时止损 |

### 期权策略评分

| 维度 | 权重 | 评估内容 |
|------|------|---------|
| 到期日选择 | 30% | DTE 是否适合策略 |
| 行权价选择 | 30% | Moneyness 是否合理 |
| 方向选择 | 20% | Call/Put 是否正确 |
| 资金效率 | 20% | 杠杆是否恰当 |

### 综合评分计算

```python
# 股票基础评分 (60%)
stock_score = (entry + exit + trend + risk) / 4

# 期权专属评分 (40%)
option_score = (option_entry + option_exit + option_strategy) / 3

# 最终综合评分
overall = stock_score * 0.6 + option_score * 0.4
```

## OptionTradeAnalyzer

### 核心功能

1. **合约解析**: 从期权代码提取标的、到期日、行权价、Call/Put
2. **入场分析**: Moneyness、DTE、技术指标、趋势一致性
3. **正股分析**: 持有期间价格变动、是否触及行权价
4. **Greeks 估算**: 基于 Moneyness 估算 Delta/Theta

### 使用示例

```python
from src.analyzers.option_analyzer import OptionTradeAnalyzer

analyzer = OptionTradeAnalyzer(session)

# 解析期权代码
info = analyzer.parse_option_symbol('AAPL250404C227500')
# {'underlying': 'AAPL', 'expiry': date(2025,4,4), 'type': 'call', 'strike': 227.5}

# 分析持仓
analysis = analyzer.analyze_position(option_position)

print(f"入场 Moneyness: {analysis['entry_context']['moneyness']}%")
print(f"入场 DTE: {analysis['entry_context']['dte']}天")
print(f"正股变动: {analysis['underlying_movement']['price_change']}%")
print(f"Delta 影响: {analysis['greeks_impact']['delta_impact']}")
```

### Moneyness 计算

```python
# Call 期权
moneyness = (stock_price - strike) / strike * 100

# Put 期权
moneyness = (strike - stock_price) / strike * 100

# 分类
ITM: moneyness > 2%   # 实值
ATM: -2% <= moneyness <= 2%  # 平值
OTM: moneyness < -2%  # 虚值
```

### DTE 分类

| 范围 | 分类 | 特点 |
|------|------|------|
| < 7天 | short | 高 Theta 风险 |
| 7-30天 | medium | 常规交易周期 |
| 30-90天 | long | 适合趋势交易 |
| > 90天 | leaps | 长期投资 |

## StrategyClassifier

自动识别交易策略类型。

### 支持的策略

| 策略 | 识别条件 |
|------|---------|
| trend | 顺趋势，ADX > 25 |
| mean_reversion | 逆趋势，RSI 极端值 |
| breakout | 突破关键价位 |
| momentum | 动量追涨杀跌 |
| range | 区间震荡交易 |

### 使用示例

```python
from src.analyzers.strategy_classifier import StrategyClassifier

classifier = StrategyClassifier()
result = classifier.classify(position, entry_indicators)

print(f"策略类型: {result['strategy_type']}")
print(f"置信度: {result['confidence']}%")
```

## 评分流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Position 持仓记录                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               获取入场/出场时市场数据                         │
│               MarketData + 技术指标                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   股票基础评分       │       │   期权专属评分       │
│   (is_option=0)     │       │   (is_option=1)     │
│                     │       │                     │
│   ├── 入场质量      │       │   ├── 期权入场      │
│   ├── 出场质量      │       │   ├── 期权出场      │
│   ├── 趋势把握      │       │   └── 期权策略      │
│   └── 风险管理      │       │                     │
└─────────┬───────────┘       └─────────┬───────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    综合评分计算                              │
│         股票: 四维度平均                                     │
│         期权: 股票60% + 期权40%                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               更新 Position 评分字段                         │
└─────────────────────────────────────────────────────────────┘
```
