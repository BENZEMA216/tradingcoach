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

## 当前状态

**版本**: v0.1.0-dev
**最后更新**: 2025-11-17
**当前分支**: `dev/foundation`
**进度**: Phase 3/7 完成 ✅ (88/88 测试通过，100% 通过率)

### 快速恢复工作

```bash
# 1. 切换到开发分支
git checkout dev/foundation

# 2. 查看当前状态
git status
git log --oneline -5

# 3. 下一步：开始Phase 4 - FIFO交易配对算法
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

### 📋 Phase 4: FIFO交易配对算法 (待开始)
**预计耗时**: 5-6小时

- [ ] FIFO配对器
  - 标准做多配对（buy → sell）
  - 做空配对（sell_short → buy_to_cover）
  - 部分成交配对处理
  - 多次建仓FIFO排序
- [ ] 期权配对特殊处理
  - 期权到期自动平仓
  - 期权行权处理
- [ ] 持仓计算
  - 盈亏计算（含费用）
  - 持仓时长计算
  - MAE/MFE计算（需分钟级数据）
- [ ] 单元测试
  - 10+配对场景测试
  - 真实数据验证

### 📋 Phase 5: 市场数据获取和缓存 (待开始)
**预计耗时**: 4-5小时

- [ ] yfinance客户端
  - OHLCV数据获取
  - 批量获取优化
  - 股票基本信息
  - 期权Greeks数据
- [ ] 期权标的关联
  - 同时获取期权和标的股票数据
- [ ] 三级缓存实现
  - L1: 内存缓存（dict）
  - L2: 数据库缓存（market_data表）
  - L3: 磁盘缓存（pickle文件）
- [ ] 批量预加载
  - 分析所有交易symbol
  - 批量获取日期范围数据
  - 限流和重试机制
- [ ] Alpha Vantage备用客户端

### 📋 Phase 6: 技术指标计算 (待开始)
**预计耗时**: 3-4小时

- [ ] pandas-ta计算器
  - RSI, MACD, Bollinger Bands
  - ATR, MA系列, ADX
  - 批量计算优化
- [ ] 指标缓存
  - 保存到market_data表
  - 避免重复计算
- [ ] 期权分析增强
  - Greeks计算/获取
  - 隐含波动率
- [ ] TA-Lib集成（可选）

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

### 项目结构
```
tradingcoach/
├── src/                      # ✅ 已创建
│   ├── models/              # ✅ 5个模型完成
│   ├── data_sources/        # 待实现
│   ├── indicators/          # 待实现
│   ├── cache/               # 待实现
│   ├── importers/           # ✅ csv_parser.py, data_cleaner.py完成
│   ├── matchers/            # 待实现
│   ├── analyzers/           # 待实现
│   └── utils/               # ✅ timezone.py, symbol_parser.py完成
├── scripts/                 # ✅ init_db.py, import_trades.py完成
├── tests/                   # ✅ 88个单元测试完成
├── project_docs/            # ✅ 5个文档完成
├── data/, cache/, logs/     # ✅ 目录已创建
└── 配置文件                  # ✅ 已创建
```

---

## 下一步待办事项

### 立即行动 🔥

1. **验证导入功能** (5分钟) ✅
   ```bash
   # 测试导入真实数据
   python3 scripts/import_trades.py --file original_data/历史-*.csv --dry-run
   ```

2. **运行测试套件** (2分钟) ✅
   ```bash
   # 验证所有测试通过
   python3 -m pytest tests/unit/ -v
   # 结果：88/88 tests passed (100%)
   ```

3. **准备Phase 4开发** (15分钟)
   - [ ] Review FIFO matching requirements in PRD
   - [ ] Design test cases for matching scenarios
   - [ ] Create Phase 4 development branch (optional)

### Phase 4 开发计划 📝

**目标**: 实现FIFO交易配对算法

**任务清单**:
1. 创建 `src/matchers/fifo_matcher.py` - FIFO配对引擎
2. 实现标准做多配对（buy → sell）
3. 实现做空配对（sell_short → buy_to_cover）
4. 处理部分成交配对
5. 期权特殊处理（到期、行权）
6. 盈亏计算（含费用）
7. MAE/MFE计算（需分钟级数据）
8. 编写10+配对场景测试

**预计完成时间**: 5-6小时

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

**已完成**: Phase 1-3 (3/7)
**进度**: 42.9%
**累计工作时间**: 约12小时
**剩余预计时间**: 约16-20小时

**里程碑**:
- ✅ 数据库架构完成（5个表，30+索引）
- ✅ CSV导入系统完成（88个测试，100%通过）
- ✅ 真实数据验证（606条交易成功导入）
- 🚧 下一步：FIFO配对算法

## 许可证

MIT License

## 联系方式

- GitHub: [@BENZEMA216](https://github.com/BENZEMA216)
- 项目链接: https://github.com/BENZEMA216/tradingcoach

---

**版本**: v0.1.0 | **最后更新**: 2025-11-16
