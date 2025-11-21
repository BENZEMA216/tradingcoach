# Trading Coach - 交易复盘系统

AI驱动的个人交易复盘工具，帮助分析交易质量、识别模式、提升交易表现。

## 功能特性

- ✅ **交易数据导入**: 支持券商CSV导入，自动解析和清洗
- ✅ **交易配对**: FIFO算法，支持部分成交、做空、期权
- ✅ **技术指标分析**: RSI, MACD, 布林带, ATR, MA等
- ✅ **质量评分系统**: 四维度评分（入场、出场、趋势、风险管理）
- ✅ **市场环境分析**: 大盘背景、波动率、行业强弱
- 🔜 **AI增强分析**: 模式识别、建议生成（未来）

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/BENZEMA216/tradingcoach.git
cd tradingcoach

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

```bash
# 复制配置模板
cp config_template.py config.py

# 编辑config.py，填入API Keys
```

**重要**: 请参考 `project_docs/api_keys_guide.md` 申请API Keys

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 导入交易数据

```bash
python scripts/import_trades.py --file original_data/历史-保证金综合账户*.csv
```

## 项目文档

完整的技术文档位于 `project_docs/` 目录:

1. **PRD.md** - 产品需求文档
2. **technical_indicators_research.md** - 技术指标研究
3. **data_extensibility_design.md** - 数据扩展性设计
4. **technical_implementation_plan.md** - 技术实现方案
5. **api_keys_guide.md** - API申请指南

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| 数据库 | SQLite (MVP) → PostgreSQL (扩展) |
| ORM | SQLAlchemy 2.0+ |
| 数据处理 | pandas, numpy |
| 技术指标 | pandas-ta, TA-Lib (可选) |
| 市场数据 | yfinance, Alpha Vantage |
| Web框架 | Streamlit |
| 可视化 | Plotly, Streamlit |

## 可视化工具

### 启动 Dashboard

```bash
streamlit run visualization/dashboard.py
```

浏览器自动打开 `http://localhost:8501`

### 功能特性

- **📊 数据概览**: 查看交易统计、数据覆盖率、识别数据缺失
- **⭐ 质量评分**: 四维度评分分析、评分分布、盈亏关系
- **🔄 FIFO验证**: 可视化匹配过程、验证系统逻辑
- **📈 技术指标**: K线图、RSI/MACD/BB、交易点位标注

详细文档: [`visualization/README.md`](visualization/README.md)

## 当前状态

**版本**: v0.3.0-dev
**最后更新**: 2025-11-20
**当前分支**: `main`
**进度**: Phase 6/7 完成 ✅ (27/27 Phase 6 测试通过，548条市场数据指标已计算)

### 快速恢复工作

```bash
# 1. 查看当前状态
git status
git log --oneline -5

# 2. 预加载市场数据并计算指标（可选）
python3 scripts/preload_market_data.py --warmup-only --top-n 10
python3 scripts/calculate_indicators.py --all

# 3. 下一步：开始Phase 7 - 交易质量评分系统
# 详见下方"下一步待办事项"
```

---

## 开发进度

### ✅ Phase 1: 基础架构 (已完成)
**耗时**: 约3小时
**提交**: d4ff273

- [x] 创建完整项目目录结构
  - `src/` (9个子模块)
  - `scripts/`, `tests/`, `data/`, `cache/`, `logs/`
- [x] 配置文件和依赖管理
  - `requirements.txt` - 完整依赖列表
  - `config.py` - 配置管理（含API keys）
  - `config_template.py` - 配置模板
  - `.gitignore` - 更新排除规则
- [x] 项目文档
  - `README.md` - 项目说明
  - `api_keys_guide.md` - API申请指南
  - 3个技术设计文档
- [x] Git工作流设置

### ✅ Phase 2: 数据库Schema (已完成)
**耗时**: 约4小时
**提交**: d8d6aba

- [x] 数据库基础架构
  - `base.py` - 连接管理、Session工厂
- [x] Trade模型（交易记录）
  - 支持部分成交（order_quantity vs filled_quantity）
  - 支持卖空（4种交易方向）
  - 期权关联标的（underlying_symbol）
  - 完整费用明细（8种费用字段）
  - 6个复合索引优化
- [x] Position模型（持仓记录）
  - 盈亏计算（realized_pnl, net_pnl）
  - 风险指标（MAE, MFE, R:R）
  - 四维度质量评分字段
  - 自动等级分配（A/B/C/D/F）
- [x] MarketData模型（市场数据）
  - OHLCV数据
  - 20+技术指标缓存字段
  - 期权Greeks字段
  - 唯一约束（symbol+timestamp）
- [x] MarketEnvironment模型（市场环境）
  - 多市场指数（SPY, VIX, HSI等）
  - 趋势判断、行业表现
- [x] StockClassification模型（股票分类）
  - GICS行业分类（4级）
  - 市值分类、估值指标
  - 财务指标、财报日历
- [x] 数据库初始化脚本
  - `scripts/init_db.py`

**数据模型统计**:
- 模型数量: 5个核心表
- 总代码行数: ~1,400行
- 索引数量: 30+
- 枚举类型: 4个

### ✅ Phase 3: CSV导入模块 (已完成)
**实际耗时**: ~5小时
**提交**: 4f423f2
**测试通过率**: 100% (88/88 tests)

- [x] CSV解析器
  - UTF-8 BOM编码处理
  - 中文字段名映射（40+ 字段）
  - 数据验证和统计
- [x] 时区转换器
  - 美东时间 → UTC（支持EST/EDT）
  - 香港时间 → UTC (HKT)
  - 中国时间 → UTC (CST)
  - 处理夏令时/冬令时
- [x] Symbol分类器
  - 识别美股/港股/A股/期权/窝轮
  - 期权symbol解析（underlying, expiry, type, strike）
  - 窝轮代码解析（从名称提取信息）
- [x] 部分成交处理
  - 检测order_quantity vs filled_quantity
  - 标记部分成交记录
  - 实际数据检测到35个部分成交
- [x] 数据清洗器
  - 过滤撤单/失败订单
  - 数字格式处理（逗号、货币符号）
  - 交易方向标准化（中文→英文）
  - NaN值处理和类型转换
- [x] 导入脚本
  - `scripts/import_trades.py`
  - 批量导入（批次提交优化）
  - 进度显示和统计
  - 错误处理和日志
  - Dry-run模式支持

**实际成果**:
- 成功导入真实数据：816 CSV行 → 606 有效交易
- 88个单元测试（100% 通过率）
- 处理时间：0.18秒
- 代码量：~1,500行（含测试）

### ✅ Phase 4: FIFO交易配对算法 (已完成)
**实际耗时**: 约6小时
**提交**: [待记录]

- [x] FIFO配对器
  - 标准做多配对（buy → sell）
  - 做空配对（sell_short → buy_to_cover）
  - 部分成交配对处理
  - 多次建仓FIFO排序
- [x] 期权配对特殊处理
  - 期权到期自动平仓
  - 期权行权处理
- [x] 持仓计算
  - 盈亏计算（含费用）
  - 持仓时长计算
  - MAE/MFE计算
- [x] 单元测试
  - 完整配对场景测试
  - 真实数据验证（606交易 → 287持仓）

**实际成果**:
- 成功配对真实数据：606条交易 → 287个持仓
- 所有单元测试通过
- 处理时长计算、盈亏分析

### ✅ Phase 5: 市场数据获取和缓存 (已完成)
**实际耗时**: 约6小时
**提交**: [待记录]
**测试通过率**: 100% (98/98 tests)
**代码覆盖率**: 93%

- [x] BaseDataClient 抽象基类
  - 统一数据源接口
  - 自定义异常体系
  - 数据验证和标准化
- [x] YFinanceClient 实现
  - OHLCV数据获取
  - 滑动窗口限流（2000 req/hour）
  - 指数退避重试机制（3次）
  - 多市场symbol转换（US/HK/CN）
  - 批量获取优化
- [x] 三级缓存系统
  - **L1**: 内存缓存 (LRU淘汰，100条目)
  - **L2**: 数据库缓存 (market_data表，持久化)
  - **L3**: 磁盘缓存 (pickle文件，快速恢复)
  - 级联查找：L1 → L2 → L3 → API
  - 写穿策略：同时写入所有层级
- [x] BatchFetcher 批量获取器
  - 分析数据库交易记录
  - 智能日期范围计算（+200天用于指标）
  - 期权symbol解析（regex: `^([A-Z]+)(\d{6})([CP])(\d{8})$`）
  - 自动获取期权标的股票数据
  - 进度追踪（tqdm）
  - Cache预热功能
- [x] 预加载脚本
  - `scripts/preload_market_data.py`
  - 全量模式：分析所有交易
  - 预热模式：仅加载Top N symbol
  - 缓存统计展示

**代码统计**:
- 核心代码：458行
- 测试代码：98个测试
- 测试文件：4个
  - test_base_client.py (24 tests)
  - test_yfinance_client.py (29 tests)
  - test_cache_manager.py (25 tests)
  - test_batch_fetcher.py (20 tests)
- 覆盖率明细：
  - base_client.py: 90%
  - yfinance_client.py: 92%
  - cache_manager.py: 92%
  - batch_fetcher.py: 97%

**实际验证**:
- 成功预热Top 3 symbols（TSLL, AAPL, FIG）
- 获取745条市场数据记录
- 三级缓存全部工作正常
- 平均获取速度：~1.7秒/symbol

### ✅ Phase 6: 技术指标计算 (已完成)
**实际耗时**: 约3小时
**提交**: [待记录]
**测试通过率**: 100% (27/27 tests)

- [x] 纯pandas技术指标计算器
  - RSI (14天) - 使用EWM算法
  - MACD (12,26,9) - DIF, DEA, Histogram
  - Bollinger Bands (20天, 2σ) - 上中下轨
  - ATR (14天) - 真实波动幅度
  - MA系列 (5, 10, 20, 50, 200天) - 简单移动平均
- [x] 数据库集成
  - 更新market_data表13个指标字段
  - 批量更新优化（548条记录）
  - NaN值处理
- [x] 指标计算脚本
  - `scripts/calculate_indicators.py`
  - 支持指定symbols或全库计算（--all）
  - 进度显示和统计报告
  - 集成三级缓存系统
- [x] 单元测试
  - 27个测试用例（全部通过）
  - 涵盖所有5类指标
  - 数据库更新和批处理测试

**代码统计**:
- 核心代码：406行（calculator.py）
- 测试代码：27个测试（test_indicator_calculator.py）
- 脚本代码：254行（calculate_indicators.py）

**实际验证**:
- 成功计算AAPL和TSLL共548条记录的指标
- 处理时间：0.2秒（全库99个symbols）
- 所有13个指标字段成功写入数据库
- 无依赖TA-Lib或pandas-ta（纯pandas实现）

### 📋 Phase 7: 交易质量评分系统 (待开始)
**预计耗时**: 4-5小时

- [ ] 四维度评分器
  - 入场质量评分（30%）
  - 出场质量评分（25%）
  - 趋势质量评分（25%）
  - 风险管理评分（20%）
- [ ] 期权评分调整
  - Delta评估
  - IV Rank
  - Theta影响
- [ ] 综合评分
  - 加权计算
  - 等级分配（A/B/C/D/F）
- [ ] 评分报告生成

---

## 已完成工作清单

### 文档和配置
- ✅ 5个技术文档（PRD、技术指标研究、数据扩展性、实现方案、API指南）
- ✅ 完整的requirements.txt（核心依赖+开发工具）
- ✅ 配置管理系统（config.py + config_template.py）
- ✅ .gitignore规则（排除敏感数据、缓存、日志）
- ✅ README.md项目说明

### 数据库模型
- ✅ 5个核心表（trades, positions, market_data, market_environment, stock_classifications）
- ✅ 4个枚举类型（TradeDirection, TradeStatus, MarketType, PositionStatus）
- ✅ 30+索引（单列、复合、唯一约束）
- ✅ 完整的业务逻辑（property方法、计算方法）
- ✅ 序列化支持（to_dict方法）

### CSV导入和数据处理 (Phase 3)
- ✅ CSV解析器（支持中文字段、UTF-8 BOM、40+字段映射）
- ✅ 时区转换工具（美东/香港/中国 → UTC，夏令时处理）
- ✅ Symbol解析器（美股期权、港股股票/窝轮、A股识别）
- ✅ 数据清洗器（过滤、标准化、NaN处理、方向映射）
- ✅ 批量导入脚本（进度显示、错误处理、dry-run模式）
- ✅ 88个单元测试（100%通过率）
- ✅ 真实数据验证（816行→606交易，0.18秒）

### FIFO交易配对 (Phase 4)
- ✅ FIFO配对引擎（标准做多、做空配对）
- ✅ 部分成交处理
- ✅ 期权特殊处理（到期、行权）
- ✅ 盈亏计算（含完整费用）
- ✅ 持仓时长和风险指标
- ✅ 真实数据验证（606交易→287持仓）

### 市场数据获取和缓存 (Phase 5)
- ✅ BaseDataClient抽象接口（4个自定义异常）
- ✅ YFinanceClient实现（限流、重试、多市场）
- ✅ 三级缓存系统（L1内存+L2数据库+L3磁盘）
- ✅ BatchFetcher批量获取（智能分析、进度追踪）
- ✅ 期权symbol解析和标的关联
- ✅ 预加载脚本（全量/预热两种模式）
- ✅ 98个单元测试（93%代码覆盖率）
- ✅ 真实数据验证（Top 3 symbols, 745条记录）

### 技术指标计算 (Phase 6)
- ✅ 纯pandas指标计算器（无TA-Lib依赖）
- ✅ 5类核心指标（RSI, MACD, BB, ATR, MA）
- ✅ 13个指标字段（rsi_14, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, atr_14, ma_5, ma_10, ma_20, ma_50, ma_200）
- ✅ 数据库批量更新（548条记录）
- ✅ 指标计算脚本（CLI工具）
- ✅ 27个单元测试（100%通过率）
- ✅ 真实数据验证（AAPL + TSLL）

### 项目结构
```
tradingcoach/
├── src/                      # ✅ 已创建
│   ├── models/              # ✅ 5个模型完成
│   ├── data_sources/        # ✅ Phase 5完成（4个模块）
│   │   ├── base_client.py
│   │   ├── yfinance_client.py
│   │   ├── cache_manager.py
│   │   └── batch_fetcher.py
│   ├── indicators/          # ✅ Phase 6完成（calculator.py）
│   ├── importers/           # ✅ csv_parser.py, data_cleaner.py完成
│   ├── matchers/            # ✅ fifo_matcher.py完成
│   ├── analyzers/           # 待实现（Phase 7）
│   └── utils/               # ✅ timezone.py, symbol_parser.py完成
├── scripts/                 # ✅ 4个脚本完成
│   ├── init_db.py
│   ├── import_trades.py
│   ├── preload_market_data.py
│   ├── calculate_indicators.py  # ✅ 新增（Phase 6）
│   ├── supplement_data_from_csv.py  # ✅ 数据补充工具
│   ├── check_data_coverage.py      # ✅ 覆盖率检查
│   └── verify_indicators.py        # ✅ 指标验证
├── visualization/           # ✅ 新增：可视化模块
│   ├── dashboard.py        # 主入口
│   ├── pages/              # 4个页面
│   ├── components/         # 可复用组件
│   └── utils/              # 数据加载器
├── verification/            # ✅ 新增：FIFO验证工具
│   ├── verify_fifo.py
│   ├── verify_positions.py
│   └── compare_calculations.py
├── tests/unit/              # ✅ 125个单元测试（Phase 5-6）
├── project_docs/            # ✅ 5个文档完成
├── data/, cache/, logs/     # ✅ 目录已创建
└── 配置文件                  # ✅ 已创建
```

---

## 下一步待办事项

### 立即行动 🔥

1. **验证Phase 6功能** (5分钟) ✅
   ```bash
   # 运行Phase 6测试套件
   python3 -m pytest tests/unit/test_indicator_calculator.py -v
   # 结果：27/27 tests passed (100%)
   ```

2. **计算所有市场数据的技术指标** (2-5分钟)
   ```bash
   # 计算所有已缓存市场数据的技术指标
   python3 scripts/calculate_indicators.py --all

   # 或指定特定symbols
   python3 scripts/calculate_indicators.py --symbols AAPL,TSLL,TSLA
   ```

3. **准备Phase 7开发** (15分钟)
   - [ ] Review 交易质量评分需求 in PRD
   - [ ] 研究四维度评分算法
   - [ ] 设计评分器架构

### Phase 7 开发计划 📝

**目标**: 实现交易质量评分系统

**任务清单**:
1. 创建 `src/analyzers/quality_scorer.py` - 质量评分引擎
2. 实现四维度评分算法
   - 入场质量评分（30%权重）- 基于RSI, BB, 趋势
   - 出场质量评分（25%权重）- 止盈止损合理性
   - 趋势质量评分（25%权重）- MA趋势, MACD信号
   - 风险管理评分（20%权重）- ATR止损, 仓位管理
3. 综合评分和等级分配（A/B/C/D/F）
4. 更新positions表（质量评分字段）
5. 生成评分报告
6. 编写单元测试

**预计完成时间**: 4-5小时

---

## 开发规范

### Git工作流
```bash
# 功能分支命名
dev/feature-name     # 新功能
fix/bug-name         # Bug修复
docs/doc-name        # 文档更新

# 提交信息格式
feat(module): 描述    # 新功能
fix(module): 描述     # Bug修复
docs(module): 描述    # 文档更新
refactor(module): 描述 # 代码重构
```

### 每个Phase完成后
1. 运行测试验证功能
2. 提交代码到Git
3. 更新README.md进度
4. 合并到main分支（可选）

### 代码规范
- 使用Black格式化代码
- 使用flake8检查代码质量
- 添加类型注解（mypy）
- 编写docstring文档
- 单元测试覆盖率 > 80%

---

## 总体进度

**已完成**: Phase 1-6 (6/7)
**进度**: 85.7%
**累计工作时间**: 约27小时
**剩余预计时间**: 约4-5小时

**里程碑**:
- ✅ 数据库架构完成（5个表，30+索引）
- ✅ CSV导入系统完成（88个测试，100%通过）
- ✅ 真实数据验证（606条交易成功导入）
- ✅ FIFO配对算法完成（606交易→287持仓）
- ✅ 市场数据获取和缓存完成（98个测试，93%覆盖率）
- ✅ 技术指标计算完成（27个测试，548条记录已计算）
- 🚧 下一步：交易质量评分系统（Phase 7）

## 许可证

MIT License

## 联系方式

- GitHub: [@BENZEMA216](https://github.com/BENZEMA216)
- 项目链接: https://github.com/BENZEMA216/tradingcoach

---

**版本**: v0.3.0-dev | **最后更新**: 2025-11-20 | **Phase 6/7 完成** ✅
