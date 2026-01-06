# Phase 4 FIFO Matching - 单元测试文档

本目录包含 Phase 4 FIFO交易配对算法的完整单元测试。

## 📁 测试文件

### 1. test_trade_quantity.py
**测试对象**: `src/matchers/trade_quantity.py` - TradeQuantity 类

**测试覆盖** (29个测试用例):
- ✅ 初始化和验证
- ✅ 数量消耗机制 (consume)
- ✅ 费用分摊计算
- ✅ 完全消耗检查
- ✅ 已消耗数量追踪
- ✅ 字符串表示
- ✅ 边界情况（单股、大数量、精度）

**关键测试场景**:
- 部分成交追踪
- 多次配对的费用分摊
- 边界条件处理

### 2. test_symbol_matcher.py
**测试对象**: `src/matchers/symbol_matcher.py` - SymbolMatcher 类

**测试覆盖** (25个测试用例):
- ✅ 做多持仓配对 (买入→卖出)
- ✅ 做空持仓配对 (卖空→买券还券)
- ✅ FIFO顺序验证
- ✅ 部分成交配对
- ✅ 孤立交易处理
- ✅ 未平仓持仓创建
- ✅ 盈亏计算（做多/做空）
- ✅ 持仓时间计算
- ✅ 统计信息

**关键测试场景**:
- FIFO先进先出验证
- 多次买入一次卖出
- 部分平仓场景
- 做多盈利/亏损
- 做空盈利/亏损

### 3. test_fifo_matcher.py
**测试对象**: `src/matchers/fifo_matcher.py` - FIFOMatcher 类

**测试覆盖** (21个测试用例):
- ✅ 初始化（dry_run/production模式）
- ✅ 交易加载
- ✅ 多标的协调
- ✅ 统计信息计算
- ✅ 数据库保存（使用Mock）
- ✅ 完整配对流程
- ✅ 警告信息生成
- ✅ 复杂场景（交错、部分成交）

**关键测试场景**:
- 单标的vs多标的处理
- dry_run模式验证
- 未平仓做空警告
- 交错的多标的交易

## 🚀 运行测试

### 方式1: 使用测试脚本（推荐）

```bash
# 运行所有Phase 4测试，生成覆盖率报告
./scripts/run_phase4_tests.sh
```

### 方式2: 使用pytest直接运行

```bash
# 运行所有Phase 4测试
python3 -m pytest tests/unit/test_trade_quantity.py \
                   tests/unit/test_symbol_matcher.py \
                   tests/unit/test_fifo_matcher.py -v

# 带覆盖率报告
python3 -m pytest tests/unit/test_trade_quantity.py \
                   tests/unit/test_symbol_matcher.py \
                   tests/unit/test_fifo_matcher.py \
                   --cov=src/matchers \
                   --cov-report=term-missing
```

### 方式3: 单独运行某个测试文件

```bash
# 只测试 TradeQuantity
python3 -m pytest tests/unit/test_trade_quantity.py -v

# 只测试 SymbolMatcher
python3 -m pytest tests/unit/test_symbol_matcher.py -v

# 只测试 FIFOMatcher
python3 -m pytest tests/unit/test_fifo_matcher.py -v
```

### 方式4: 运行特定的测试类或测试方法

```bash
# 运行特定测试类
python3 -m pytest tests/unit/test_symbol_matcher.py::TestSymbolMatcherLongPositions -v

# 运行特定测试方法
python3 -m pytest tests/unit/test_symbol_matcher.py::TestSymbolMatcherLongPositions::test_fifo_order -v
```

## 📊 测试覆盖率

当前测试覆盖率: **97%**

| 模块 | 语句数 | 未覆盖 | 覆盖率 | 未覆盖行号 |
|------|--------|--------|--------|------------|
| `trade_quantity.py` | 42 | 1 | 98% | 132 |
| `symbol_matcher.py` | 134 | 6 | 96% | 74-75, 101, 131, 245, 272 |
| `fifo_matcher.py` | 107 | 1 | 99% | 155 |
| `__init__.py` | 4 | 0 | 100% | - |
| **总计** | **287** | **8** | **97%** | - |

### 未覆盖的代码说明

1. **trade_quantity.py:132** - `calculate_fee_allocation` 中原始数量为0的边界情况
2. **symbol_matcher.py:74-75, 101, 131** - 未知交易方向的警告分支（实际不会发生）
3. **symbol_matcher.py:245, 272** - 价格为0的边界情况检查
4. **fifo_matcher.py:155** - 日志输出的进度报告

这些未覆盖的代码主要是:
- 极端边界情况（不太可能在实际数据中出现）
- 日志输出语句
- 防御性编程的错误处理

## 🧪 测试架构

### 测试组织结构

```
tests/unit/
├── test_trade_quantity.py     # TradeQuantity 测试
│   ├── TestTradeQuantityInit
│   ├── TestTradeQuantityConsume
│   ├── TestTradeQuantityFeeAllocation
│   ├── TestTradeQuantityMatchedPositions
│   ├── TestTradeQuantityIsFullyConsumed
│   ├── TestTradeQuantityGetConsumedQuantity
│   ├── TestTradeQuantityRepr
│   └── TestTradeQuantityEdgeCases
│
├── test_symbol_matcher.py     # SymbolMatcher 测试
│   ├── TestSymbolMatcherInit
│   ├── TestSymbolMatcherLongPositions
│   ├── TestSymbolMatcherShortPositions
│   ├── TestSymbolMatcherOrphanedTrades
│   ├── TestSymbolMatcherOpenPositions
│   ├── TestSymbolMatcherPnLCalculation
│   ├── TestSymbolMatcherHoldingPeriod
│   ├── TestSymbolMatcherWrongSymbol
│   ├── TestSymbolMatcherStatistics
│   └── TestSymbolMatcherRepr
│
└── test_fifo_matcher.py       # FIFOMatcher 测试
    ├── TestFIFOMatcherInit
    ├── TestFIFOMatcherLoadTrades
    ├── TestFIFOMatcherProcessTrades
    ├── TestFIFOMatcherStatistics
    ├── TestFIFOMatcherSavePositions
    ├── TestFIFOMatcherMatchAllTrades
    ├── TestFIFOMatcherWarnings
    ├── TestFIFOMatcherGetPositionsBySymbol
    ├── TestMatchTradesFromDatabase
    └── TestFIFOMatcherComplexScenarios
```

### 测试策略

1. **单元测试**: 每个类的方法都有独立的测试
2. **集成测试**: 测试多个组件协作的场景
3. **边界测试**: 覆盖零值、负值、极大值等边界情况
4. **错误处理**: 验证异常情况的正确处理
5. **Mock测试**: 使用Mock隔离数据库依赖

### 测试辅助函数

各测试文件都包含辅助函数用于创建测试数据:

```python
# test_symbol_matcher.py
def create_trade(direction, quantity, price, filled_time, fee=1.0, symbol='AAPL')

# test_fifo_matcher.py
def create_trade(symbol, direction, quantity, price, filled_time, trade_id=None)
```

## ✅ 测试质量指标

- **总测试数**: 75个
- **通过率**: 100%
- **代码覆盖率**: 97%
- **平均执行时间**: ~0.12秒

## 🐛 已发现并修复的Bug

在编写测试过程中发现并修复的bug:

1. **FIFOMatcher._calculate_statistics 中的enum比较错误**
   - **问题**: 使用 `p.status.value == 'OPEN'` (大写) 比较
   - **修复**: 改为 `p.status.value == 'open'` (小写)
   - **影响**: 导致统计信息中 closed_positions 和 open_positions 始终为0
   - **文件**: `src/matchers/fifo_matcher.py:208-209`

## 📝 编写新测试

当需要添加新功能时，请遵循以下模式:

```python
class TestNewFeature:
    """测试新功能"""

    def test_normal_case(self, fixture):
        """测试正常情况"""
        # Arrange - 准备测试数据
        # Act - 执行测试操作
        # Assert - 验证结果

    def test_edge_case(self, fixture):
        """测试边界情况"""
        pass

    def test_error_handling(self, fixture):
        """测试错误处理"""
        with pytest.raises(ValueError, match="error message"):
            # 触发错误的代码
            pass
```

## 🔧 依赖项

运行测试需要以下Python包:

```
pytest>=7.0.0
pytest-cov>=4.0.0
```

安装命令:
```bash
pip install pytest pytest-cov
```

## 📚 相关文档

- [Phase 4 PRD](../../project_docs/PRD.md#phase-4-fifo配对算法)
- [FIFO Matcher 实现](../../src/matchers/fifo_matcher.py)
- [Symbol Matcher 实现](../../src/matchers/symbol_matcher.py)
- [Trade Quantity 实现](../../src/matchers/trade_quantity.py)
