# indicators - 技术指标计算层

使用纯 pandas 实现常用技术指标计算。

## 设计思路

### 为什么不用 TA-Lib?

1. **跨平台兼容**: pandas 纯 Python，无 C 依赖
2. **透明可控**: 公式清晰，便于调试
3. **自定义灵活**: 易于修改参数和算法

### 指标分类

| 类别 | 指标 | 用途 |
|------|------|------|
| 趋势 | MA, EMA, ADX | 判断趋势方向和强度 |
| 动量 | RSI, MACD, Stochastic | 判断超买超卖 |
| 波动 | ATR, Bollinger Bands | 衡量波动性 |

## 文件说明

| 文件 | 说明 | 行数 |
|------|------|------|
| `calculator.py` | 指标计算器主类 | ~660 |
| `timeframe_converter.py` | 时间周期转换 | ~100 |

## IndicatorCalculator

### 支持的指标

| 指标 | 方法 | 参数 | 输出 |
|------|------|------|------|
| RSI | `calculate_rsi()` | period=14 | 0-100 |
| MACD | `calculate_macd()` | fast=12, slow=26, signal=9 | macd, signal, histogram |
| Bollinger | `calculate_bollinger_bands()` | period=20, std=2.0 | upper, middle, lower |
| ATR | `calculate_atr()` | period=14 | ATR值 |
| MA | `calculate_ma()` | periods=[5,10,20,50,200] | MA系列 |
| EMA | `calculate_ema()` | periods=[12,26] | EMA系列 |
| ADX | `calculate_adx()` | period=14 | adx, +DI, -DI |
| Stochastic | `calculate_stochastic()` | k=14, d=3 | %K, %D |

### 使用示例

```python
from src.indicators.calculator import IndicatorCalculator

calculator = IndicatorCalculator()

# 计算单个指标
rsi = calculator.calculate_rsi(df, period=14)
macd = calculator.calculate_macd(df)  # 返回 dict

# 计算所有指标（推荐）
df_with_indicators = calculator.calculate_all_indicators(df)

# 更新数据库
updated = calculator.update_market_data_indicators(
    session, 'AAPL', df_with_indicators
)
```

## 指标公式

### RSI (Relative Strength Index)

```
RSI = 100 - (100 / (1 + RS))
RS = 平均涨幅(EMA) / 平均跌幅(EMA)
```

**解读**:
- RSI > 70: 超买区域
- RSI < 30: 超卖区域
- RSI 50: 中性

### MACD (Moving Average Convergence Divergence)

```
DIF = EMA(12) - EMA(26)
DEA = EMA(DIF, 9)
MACD柱 = (DIF - DEA) × 2
```

**解读**:
- DIF 上穿 DEA: 金叉，看涨
- DIF 下穿 DEA: 死叉，看跌
- 柱状图转正/负: 趋势确认

### Bollinger Bands

```
中轨 = SMA(20)
上轨 = 中轨 + 2 × STD(20)
下轨 = 中轨 - 2 × STD(20)
```

**解读**:
- 价格触及上轨: 可能超买
- 价格触及下轨: 可能超卖
- 带宽收窄: 波动率降低，可能即将突破

**额外指标**:
```
BB Width = (上轨 - 下轨) / 中轨 × 100  # 波动率
BB %B = (Close - 下轨) / (上轨 - 下轨)  # 相对位置
```

### ATR (Average True Range)

```
TR = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
ATR = EMA(TR, 14)
```

**用途**:
- 止损距离计算 (通常 2-3 × ATR)
- 波动性筛选
- 仓位管理

### ADX (Average Directional Index)

```
+DM = High - PrevHigh (若为正且 > |-DM|)
-DM = PrevLow - Low (若为正且 > |+DM|)
+DI = 100 × EMA(+DM) / ATR
-DI = 100 × EMA(-DM) / ATR
DX = 100 × |+DI - -DI| / (+DI + -DI)
ADX = EMA(DX, 14)
```

**解读**:
- ADX > 25: 强趋势
- ADX < 20: 弱趋势/震荡
- +DI > -DI: 上升趋势
- -DI > +DI: 下降趋势

### Stochastic

```
%K = 100 × (Close - LowestLow) / (HighestHigh - LowestLow)
%D = SMA(%K, 3)
```

**解读**:
- %K < 20: 超卖
- %K > 80: 超买
- %K 上穿 %D: 金叉

## 计算流程

```
┌─────────────────────────────────────────────────────────────┐
│                    OHLCV DataFrame                           │
│  columns: Open, High, Low, Close, Volume                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              calculate_all_indicators()                      │
│                                                              │
│  ├── calculate_rsi()         → rsi_14                       │
│  ├── calculate_macd()        → macd, macd_signal, macd_hist │
│  ├── calculate_bollinger()   → bb_upper, bb_middle, bb_lower│
│  ├── calculate_atr()         → atr_14                       │
│  ├── calculate_adx()         → adx, plus_di, minus_di       │
│  ├── calculate_stochastic()  → stoch_k, stoch_d             │
│  ├── calculate_ma()          → ma_5, ma_10, ma_20, ma_50... │
│  └── calculate_ema()         → ema_12, ema_26               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              DataFrame with All Indicators                   │
│  25+ 新增列                                                  │
└─────────────────────────────────────────────────────────────┘
```

## 数据库更新

```python
# 批量计算并更新
results = calculator.batch_calculate_and_update(
    session=session,
    symbols=['AAPL', 'TSLA', 'NVDA'],
    from_cache_func=cache.get_dataframe
)

# 结果: {symbol: updated_count}
print(results)
# {'AAPL': 252, 'TSLA': 252, 'NVDA': 252}
```

## 注意事项

### NaN 值处理

前 N 个数据点因历史数据不足会产生 NaN：
- RSI(14): 前 14 个为 NaN
- MA(200): 前 200 个为 NaN
- MACD: 前 26 个为 NaN

### 数据要求

- 最少 200+ 条数据才能计算完整指标
- 数据需按时间升序排列
- 不能有缺失的交易日

### 性能优化

- 使用向量化运算（pandas/numpy）
- 避免逐行迭代
- 批量更新数据库
