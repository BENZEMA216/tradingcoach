# 技术指标与交易质量评估研究

**文档版本**: v1.0
**创建日期**: 2025-11-13
**目的**: 研究如何使用技术指标评估交易质量，为后续实现交易评分系统提供理论基础

---

## 目录

1. [常用技术指标应用](#1-常用技术指标应用)
2. [交易质量评分体系](#2-交易质量评分体系)
3. [实际案例分析](#3-实际案例分析)
4. [技术实现路径](#4-技术实现路径)

---

## 1. 常用技术指标应用

### 1.1 RSI（相对强弱指标）- 进场/出场时机评估

**指标原理**:
- RSI = 100 - (100 / (1 + RS))，其中 RS = 平均涨幅 / 平均跌幅
- 标准周期：14天
- 取值范围：0-100

**进场质量评分标准**:

| RSI区间 | 做多评分 | 做空评分 | 说明 |
|---------|---------|---------|------|
| < 30 | 90-100 | 0-30 | 超卖区，做多时机优秀 |
| 30-40 | 70-89 | 30-50 | 接近超卖，做多良好 |
| 40-60 | 50-69 | 50-69 | 中性区域 |
| 60-70 | 30-50 | 70-89 | 接近超买，做空良好 |
| > 70 | 0-30 | 90-100 | 超买区，做空时机优秀 |

**出场质量评估**:
- 多头：RSI达到70+时止盈（90-100分）
- 空头：RSI回到30-时止盈（90-100分）
- 趋势反转：RSI形成M顶或W底形态

**代码示例**:
```python
def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def evaluate_rsi_entry_quality(entry_rsi, direction):
    """评估基于RSI的进场质量"""
    if direction == 'long':
        if entry_rsi < 30:
            return 95, "优秀进场：RSI超卖区买入"
        elif entry_rsi < 40:
            return 80, "良好进场：RSI接近超卖"
        elif entry_rsi < 50:
            return 65, "中等进场：RSI偏低但未超卖"
        elif entry_rsi < 60:
            return 50, "一般进场：RSI中性区域"
        else:
            return 30, "差进场：RSI偏高，追高风险"
    else:  # short
        if entry_rsi > 70:
            return 95, "优秀进场：RSI超买区做空"
        elif entry_rsi > 60:
            return 80, "良好进场：RSI接近超买"
        elif entry_rsi > 50:
            return 65, "中等进场：RSI偏高"
        else:
            return 30, "差进场：RSI偏低，不宜做空"
```

---

### 1.2 MACD（移动平均收敛发散）- 趋势把握评估

**指标原理**:
- DIF（差离值）= EMA(12) - EMA(26)
- DEA（信号线）= EMA(DIF, 9)
- MACD柱 = (DIF - DEA) × 2

**趋势识别质量**:

| 信号类型 | 条件 | 评分 | 说明 |
|---------|-----|------|------|
| 强势金叉 | DIF上穿DEA且DIF>0 | 90-100 | 零轴上方金叉，强看涨 |
| 普通金叉 | DIF上穿DEA但DIF<0 | 70-89 | 零轴下方金叉，中等看涨 |
| 死叉后买入 | DIF下穿DEA后买入 | 0-40 | 逆势操作 |

**趋势持续性评估**:
```python
def evaluate_macd_trend_quality(entry_macd, exit_macd, direction):
    """评估MACD趋势把握质量"""
    entry_signal = "golden_cross" if entry_macd['dif'] > entry_macd['dea'] else "death_cross"

    # 进场信号质量
    if direction == 'long':
        if entry_signal == 'golden_cross' and entry_macd['dif'] > 0:
            entry_score = 95  # 零轴上方金叉
        elif entry_signal == 'golden_cross':
            entry_score = 80  # 零轴下方金叉
        else:
            entry_score = 40  # 死叉后买入

    # 趋势持续性（持仓期间MACD是否保持有利方向）
    if direction == 'long':
        if exit_macd['dif'] > entry_macd['dif']:
            duration_score = 90  # 趋势加强
        elif exit_macd['dif'] > entry_macd['dea']:
            duration_score = 70  # 趋势保持
        else:
            duration_score = 40  # 趋势减弱

    return (entry_score + duration_score) / 2
```

---

### 1.3 布林带（Bollinger Bands）- 波动率位置评估

**指标原理**:
- 中轨：20日移动平均线（MA20）
- 上轨：中轨 + 2倍标准差
- 下轨：中轨 - 2倍标准差

**波动率位置质量评估**:

| 价格位置 | BB宽度 | 做多评分 | 策略 |
|---------|--------|---------|------|
| 下轨附近 | 收窄 | 90-100 | 低波动突破机会 |
| 下轨附近 | 正常 | 80-89 | 均值回归机会 |
| 中轨附近 | 任意 | 60-69 | 中性位置 |
| 上轨附近 | 扩张 | 0-40 | 追高风险 |

**代码示例**:
```python
def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """计算布林带"""
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    width = (upper - lower) / middle
    return {'upper': upper, 'middle': middle, 'lower': lower, 'width': width}

def evaluate_bollinger_position(price, bb_upper, bb_middle, bb_lower, bb_width, direction):
    """评估布林带位置质量"""
    # 计算价格在布林带中的相对位置（0-1）
    bb_position = (price - bb_lower) / (bb_upper - bb_lower)

    if direction == 'long':
        if bb_position < 0.1:  # 接近或突破下轨
            position_score = 95
        elif bb_position < 0.3:
            position_score = 80
        elif bb_position < 0.5:
            position_score = 65
        elif bb_position < 0.7:
            position_score = 45
        else:  # 上轨附近买入
            position_score = 25

    # 波动率评估（低波动率突破更有价值）
    if bb_width < 0.05:  # 极度收窄
        volatility_score = 90
    elif bb_width < 0.10:
        volatility_score = 70
    else:
        volatility_score = 50

    overall_score = position_score * 0.7 + volatility_score * 0.3
    return overall_score
```

---

### 1.4 成交量分析 - 信号强度验证

**量价配合质量评分**:

| 情况 | 评分 | 说明 |
|-----|------|------|
| 放量上涨（2倍+） | 90-100 | 强势确认 |
| 温和放量上涨（1.5倍） | 70-89 | 良好配合 |
| 缩量上涨（<0.8倍） | 30-50 | 动能不足 |
| 放量下跌 | 20-40 | 抛压沉重 |

**代码示例**:
```python
def evaluate_volume_quality(entry_volume, avg_volume_20d, price_change, direction):
    """评估成交量质量"""
    volume_ratio = entry_volume / avg_volume_20d

    # 量价配合评估
    if direction == 'long':
        if price_change > 0 and volume_ratio > 2.0:
            volume_score = 95  # 放量上涨
            signal_strength = 0.95
        elif price_change > 0 and volume_ratio > 1.5:
            volume_score = 80
            signal_strength = 0.80
        elif price_change > 0 and volume_ratio < 0.8:
            volume_score = 40  # 缩量上涨，动能不足
            signal_strength = 0.40
        elif price_change < 0 and volume_ratio > 2.0:
            volume_score = 30  # 放量下跌，风险
            signal_strength = 0.30

    return {
        'volume_score': volume_score,
        'signal_strength': signal_strength,
        'volume_ratio': volume_ratio
    }
```

---

### 1.5 移动平均线（MA）- 趋势跟随能力评估

**多周期均线系统**:
- 短期：MA5, MA10
- 中期：MA20, MA50
- 长期：MA100, MA200

**均线排列评分**:

| 均线状态 | 评分 | 说明 |
|---------|------|------|
| 完美多头排列 | 90-100 | MA5>MA10>MA20>MA50>MA200 |
| 部分多头排列 | 70-89 | 主要均线多头 |
| 价格在MA20上方 | 60-79 | 中期趋势支持 |
| 价格在MA50下方 | 0-50 | 逆趋势操作 |

---

### 1.6 ATR（真实波动幅度）- 风险管理评估

**ATR指标原理**:
- ATR = 过去N期真实波幅的移动平均（通常N=14）
- 真实波幅 = max(高-低, |高-昨收|, |低-昨收|)

**止损设置合理性**:

| 止损距离 | 评分 | 说明 |
|---------|------|------|
| 1.5-2.5倍ATR | 90-100 | 理想止损距离 |
| 1.0-1.5倍ATR | 70-89 | 略紧但可接受 |
| < 1.0倍ATR | 0-50 | 容易被正常波动止损 |
| > 3.0倍ATR | 30-60 | 止损过宽，风险大 |

**代码示例**:
```python
def evaluate_atr_risk_management(entry_price, stop_loss, take_profit, atr, position_size, account_value):
    """评估基于ATR的风险管理质量"""
    # 计算止损距离（以ATR为单位）
    stop_distance = abs(entry_price - stop_loss)
    stop_atr_ratio = stop_distance / atr

    # 计算风险回报比
    if take_profit:
        profit_distance = abs(take_profit - entry_price)
        risk_reward_ratio = profit_distance / stop_distance
    else:
        risk_reward_ratio = None

    # 计算账户风险百分比
    position_value = position_size * entry_price
    max_loss = position_size * stop_distance
    account_risk_pct = (max_loss / account_value) * 100

    # 止损设置评分
    if 1.5 <= stop_atr_ratio <= 2.5:
        stop_score = 95
    elif 1.0 <= stop_atr_ratio < 1.5:
        stop_score = 80
    elif stop_atr_ratio < 1.0:
        stop_score = 40  # 止损过紧
    else:
        stop_score = 50  # 止损过宽

    # 风险回报比评分
    if risk_reward_ratio:
        if risk_reward_ratio >= 3.0:
            rr_score = 100
        elif risk_reward_ratio >= 2.0:
            rr_score = 90
        elif risk_reward_ratio >= 1.5:
            rr_score = 75
        else:
            rr_score = 40
    else:
        rr_score = 50  # 未设置止盈

    # 账户风险评分
    if account_risk_pct <= 1.0:
        risk_pct_score = 100
    elif account_risk_pct <= 2.0:
        risk_pct_score = 85
    elif account_risk_pct <= 3.0:
        risk_pct_score = 70
    else:
        risk_pct_score = 40  # 单笔风险过大

    overall_score = (stop_score * 0.4 + rr_score * 0.3 + risk_pct_score * 0.3)

    return {
        'risk_score': overall_score,
        'stop_atr_ratio': stop_atr_ratio,
        'risk_reward_ratio': risk_reward_ratio,
        'account_risk_pct': account_risk_pct
    }
```

---

## 2. 交易质量评分体系

### 2.1 四维度评分框架

**综合评分公式**:
```
交易总分 = 进场质量(30%) + 出场质量(25%) + 趋势把握(25%) + 风险管理(20%)
```

### 2.2 进场质量评分（0-100分，权重30%）

**组成部分**:
- 技术指标配合度（40%）：RSI、MACD、布林带综合评分
- 支撑/阻力位置（30%）：进场价格相对关键位置
- 成交量确认（20%）：量价配合情况
- 市场环境（10%）：大盘趋势、VIX波动率

**评分标准**:
- 90-100分（A）：多个指标共振，进场时机优秀
- 70-89分（B）：大部分指标支持，良好进场
- 50-69分（C）：部分指标支持，一般进场
- 0-49分（D/F）：技术面不支持，差进场

---

### 2.3 出场质量评分（0-100分，权重25%）

**组成部分**:
- 出场时机（40%）：基于技术指标的出场时机评估
- 盈亏目标达成（30%）：是否达到预设目标
- 止损执行（20%）：止损纪律性
- 持仓时间合理性（10%）：持仓时长与策略的匹配度

**关键指标**:
- 利润捕获率 = 实际盈亏 / 最大浮盈（MFE）
- 止损执行率 = 实际止损 / 计划止损
- 持仓效率 = 日均收益率

---

### 2.4 趋势把握评分（0-100分，权重25%）

**组成部分**:
- 趋势方向一致性（40%）：交易方向与多个趋势指标的一致性
- 趋势强度（30%）：ADX、均线分离度、价格动量
- 趋势持续性（30%）：持仓期间趋势是否保持

**关键指标**:
- ADX > 25：强趋势
- 均线多头/空头排列
- MACD柱状图持续性

---

### 2.5 风险管理评分（0-100分，权重20%）

**组成部分**:
- 计划风险收益比（40%）：进场前设定的RR比
- 实际风险收益比（30%）：MAE vs MFE
- 仓位管理（30%）：仓位大小、账户风险百分比

**优秀标准**:
- RR比 ≥ 2:1
- 单笔账户风险 ≤ 2%
- 止损距离 = 1.5-2倍ATR

---

### 2.6 等级划分

| 总分范围 | 等级 | 说明 |
|---------|------|------|
| 95-100 | A+ | 卓越交易，值得复制 |
| 90-94 | A | 优秀交易 |
| 85-89 | A- | 优秀偏上 |
| 80-84 | B+ | 良好交易 |
| 75-79 | B | 良好 |
| 70-74 | B- | 良好偏下 |
| 65-69 | C+ | 中等偏上 |
| 60-64 | C | 中等 |
| 55-59 | C- | 中等偏下 |
| 50-54 | D | 需改进 |
| 0-49 | F | 差，需深刻反思 |

---

## 3. 实际案例分析

### 3.1 案例1：优秀交易（A-级，87分）

**交易详情**:
- 标的：AAPL
- 方向：做多
- 进场：2024-10-15, $170.50
- 出场：2024-10-25, $178.20
- 盈亏：+$770 (+4.52%)
- 持仓：10天

**技术指标评估**:

**进场质量：88/100 (A-)**
- RSI：28.5（超卖区）→ 95分 ✓ 在超卖区买入，进场时机优秀
- MACD：金叉 + DIF上穿0轴 → 90分 ✓ 强势金叉信号
- 布林带：价格在下轨 → 92分 ✓ 均值回归机会
- 成交量：放量20% → 75分 ✓ 温和放量确认
- 均线：价格接近MA50支撑 → 85分 ✓ 在关键支撑位买入

**出场质量：82/100 (B+)**
- 出场时机：RSI 68 → 75分 ⚠ RSI接近超买但未极端
- 目标达成：4.52% vs 目标5% → 90分 ✓ 达到90%盈利目标
- 持仓效率：日均0.45% → 85分 ✓ 持仓效率良好
- 利润保护：捕获75%潜在利润 → 80分 ✓ 最高曾达6%，在回调前止盈

**趋势把握：90/100 (A)**
- 趋势方向：三重确认 → 95分 ✓ MA多头排列、MACD金叉、价格上升
- 趋势强度：ADX 32 → 88分 ✓ 强趋势环境
- 趋势持续：持仓期间持续上涨 → 88分 ✓ 趋势判断准确

**风险管理：85/100 (B+)**
- 计划RR比：2.5:1 → 90分 ✓ 止损-2%, 目标+5%
- 实际RR比：MAE -0.5%, MFE +6% → 92分 ✓ 实际表现优于预期
- 仓位管理：15%仓位，风险1.2% → 75分 ✓ 仓位适中

**综合评分：87/100 (A-)**

**优势**:
- 进场时机把握精准，多指标共振
- 趋势判断准确，顺势而为
- 风险管理严格，RR比合理

**可改进**:
- 出场略早，可等待RSI>70或MACD死叉信号
- 可考虑分批止盈，保留部分仓位让利润奔跑

---

### 3.2 案例2：中等交易（C-级，58分）

**交易详情**:
- 标的：TSLA
- 方向：做多
- 进场：2024-09-20, $245.00
- 出场：2024-09-27, $238.50
- 盈亏：-$325 (-2.65%)
- 持仓：7天

**技术指标评估**:

**进场质量：52/100 (D)**
- RSI：72.3（超买区）→ 30分 ✗ 在超买区追高买入
- MACD：柱状图缩小 → 55分 ⚠ 动能减弱
- 布林带：价格突破上轨 → 40分 ✗ 在上轨外买入，追高风险
- 成交量：缩量15% → 40分 ✗ 缩量上涨，动能不足
- 均线：价格远离MA20达8% → 45分 ⚠ 乖离率过大

**出场质量：75/100 (B)**
- 出场时机：RSI回落至45, MACD死叉 → 80分 ✓ 趋势转弱时及时出场
- 止损执行：-2.65% vs 预设-3% → 85分 ✓ 在止损范围内出场
- 持仓效率：7天快速止损 → 80分 ✓ 未长期扛单

**趋势把握：45/100 (D)**
- 趋势方向：逆短期回调买入 → 35分 ✗ 追涨买入后立即回调
- 趋势强度：ADX 28但开始回落 → 50分 ⚠ 趋势强度减弱

**风险管理：68/100 (C)**
- 计划RR比：1.33:1 → 70分 ⚠ 勉强可接受
- 实际RR比：MAE -4%, MFE +1.5% → 45分 ✗ 买入后立即浮亏
- 仓位管理：20%仓位，风险1.8% → 75分 ✓ 基本合理

**综合评分：58/100 (C-)**

**问题**:
- 在超买区追高买入，违背"低买高卖"原则
- 进场时多个指标显示风险（RSI超买、缩量、乖离率大）

**做得好**:
- 止损执行坚决，未让亏损扩大
- 快速认错，避免长期扛单

---

### 3.3 案例3：差交易（F级，25分）

**交易详情**:
- 标的：NVDA
- 方向：做空
- 进场：2024-08-10, $420.00
- 出场：2024-08-28, $487.00
- 盈亏：-$1,340 (-15.95%)
- 持仓：18天

**技术指标评估**:

**进场质量：28/100 (F)**
- RSI：35 → 45分 ⚠ RSI不支持做空
- MACD：强势金叉 → 20分 ✗ 完全逆势做空
- 布林带：价格在中轨上方，带宽扩大 → 25分 ✗ 趋势突破中
- 成交量：连续放量 → 15分 ✗ 放量上涨，多头强势
- 均线：完美多头排列 → 10分 ✗ 最强势时做空

**出场质量：35/100 (F)**
- 出场时机：亏损-16%才止损 → 25分 ✗ 止损过晚
- 止损执行：预设-5%，实际-16% → 15分 ✗ 严重违反纪律
- 持仓效率：18天扛单 → 20分 ✗ 长期扛单

**趋势把握：15/100 (F)**
- 趋势方向：完全逆强势上升趋势 → 10分 ✗ 致命错误
- 趋势强度：ADX 45 → 15分 ✗ 逆极强趋势
- 趋势持续：持仓期间趋势持续加强 → 20分 ✗ 持续逆势扛单

**风险管理：22/100 (F)**
- 计划RR比：2:1 → 50分 ⚠ 做空RR比尚可
- 实际RR比：MAE -18%, MFE +2% → 0分 ✗ 完全失败
- 仓位管理：25%仓位 → 40分 ⚠ 仓位过大，逆势应轻仓
- 止损纪律：完全违反 → 0分 ✗ 计划-5%，实际-16%

**综合评分：25/100 (F)**

**严重问题**:
- 【致命错误】完全逆趋势做空，所有技术指标都显示强势上涨
- 【纪律崩溃】止损从-5%扩大到-16%，严重违反交易纪律
- 【情绪化交易】在亏损时不断扩大止损，陷入赌徒心态
- 【仓位管理失误】逆势操作使用25%重仓

**深层原因**:
- 主观臆断：认为股价"涨太多了"应该下跌
- 逆势操作：在所有指标看涨时做空
- 止损失控：不断调整止损，从-5%放宽到-16%
- 赌徒心态：不愿承认错误，希望"扛回来"

**强烈建议**:
1. 建立铁的止损纪律，-3到-5%必须离场
2. 永远顺势交易，均线多头排列时不做空
3. 逆势操作（如果一定要做）最多5%仓位
4. 发现判断失误立即离场
5. 接受"错过"比"做错"好

---

## 4. 技术实现路径

### 4.1 数据需求

**必需数据**:
1. 历史OHLCV数据（开高低收量）
2. 订单执行数据（已有，来自CSV）
3. 账户资金数据（用于计算仓位比例）

**可选数据**:
4. VIX波动率指数
5. 大盘指数（SPY、QQQ）
6. 行业ETF数据
7. 财报日期
8. 新闻事件

---

### 4.2 技术指标计算库

**选项1：TA-Lib**（推荐）
```bash
# 安装
pip install TA-Lib

# 使用示例
import talib
rsi = talib.RSI(close_prices, timeperiod=14)
macd, signal, hist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
upper, middle, lower = talib.BBANDS(close_prices, timeperiod=20)
```

优点：
- 性能极高（C语言实现）
- 指标全面（150+种）
- 行业标准

缺点：
- 安装复杂（需要编译）
- macOS/Linux需要额外配置

**选项2：pandas-ta**（备选）
```bash
pip install pandas-ta

# 使用示例
import pandas_ta as ta
df.ta.rsi(length=14, append=True)
df.ta.macd(fast=12, slow=26, signal=9, append=True)
df.ta.bbands(length=20, std=2, append=True)
```

优点：
- 安装简单，纯Python
- DataFrame集成好
- 易于扩展

缺点：
- 性能略低于TA-Lib
- 某些高级指标缺失

---

### 4.3 行情数据获取方案

**推荐方案：yfinance（免费）**
```python
import yfinance as yf

# 获取历史数据
ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1y", interval="1d")

# 包含：Open, High, Low, Close, Volume
```

优点：
- 完全免费
- 数据全面（美股、港股、加密货币）
- 无需API key
- Python支持好

缺点：
- 无官方支持
- 稳定性一般（偶尔被限流）
- 实时数据延迟

**备选方案：Alpha Vantage**
```python
from alpha_vantage.timeseries import TimeSeries

ts = TimeSeries(key='YOUR_API_KEY', output_format='pandas')
data, meta = ts.get_daily(symbol='AAPL', outputsize='full')
```

优点：
- 官方API
- 数据质量高
- 支持技术指标直接获取

缺点：
- 免费版限制严格（5次/分钟，500次/天）
- 速度较慢

---

### 4.4 实施步骤

**Phase 1：基础数据层**（MVP已完成）
- ✅ CSV订单数据导入
- ✅ 交易配对
- ✅ 基础盈亏指标

**Phase 2：技术指标集成**（下一步）
1. 为每笔trade获取进场和出场时的行情数据
2. 计算技术指标（RSI、MACD、布林带等）
3. 存储到market_data表

**Phase 3：交易质量评分**（第3步）
1. 实现四维度评分算法
2. 为每笔trade计算quality_score
3. 存储详细评分到trade_quality_details表

**Phase 4：可视化和报告**（第4步）
1. 交易质量仪表盘
2. 单笔交易详细分析页面
3. 改进建议生成

---

### 4.5 性能优化

**缓存策略**:
- 行情数据按日缓存（避免重复请求API）
- 技术指标预计算并存储
- 使用SQLite JSON字段存储完整指标数据

**批量处理**:
- 按标的批量获取行情数据
- 批量计算技术指标
- 批量插入数据库

**增量更新**:
- 只获取新增交易的行情数据
- 已有数据不重复计算

---

## 5. 下一步行动

### 5.1 立即可做（不依赖外部数据）

1. ✅ 完善数据库Schema（已包含技术指标预留字段）
2. ✅ 实现基础指标计算
3. ⏭ 设计交易质量评分算法框架

### 5.2 需要行情数据后才能做

1. ⏭ 集成yfinance获取历史行情
2. ⏭ 计算技术指标（RSI、MACD、布林带等）
3. ⏭ 实现交易质量四维度评分
4. ⏭ 生成交易质量报告

### 5.3 优先级排序

**P0（今天完成）**:
- 数据库Schema设计（含技术指标预留）
- CSV数据导入
- 交易配对
- 基础指标计算

**P1（本周完成）**:
- 集成yfinance
- 技术指标计算
- 交易质量评分算法

**P2（下周完成）**:
- 可视化仪表盘
- 单笔交易详细分析
- AI洞察生成

---

## 附录：技术指标公式汇总

### RSI
```
RSI = 100 - (100 / (1 + RS))
RS = 平均涨幅 / 平均跌幅
```

### MACD
```
DIF = EMA(12) - EMA(26)
DEA = EMA(DIF, 9)
MACD = (DIF - DEA) × 2
```

### 布林带
```
中轨 = MA(20)
上轨 = 中轨 + 2 × STD(20)
下轨 = 中轨 - 2 × STD(20)
```

### ATR
```
TR = max(高-低, |高-昨收|, |低-昨收|)
ATR = MA(TR, 14)
```

### ADX
```
+DI = 100 × MA(+DM, 14) / ATR
-DI = 100 × MA(-DM, 14) / ATR
DX = 100 × |+DI - -DI| / (+DI + -DI)
ADX = MA(DX, 14)
```

---

**文档结束**

最后更新：2025-11-13
