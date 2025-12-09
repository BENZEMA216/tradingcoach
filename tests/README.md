# tests - 测试目录

单元测试和集成测试，确保代码质量和正确性。

## 设计思路

- **单元测试**: 测试单个函数/类的功能
- **集成测试**: 测试模块间的协作
- **Fixture**: 复用测试数据和环境

## 目录结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_csv_parser.py
│   ├── test_data_cleaner.py
│   ├── test_fifo_matcher.py
│   ├── test_yfinance_client.py
│   ├── test_cache_manager.py
│   ├── test_indicator_calculator.py
│   ├── test_quality_scorer.py
│   ├── test_option_analyzer.py   # 期权分析测试 (24个用例)
│   └── ...
├── fixtures/                # 测试数据
│   ├── sample_trades.csv
│   └── sample_positions.json
└── conftest.py             # pytest 配置和共享 fixture
```

## 运行测试

### 运行所有测试

```bash
python -m pytest tests/ -v
```

### 运行特定测试文件

```bash
python -m pytest tests/unit/test_quality_scorer.py -v
```

### 运行特定测试类

```bash
python -m pytest tests/unit/test_quality_scorer.py::TestEntryScoring -v
```

### 运行特定测试方法

```bash
python -m pytest tests/unit/test_option_analyzer.py::TestOptionAnalyzer::test_parse_call_option -v
```

### 显示测试覆盖率

```bash
python -m pytest tests/ --cov=src --cov-report=html
# 报告生成在 htmlcov/index.html
```

### 快速测试（跳过慢测试）

```bash
python -m pytest tests/ -v -m "not slow"
```

## 测试文件说明

### test_csv_parser.py
- 测试 CSV 解析功能
- UTF-8 BOM 编码处理
- 字段映射正确性

### test_data_cleaner.py
- 数据清洗规则
- 方向标准化
- 数值类型转换

### test_fifo_matcher.py
- FIFO 配对算法
- 部分成交处理
- 做空配对
- 边界情况

### test_yfinance_client.py
- 代码转换 (港股/A股)
- 限流机制
- 数据格式标准化

### test_indicator_calculator.py
- RSI 计算
- MACD 计算
- 布林带计算
- ATR 计算
- 边界数据处理

### test_quality_scorer.py
- 四维度评分
- 评分等级分配
- 边界分数处理

### test_option_analyzer.py (24 个测试用例)

| 测试类 | 测试内容 |
|--------|---------|
| TestOptionInfoParsing | Call/Put 解析、无效格式处理 |
| TestMoneynessCalculation | ATM/ITM/OTM 计算 |
| TestDTEClassification | 短期/中期/长期/LEAPS 分类 |
| TestEntryAnalysis | 有/无市场数据的入场分析 |
| TestTrendAlignment | Call/Put 趋势一致性 |
| TestUnderlyingMovement | 正股走势分析 |
| TestGreeksImpact | Delta/Theta 影响估算 |
| TestStrategyEvaluation | 策略评估 |
| TestScoresCalculation | 评分计算 |
| TestFullPositionAnalysis | 完整持仓分析 |
| TestEdgeCases | 边界情况处理 |

## Fixture 示例

### conftest.py

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.base import Base

@pytest.fixture
def db_session():
    """创建内存数据库会话"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def sample_position(db_session):
    """创建示例持仓"""
    from src.models.position import Position
    position = Position(
        symbol='AAPL',
        direction='long',
        open_price=150.0,
        close_price=160.0,
        quantity=100,
        # ...
    )
    db_session.add(position)
    db_session.commit()
    return position
```

### 使用 fixture

```python
def test_calculate_score(db_session, sample_position):
    from src.analyzers.quality_scorer import QualityScorer

    scorer = QualityScorer()
    result = scorer.calculate_overall_score(db_session, sample_position)

    assert result['overall_score'] >= 0
    assert result['overall_score'] <= 100
```

## 编写测试

### 命名规范

- 测试文件: `test_<module_name>.py`
- 测试类: `Test<FeatureName>`
- 测试方法: `test_<what_is_being_tested>`

### 测试结构 (AAA 模式)

```python
def test_rsi_calculation(self):
    # Arrange - 准备测试数据
    df = pd.DataFrame({
        'Close': [100, 102, 101, 103, 105, ...],
    })
    calculator = IndicatorCalculator()

    # Act - 执行被测试的方法
    rsi = calculator.calculate_rsi(df, period=14)

    # Assert - 验证结果
    assert len(rsi) == len(df)
    assert rsi.iloc[-1] > 50  # 上涨趋势 RSI > 50
```

### 边界测试

```python
def test_empty_dataframe(self):
    """测试空数据处理"""
    calculator = IndicatorCalculator()
    df = pd.DataFrame()

    rsi = calculator.calculate_rsi(df)

    assert rsi.empty

def test_single_row(self):
    """测试单行数据"""
    df = pd.DataFrame({'Close': [100]})
    rsi = calculator.calculate_rsi(df)

    assert pd.isna(rsi.iloc[0])  # 数据不足应返回 NaN
```

## 标记慢测试

```python
import pytest

@pytest.mark.slow
def test_batch_fetch_100_symbols():
    """需要网络请求的慢测试"""
    # ...
```

## Mock 外部依赖

```python
from unittest.mock import Mock, patch

@patch('src.data_sources.yfinance_client.yf.Ticker')
def test_get_ohlcv_mocked(mock_ticker):
    """模拟 yfinance API 调用"""
    mock_ticker.return_value.history.return_value = pd.DataFrame({
        'Open': [100], 'High': [105], 'Low': [99],
        'Close': [103], 'Volume': [1000000]
    })

    client = YFinanceClient()
    df = client.get_ohlcv('AAPL', date(2024,1,1), date(2024,1,1))

    assert len(df) == 1
    mock_ticker.assert_called_once_with('AAPL')
```

## 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| models | > 80% |
| importers | > 90% |
| matchers | > 90% |
| indicators | > 85% |
| analyzers | > 80% |

## 持续集成

测试在 GitHub Actions 中自动运行：

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    python -m pytest tests/ -v --cov=src
```
