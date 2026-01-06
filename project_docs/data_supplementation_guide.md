# 市场数据补充指南
# Market Data Supplementation Guide

## 目录

1. [概述](#概述)
2. [为什么需要补充数据](#为什么需要补充数据)
3. [数据补充流程](#数据补充流程)
4. [使用自动化工具](#使用自动化工具)
5. [手动补充数据](#手动补充数据)
6. [数据质量验证](#数据质量验证)
7. [常见问题](#常见问题)

---

## 概述

本指南说明如何根据交易CSV文件补充对应标的的历史市场数据，以支持完整的交易质量评分和技术分析。

### 核心目标

- 从用户上传的交易CSV中提取所有交易过的股票代码
- 自动获取这些股票的历史市场数据（OHLCV + 技术指标）
- 填补数据库中的市场数据空缺
- 提升质量评分的准确性

---

## 为什么需要补充数据

### 当前系统状态

根据实际数据统计：

```
总交易记录: 2006 笔
总持仓: 1505 个 (1324 已平仓, 181 未平仓)
市场数据记录: 745 条
市场数据覆盖率: 仅 3/99 个股票 (15%)
```

### 数据缺失的影响

质量评分系统依赖四个维度：

| 维度 | 权重 | 当前平均分 | 数据依赖 | 影响 |
|------|------|------------|----------|------|
| 进场质量 (Entry) | 30% | **54.35** ⚠️ | 高度依赖市场数据 | 数据不足导致评分偏低 |
| 出场质量 (Exit) | 25% | 66.20 | 中等依赖 | 部分影响 |
| 趋势质量 (Trend) | 25% | 58.77 | 高度依赖市场数据 | 严重影响 |
| 风险管理 (Risk) | 20% | 64.54 | 中等依赖 | 部分影响 |

**关键发现**: 进场质量分数 54.35 显著低于预期 65-70 分，主要原因是缺少技术指标数据（RSI、MACD、MA等）。

### 补充数据后的预期改善

- 市场数据覆盖率: 15% → **95%+**
- 进场质量平均分: 54.35 → **65-70** (预期提升 20-30%)
- 趋势质量平均分: 58.77 → **65-72** (预期提升 10-20%)
- 总体评分准确性: **显著提升**

---

## 数据补充流程

### 流程图

```
用户交易CSV
    ↓
提取所有唯一股票代码
    ↓
检查数据库现有数据
    ↓
识别缺失数据的股票
    ↓
从 yfinance API 获取历史数据
    ↓
计算技术指标 (RSI, MACD, MA, etc.)
    ↓
写入数据库 (MarketData表)
    ↓
(可选) 重新评分受影响的持仓
    ↓
验证数据完整性
```

### 时间范围策略

为了确保质量评分准确，需要获取交易日期前后的充足数据：

```python
# 对于每个股票，获取数据的时间范围：
start_date = min(交易日期) - 60天  # 提供技术指标计算的基础数据
end_date = max(交易日期) + 30天    # 确保覆盖所有交易
```

**原因**:
- MA50 (50日均线) 需要至少50天的历史数据
- MACD 需要约 26-34 天的数据
- 充足的数据窗口确保指标计算准确

---

## 使用自动化工具

### 工具: `scripts/supplement_data_from_csv.py`

这是推荐的数据补充方式，全自动化处理。

### 基本用法

```bash
cd /path/to/tradingcoach

# 方式1: 从交易CSV文件补充数据
python3 scripts/supplement_data_from_csv.py \
    original_data/历史-保证金综合账户(2663)-20251103-231527.csv

# 方式2: 直接从数据库已有交易中提取股票代码
python3 scripts/supplement_data_from_csv.py --from-db

# 方式3: 指定特定股票列表
python3 scripts/supplement_data_from_csv.py --symbols AAPL,TSLA,GOOGL
```

### 高级选项

```bash
# 详细模式 (显示进度和详细信息)
python3 scripts/supplement_data_from_csv.py data.csv --verbose

# 仅显示将要处理的股票，不实际下载
python3 scripts/supplement_data_from_csv.py data.csv --dry-run

# 强制重新下载已有数据的股票
python3 scripts/supplement_data_from_csv.py data.csv --force

# 完成后自动重新评分
python3 scripts/supplement_data_from_csv.py data.csv --rescore

# 设置API请求延迟 (避免速率限制)
python3 scripts/supplement_data_from_csv.py data.csv --delay 2.0

# 批处理大小 (每批处理N个股票)
python3 scripts/supplement_data_from_csv.py data.csv --batch-size 10
```

### 输出示例

```
================================================================================
市场数据补充工具
================================================================================

[1/4] 从 CSV 提取股票代码...
  ✓ 找到 99 个唯一股票代码

[2/4] 检查数据库现有数据...
  ✓ 已有数据: 3 个股票 (TSLL, AAPL, FIG)
  ⚠️  缺失数据: 96 个股票

[3/4] 获取市场数据...
  进度: [████████░░░░░░░░░░░░] 10/96 (10.4%)

  处理: TSLA
    时间范围: 2024-01-15 → 2024-11-20
    获取: 217 天数据
    ✓ 技术指标计算完成
    ✓ 写入数据库: 217 条记录

  处理: GOOGL
    时间范围: 2024-02-01 → 2024-11-20
    获取: 198 天数据
    ✓ 技术指标计算完成
    ✓ 写入数据库: 198 条记录

  ...

  ✓ 成功: 94 个股票
  ⚠️  失败: 2 个股票 (详见日志)
  总计新增: 18,456 条市场数据记录

[4/4] 数据验证...
  ✓ 数据完整性检查通过
  ✓ 技术指标验证通过

================================================================================
补充完成!
================================================================================

补充前: 745 条记录 (3 股票, 覆盖率 15%)
补充后: 19,201 条记录 (97 股票, 覆盖率 98%)

建议下一步:
  python3 scripts/score_positions.py --all --force
  (重新评分所有持仓以反映新数据)
```

---

## 手动补充数据

如果需要更细粒度的控制，可以使用底层工具：

### 使用 `scripts/fetch_market_data.py`

```bash
# 获取单个股票的数据
python3 scripts/fetch_market_data.py AAPL \
    --start 2024-01-01 \
    --end 2024-11-20

# 从文件批量获取
echo "AAPL\nTSLA\nGOOGL" > symbols.txt
python3 scripts/fetch_market_data.py --file symbols.txt \
    --start 2024-01-01 \
    --end 2024-11-20

# 自动推断时间范围（基于数据库已有交易）
python3 scripts/fetch_market_data.py AAPL --auto-range
```

### Python API 方式

如果需要在自定义脚本中使用：

```python
from src.data.market_data_fetcher import MarketDataFetcher
from src.models.base import init_database, get_session
from datetime import datetime, timedelta

# 初始化
init_database('sqlite:///data/tradingcoach.db')
session = get_session()
fetcher = MarketDataFetcher(session)

# 获取单个股票数据
symbol = 'AAPL'
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 11, 20)

data = fetcher.fetch_and_store(symbol, start_date, end_date)
print(f"获取 {len(data)} 条数据")

# 批量获取
symbols = ['AAPL', 'TSLA', 'GOOGL']
for symbol in symbols:
    try:
        data = fetcher.fetch_and_store(symbol, start_date, end_date)
        print(f"✓ {symbol}: {len(data)} 条")
    except Exception as e:
        print(f"✗ {symbol}: {e}")

session.close()
```

---

## 数据质量验证

补充数据后，务必验证数据质量：

### 1. 检查覆盖率

```bash
python3 scripts/check_data_coverage.py
```

输出示例：
```
股票代码    交易次数    市场数据记录    覆盖率    状态
TSLL       274        245            89%      ✓
AAPL       84         78             93%      ✓
TSLA       156        0              0%       ✗ 缺失
...
```

### 2. 验证技术指标

```bash
python3 scripts/verify_indicators.py AAPL
```

检查项目：
- RSI 值在 0-100 范围内
- MACD 计算正确
- 移动平均线顺序合理
- 没有异常的空值

### 3. 数据一致性检查

```python
from src.models.market_data import MarketData
from src.models.base import get_session

session = get_session()

# 检查是否有异常数据
anomalies = session.query(MarketData).filter(
    (MarketData.close <= 0) |  # 价格异常
    (MarketData.volume < 0) |  # 成交量异常
    (MarketData.rsi > 100) |   # RSI异常
    (MarketData.rsi < 0)
).all()

if anomalies:
    print(f"⚠️  发现 {len(anomalies)} 条异常数据")
else:
    print("✓ 数据一致性检查通过")
```

---

## 常见问题

### Q1: yfinance API 速率限制问题

**问题**: 获取大量股票数据时被限速或封IP

**解决方案**:
```bash
# 增加请求延迟
python3 scripts/supplement_data_from_csv.py data.csv --delay 3.0

# 分批处理
python3 scripts/supplement_data_from_csv.py data.csv --batch-size 10

# 使用代理 (在代码中配置)
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

### Q2: 某些股票无法获取数据

**可能原因**:
1. 股票代码格式不正确 (如期权代码 `AMZN260618P195000`)
2. 股票已退市
3. 股票代码在 yfinance 中不存在

**解决方案**:
```bash
# 查看详细错误日志
python3 scripts/supplement_data_from_csv.py data.csv --verbose

# 手动验证股票代码
python3 -c "import yfinance as yf; print(yf.Ticker('AAPL').info)"
```

### Q3: 期权数据如何处理？

**问题**: 期权代码如 `AMZN260618P195000` 无法直接获取市场数据

**解决方案**:
系统会自动提取底层股票代码 (如 `AMZN`)，并获取股票的市场数据用于评分。

```python
# 自动代码提取示例
"AMZN260618P195000" → 提取 "AMZN"
"TSLA250117C400000" → 提取 "TSLA"
```

### Q4: 补充数据后质量评分没有变化？

**原因**: 数据已写入数据库，但持仓的质量评分是缓存的，需要重新评分。

**解决方案**:
```bash
# 强制重新评分所有持仓
python3 scripts/score_positions.py --all --force

# 或使用自动化工具的 --rescore 选项
python3 scripts/supplement_data_from_csv.py data.csv --rescore
```

### Q5: 如何只补充特定日期范围的数据？

**方案1**: 手动指定
```bash
python3 scripts/fetch_market_data.py AAPL \
    --start 2024-06-01 \
    --end 2024-09-30
```

**方案2**: 使用自动化工具 (自动推断)
```bash
# 自动根据交易日期推断范围
python3 scripts/supplement_data_from_csv.py data.csv
```

### Q6: 数据存储空间问题

**问题**: 担心市场数据占用太多磁盘空间

**估算**:
```
单个股票 1 年数据: ~250 条记录
每条记录大小: ~200 bytes
100 个股票 × 1年: ~5 MB

实际案例:
99 股票, 平均 200 天数据: ~3.9 MB
```

数据量很小，无需担心存储问题。

### Q7: 如何验证补充是否成功？

**三步验证法**:

```bash
# 1. 检查数据库记录数
python3 -c "
from src.models.base import init_database, get_session
from src.models.market_data import MarketData
init_database('sqlite:///data/tradingcoach.db')
session = get_session()
count = session.query(MarketData).count()
symbols = session.query(MarketData.symbol).distinct().count()
print(f'总记录: {count}, 股票数: {symbols}')
"

# 2. 检查覆盖率
python3 scripts/check_data_coverage.py

# 3. 验证质量评分
python3 scripts/score_positions.py --all --force
python3 scripts/analyze_scores.py
```

---

## 最佳实践

### 1. 首次使用建议流程

```bash
# Step 1: 从 CSV 自动补充数据
python3 scripts/supplement_data_from_csv.py \
    original_data/your_trades.csv \
    --verbose \
    --delay 2.0

# Step 2: 验证数据质量
python3 scripts/check_data_coverage.py

# Step 3: 重新评分
python3 scripts/score_positions.py --all --force

# Step 4: 分析结果
python3 scripts/analyze_scores.py
```

### 2. 定期更新数据

建议每周或每月更新一次：

```bash
# 更新所有股票的最新数据
python3 scripts/supplement_data_from_csv.py --from-db --rescore
```

### 3. 新导入交易后

每次导入新的交易CSV后：

```bash
# 导入交易
python3 scripts/import_trades.py new_trades.csv

# 自动补充新股票的市场数据
python3 scripts/supplement_data_from_csv.py new_trades.csv --rescore
```

---

## 技术细节

### 市场数据表结构

```python
class MarketData(Base):
    symbol: str           # 股票代码
    date: datetime        # 日期

    # OHLCV 数据
    open: Decimal         # 开盘价
    high: Decimal         # 最高价
    low: Decimal          # 最低价
    close: Decimal        # 收盘价
    volume: int           # 成交量

    # 技术指标
    rsi: Decimal          # RSI (14日)
    macd: Decimal         # MACD
    macd_signal: Decimal  # MACD 信号线
    macd_hist: Decimal    # MACD 柱状图
    bb_upper: Decimal     # 布林带上轨
    bb_middle: Decimal    # 布林带中轨
    bb_lower: Decimal     # 布林带下轨
    atr: Decimal          # ATR (14日)
    ma_5: Decimal         # 5日均线
    ma_20: Decimal        # 20日均线
    ma_50: Decimal        # 50日均线
```

### 数据来源

- **主要数据源**: yfinance (Yahoo Finance API)
- **备选方案**: Alpha Vantage, Polygon.io (需要配置)
- **缓存策略**: 3层缓存 (数据库 → 文件系统 → API)

### 性能考虑

- **批处理**: 默认每批 20 个股票
- **并发**: 支持多线程 (可配置)
- **缓存**: 已下载的数据不会重复获取
- **速率限制**: 自动延迟 (默认 1 秒)

---

## 总结

数据补充是提升交易质量评分准确性的关键步骤。使用自动化工具可以大大简化这一过程：

```bash
# 一键补充所有数据并重新评分
python3 scripts/supplement_data_from_csv.py \
    original_data/your_trades.csv \
    --verbose \
    --rescore
```

补充数据后，你将看到：
- ✅ 市场数据覆盖率从 15% 提升到 95%+
- ✅ 质量评分准确性显著提升
- ✅ 技术指标完整可用
- ✅ 分析结果更可信

---

**下一步**: [创建第一次数据补充](#使用自动化工具)
