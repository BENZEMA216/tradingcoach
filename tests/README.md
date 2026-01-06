# 测试指南

一旦我所属的文件夹有所变化，请更新我

## 架构说明

TradingCoach 采用多层次测试策略，包括单元测试、集成测试、契约测试、数据完整性测试、性能基准测试和 E2E 测试。确保代码质量、API 一致性和性能稳定。

## 目录结构

```
tests/
├── unit/                    # 单元测试 (687+ 测试用例)
│   ├── test_csv_parser.py
│   ├── test_fifo_matcher.py
│   ├── test_quality_scorer.py
│   ├── test_option_analyzer.py   # 期权分析 (24个用例)
│   └── ...
├── integration/             # API 集成测试
│   ├── conftest.py              # TestClient 配置
│   ├── test_api_positions.py    # Positions API 测试
│   └── test_api_statistics.py   # Statistics API 测试
├── contract/                # 契约测试
│   └── test_api_schema.py       # Schema 验证
├── benchmark/               # 性能基准测试
│   └── test_fifo_performance.py # FIFO/CSV 性能测试
├── data_integrity/          # 数据完整性测试 (34项)
│   ├── conftest.py              # 支持测试数据 & 生产数据两种模式
│   ├── test_trade_integrity.py
│   ├── test_position_integrity.py
│   ├── test_matching_integrity.py
│   └── test_business_rules.py
├── fixtures/                # 固定测试数据
│   ├── test_data.sql            # SQL 格式测试数据
│   └── README.md                # 测试数据说明
├── factories.py             # 测试数据工厂 (factory_boy)
└── conftest.py              # 全局 pytest 配置
```

## 文件清单

| 文件/目录 | 角色 | 功能 |
|----------|------|------|
| `unit/` | 单元测试 | 模块级功能测试 |
| `integration/` | 集成测试 | API 端点测试 |
| `contract/` | 契约测试 | Schema 一致性验证 |
| `benchmark/` | 性能测试 | 性能基准和阈值 |
| `data_integrity/` | 数据校验 | 34项数据库规则 (支持测试/生产双模式) |
| `fixtures/` | 测试数据 | 固定的 SQL 测试数据集 |
| `factories.py` | 数据工厂 | 生成随机测试数据 (factory_boy) |
| `conftest.py` | 全局配置 | fixtures 和钩子 |

---

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
# 所有测试
python -m pytest tests/ -v

# 带覆盖率 (门槛 75%)
python -m pytest tests/ -v --cov=src --cov-report=html --cov-fail-under=75

# 跳过慢速测试
python -m pytest tests/ -v -m "not slow"

# 并行运行
python -m pytest tests/ -n auto
```

---

## 测试类型详解

### 1. 单元测试 (`tests/unit/`)

```bash
python -m pytest tests/unit/ -v
```

**主要模块覆盖：**

| 测试文件 | 测试内容 |
|----------|---------|
| `test_fifo_matcher.py` | FIFO 配对算法 (21个用例) |
| `test_quality_scorer.py` | 四维度评分系统 |
| `test_option_analyzer.py` | 期权分析 (24个用例) |
| `test_indicator_calculator.py` | RSI/MACD/BB/ATR |
| `test_csv_parser.py` | CSV 解析和编码 |

### 2. 集成测试 (`tests/integration/`)

测试 API 完整请求-响应流程。

```bash
python -m pytest tests/integration/ -v
```

**测试覆盖：**
- Positions API: 列表、筛选、分页、详情、错误处理
- Statistics API: 性能指标、分解统计、风险指标

### 3. 契约测试 (`tests/contract/`)

验证 API Schema 一致性。

```bash
python -m pytest tests/contract/ -v
```

**验证内容：**
- Pydantic Schema 结构验证
- OpenAPI Schema 定义
- 响应格式一致性

### 4. 性能基准测试 (`tests/benchmark/`)

```bash
# 运行基准测试
python -m pytest tests/benchmark/ -v --benchmark-only

# 生成 JSON 报告
python -m pytest tests/benchmark/ --benchmark-json=benchmark.json
```

**性能阈值：**
- FIFO 配对 5000 笔: < 2 秒
- CSV 解析 5000 行: < 1 秒

### 5. 数据完整性测试 (`tests/data_integrity/`)

34 项数据库校验规则，支持两种运行模式。

#### 运行模式

| 模式 | 命令 | 用途 |
|------|------|------|
| **测试模式** (默认) | `pytest tests/data_integrity/ -v` | CI/CD，代码正确性验证 |
| **生产监控模式** | `pytest tests/data_integrity/ -v --use-production-db` | 生产数据质量监控 |

```bash
# 默认: 使用 tests/fixtures/test_data.sql 的固定测试数据
python -m pytest tests/data_integrity/ -v

# 生产监控: 检查实际数据库数据质量
python -m pytest tests/data_integrity/ -v --use-production-db

# 独立数据监控脚本 (推荐用于生产监控)
python scripts/monitor_data_quality.py
python scripts/monitor_data_quality.py --quick  # 快速检查
```

#### 检查项

| 类别 | 检查项 |
|------|--------|
| DI-TRADE-* | 交易表 (7项) |
| DI-POS-* | 持仓表 (11项) |
| DI-MATCH-* | 配对规则 (5项) |
| DI-BIZ-* | 业务规则 (7项) |
| DI-MD-* | 市场数据 (3项) |

#### 测试数据 vs 生产数据

| 场景 | 推荐方式 |
|------|---------|
| CI/CD 流水线 | 默认模式 (测试数据) |
| 本地开发验证 | 默认模式 (测试数据) |
| 数据导入后验证 | `--use-production-db` 或 `monitor_data_quality.py` |
| 定期数据质量检查 | `monitor_data_quality.py` |

---

## 测试数据工厂

使用 `factory_boy` 生成测试数据：

```python
from tests.factories import (
    TradeFactory,
    PositionFactory,
    OptionPositionFactory,
    create_winning_positions,
    create_losing_positions,
    create_mixed_portfolio,
)

# 创建单个交易
trade = TradeFactory.build()

# 创建批量持仓
positions = PositionFactory.create_batch(10)

# 创建盈利组合
winners = create_winning_positions(5)

# 创建混合组合 (6盈4亏)
portfolio = create_mixed_portfolio(winners=6, losers=4)
```

---

## 覆盖率

### 生成报告

```bash
# HTML 报告
python -m pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# 带门槛检查 (75%)
python -m pytest tests/ --cov=src --cov-fail-under=75
```

### 覆盖率目标

| 模块 | 目标 |
|------|------|
| models | > 80% |
| importers | > 90% |
| matchers | > 90% |
| analyzers | > 80% |

---

## 突变测试

验证测试质量：

```bash
# 运行突变测试
mutmut run --paths-to-mutate=src/matchers/

# 查看结果
mutmut results

# 查看存活突变体
mutmut show <id>
```

---

## Allure 报告

```bash
# 收集测试数据
python -m pytest tests/ --alluredir=allure-results

# 生成报告
allure serve allure-results
```

---

## CI/CD 集成

GitHub Actions 自动运行：

| Job | 触发条件 | 内容 |
|-----|---------|------|
| test | Push/PR | 单元测试 + 覆盖率 |
| integration | Push/PR | 集成测试 |
| contract | Push/PR | 契约测试 |
| data-integrity | main | 数据完整性 |
| benchmark | main | 性能基准 |
| e2e | main | 端到端测试 |
| allure-report | 所有 | Allure 报告 |

---

## 前端测试

### 单元/快照测试 (Vitest)

```bash
cd frontend
npm run test:unit       # 运行测试
npm run test:watch      # 监视模式
npm run test:coverage   # 覆盖率
npm run test:unit -- -u # 更新快照
```

### E2E 测试 (Playwright)

```bash
cd frontend
npm run test:e2e          # 运行所有 E2E 测试
npm run test:e2e:ui       # UI 模式
npm run test:e2e:console  # 控制台错误监控
npm run test:e2e:perf     # 性能测试
npm run test:e2e:a11y     # 可访问性测试
npm run test:e2e:visual   # 视觉回归测试
npm run test:e2e:qa       # 用户流程测试
```

**E2E 测试类型：**

| 测试类型 | 文件 | 功能 |
|----------|------|------|
| 控制台错误 | `console-errors.spec.ts` | 检测 JS 错误和警告 |
| 性能测试 | `performance.spec.ts` | 验证加载/渲染性能 |
| 可访问性 | `accessibility.spec.ts` | 键盘导航、ARIA 标签 |
| 视觉回归 | `visual-regression/*.spec.ts` | 截图对比 |
| 用户流程 | `qa-walkthrough.spec.ts` | 完整操作流程 |

---

## 全量测试脚本

一键运行所有测试：

```bash
# 运行完整测试套件
./scripts/run_full_test_suite.sh

# 快速模式（跳过慢速测试）
./scripts/run_full_test_suite.sh --quick

# 生成 HTML 报告
./scripts/run_full_test_suite.sh --report

# 跳过特定测试
./scripts/run_full_test_suite.sh --skip-e2e
./scripts/run_full_test_suite.sh --skip-backend
./scripts/run_full_test_suite.sh --skip-frontend
```

---

## 命名规范

```python
# 文件: test_<module>.py
# 类: Test<Feature>
# 方法: test_<action>_<scenario>_<expected>

def test_fifo_matching_partial_fill_creates_remaining():
    pass
```

---

## 常用命令

```bash
# 运行特定文件
python -m pytest tests/unit/test_fifo_matcher.py -v

# 运行特定类
python -m pytest tests/unit/test_quality_scorer.py::TestEntryScoring -v

# 运行标记的测试
python -m pytest tests/ -m integration

# 调试失败测试
python -m pytest tests/path/to/test.py -v --tb=long -x

# 显示最慢的 10 个测试
python -m pytest tests/ --durations=10
```
