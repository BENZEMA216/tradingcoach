# 技术指标全面扩展计划

## 需求总结

- **覆盖范围**: 全部指标类型（成交量、动量、波动率、趋势）
- **用户定位**: 支持多种交易风格（趋势跟踪、波段、日内、期权）
- **多周期支持**: 日线/周线/月线
- **期权指标**: 需要Greeks和IV
- **评分集成**: 新指标全面集成到评分系统

---

## 当前已有指标（23个字段）

| 类别 | 指标 | 字段 |
|------|------|------|
| 动量 | RSI, Stochastic | `rsi_14`, `stoch_k`, `stoch_d` |
| 趋势 | MACD | `macd`, `macd_signal`, `macd_hist` |
| 趋势 | ADX+DI | `adx`, `plus_di`, `minus_di` |
| 趋势 | MA/EMA | `ma_5/10/20/50/200`, `ema_12/26` |
| 波动 | 布林带, ATR | `bb_*`, `atr_14` |
| 成交量 | Volume SMA | `volume_sma_20` |

---

## 新增指标计划（35+个字段）

### 第一批：成交量分析（6个字段）

| 指标 | 字段名 | 公式概要 | 评分用途 |
|------|--------|---------|---------|
| **OBV** | `obv` | 累积量（上涨+，下跌-） | 量价背离检测 |
| **VWAP** | `vwap` | Σ(价格×量)/Σ量 | 日内基准价、机构行为 |
| **MFI** | `mfi_14` | 量加权RSI | 量价超买超卖 |
| **A/D Line** | `ad_line` | CLV×Volume累积 | 主力吸筹/派发 |
| **CMF** | `cmf_20` | A/D的20日均值 | 短期资金流向 |
| **Volume Ratio** | `volume_ratio` | 当日量/均量 | 异常成交量检测 |

### 第二批：动量指标（6个字段）

| 指标 | 字段名 | 公式概要 | 评分用途 |
|------|--------|---------|---------|
| **CCI** | `cci_20` | (TP-MA)/MAD | 周期性超买超卖 |
| **Williams %R** | `willr_14` | (最高-收盘)/(最高-最低) | 敏感超买超卖 |
| **ROC** | `roc_12` | (今-N日前)/N日前×100 | 动量强度 |
| **Momentum** | `mom_10` | 今-N日前 | 价格动量 |
| **Ultimate Osc** | `uo` | 加权多周期动量 | 综合动量信号 |
| **RSI Divergence** | `rsi_div` | 价格/RSI背离检测 | 反转预警 |

### 第三批：波动率指标（8个字段）

| 指标 | 字段名 | 公式概要 | 评分用途 |
|------|--------|---------|---------|
| **Keltner Upper** | `kc_upper` | EMA + 2×ATR | 挤压信号上轨 |
| **Keltner Lower** | `kc_lower` | EMA - 2×ATR | 挤压信号下轨 |
| **Donchian Upper** | `dc_upper` | N日最高 | 突破上轨 |
| **Donchian Lower** | `dc_lower` | N日最低 | 突破下轨 |
| **Historical Vol** | `hvol_20` | 20日收益率标准差 | 期权分析 |
| **ATR%** | `atr_pct` | ATR/价格×100 | 标准化波动率 |
| **BB Squeeze** | `bb_squeeze` | BB在KC内 | 挤压信号 |
| **Volatility Rank** | `vol_rank` | 当前波动率百分位 | 波动率环境 |

### 第四批：趋势指标（10个字段）

| 指标 | 字段名 | 公式概要 | 评分用途 |
|------|--------|---------|---------|
| **Ichimoku 转换线** | `ichi_tenkan` | (9日高+9日低)/2 | 短期趋势 |
| **Ichimoku 基准线** | `ichi_kijun` | (26日高+26日低)/2 | 中期趋势 |
| **Ichimoku 先行A** | `ichi_senkou_a` | (转换+基准)/2 | 云图上沿 |
| **Ichimoku 先行B** | `ichi_senkou_b` | (52日高+52日低)/2 | 云图下沿 |
| **Ichimoku 迟行** | `ichi_chikou` | 收盘价位移26日 | 趋势确认 |
| **Parabolic SAR** | `psar` | 抛物线止损点 | 止损追踪 |
| **SuperTrend** | `supertrend` | ATR通道趋势 | 趋势方向 |
| **SuperTrend Dir** | `supertrend_dir` | 1=多头/-1=空头 | 趋势信号 |
| **TRIX** | `trix` | 三重EMA变化率 | 过滤噪音趋势 |
| **DPO** | `dpo` | 去趋势价格 | 周期分析 |

### 第五批：期权专属（8个字段）

| 指标 | 字段名 | 数据来源 | 评分用途 |
|------|--------|---------|---------|
| **Delta** | `delta` | 外部API/计算 | 方向敏感度 |
| **Gamma** | `gamma` | 外部API/计算 | Delta变化率 |
| **Theta** | `theta` | 外部API/计算 | 时间衰减 |
| **Vega** | `vega` | 外部API/计算 | 波动率敏感度 |
| **IV** | `implied_vol` | 外部API | 隐含波动率 |
| **IV Rank** | `iv_rank` | 计算 | IV历史百分位 |
| **IV Percentile** | `iv_percentile` | 计算 | IV天数百分位 |
| **Put/Call Ratio** | `pcr` | 外部API | 市场情绪 |

---

## 实施步骤

### Step 1: 数据库迁移
- 文件: `src/models/market_data.py`
- 添加38个新字段到 `market_data` 表
- 使用 Alembic 生成迁移脚本

### Step 2: 指标计算引擎扩展
- 文件: `src/indicators/calculator.py`
- 实现各类指标计算方法
- 更新 `calculate_all_indicators()` 入口

### Step 3: 多周期支持
- 文件: `src/indicators/timeframe_converter.py`
- 扩展周线/月线指标计算
- 添加周期参数到计算方法

### Step 4: 期权数据集成
- 新文件: `src/data_sources/options_client.py`
- 获取期权链数据（yfinance/polygon）
- Greeks计算或API获取

### Step 5: 评分系统集成
- 文件: `src/analyzers/quality_scorer.py`
- 添加新指标评分标准
- 调整权重分配

### Step 6: API和前端
- 更新 `backend/app/schemas/market_data.py`
- 更新 API 端点返回新字段
- 前端图表支持新指标展示

### Step 7: 重新计算历史数据
- 脚本: `scripts/calculate_indicators.py`
- 为所有历史数据计算新指标

---

## 核心文件清单

| 文件路径 | 修改类型 |
|---------|---------|
| `src/models/market_data.py` | 添加字段 |
| `src/indicators/calculator.py` | 添加计算方法 |
| `src/indicators/timeframe_converter.py` | 多周期支持 |
| `src/data_sources/options_client.py` | 新建 |
| `src/analyzers/quality_scorer.py` | 评分集成 |
| `backend/app/schemas/market_data.py` | Schema扩展 |
| `backend/app/api/v1/endpoints/market_data.py` | API更新 |
| `scripts/calculate_indicators.py` | 批量计算 |
| Alembic迁移文件 | 数据库变更 |

---

## 评分系统集成方案

### 进场质量增强
- OBV背离检测 (+5%权重)
- MFI超买超卖 (+3%权重)
- Ichimoku云图位置 (+5%权重)
- 挤压信号检测 (+2%权重)

### 出场质量增强
- Parabolic SAR止损 (+5%权重)
- SuperTrend信号 (+3%权重)
- CCI极值区域 (+2%权重)

### 趋势把握增强
- Ichimoku多维确认 (+5%权重)
- 多周期趋势一致性 (+5%权重)

### 风险管理增强
- 波动率环境评估 (+3%权重)
- ATR%标准化 (+2%权重)
