# scripts - 脚本工具

命令行脚本，用于执行数据处理流水线的各个阶段。

## 设计思路

每个脚本对应数据处理流水线的一个步骤，支持独立运行和参数配置。

```
init_db.py → import_trades.py → run_matching.py → preload_market_data.py
    → calculate_indicators.py → score_positions.py → analyze_scores.py
```

## 脚本列表

| 脚本 | 功能 | 依赖 |
|------|------|------|
| `init_db.py` | 初始化数据库 | - |
| `import_trades.py` | 导入交易数据 | init_db |
| `run_matching.py` | FIFO 配对 | import_trades |
| `preload_market_data.py` | 预加载市场数据 | run_matching |
| `calculate_indicators.py` | 计算技术指标 | preload_market_data |
| `score_positions.py` | 质量评分 | calculate_indicators |
| `analyze_scores.py` | 评分分析 | score_positions |
| `classify_strategies.py` | 策略分类 | score_positions |
| `calculate_post_exit.py` | 离场后走势 | score_positions |
| `check_data_coverage.py` | 数据覆盖检查 | preload_market_data |
| `verify_indicators.py` | 验证指标计算 | calculate_indicators |
| `enrich_position_indicators.py` | 丰富持仓指标 | calculate_indicators |

## 使用指南

### 1. init_db.py

初始化数据库，创建所有表结构。

```bash
# 基本用法
python scripts/init_db.py

# 重建数据库（清空所有数据）
python scripts/init_db.py --rebuild
```

### 2. import_trades.py

从 CSV 导入交易记录。

```bash
# 导入指定文件
python scripts/import_trades.py --file original_data/交易记录.csv

# 预览模式（不实际导入）
python scripts/import_trades.py --file 交易记录.csv --dry-run

# 指定批次大小
python scripts/import_trades.py --file 交易记录.csv --batch-size 100
```

### 3. run_matching.py

运行 FIFO 配对算法。

```bash
# 配对所有未配对的交易
python scripts/run_matching.py --all

# 配对指定 symbol
python scripts/run_matching.py --symbol AAPL

# 预览模式
python scripts/run_matching.py --all --dry-run
```

### 4. preload_market_data.py

预加载市场 OHLCV 数据。

```bash
# 预加载所有交易相关的市场数据
python scripts/preload_market_data.py --all

# 仅预热 Top N 个 symbol
python scripts/preload_market_data.py --warmup-only --top-n 10

# 指定日期范围
python scripts/preload_market_data.py --all --start 2024-01-01 --end 2024-12-31
```

### 5. calculate_indicators.py

计算技术指标（RSI, MACD, BB, ATR, MA 等）。

```bash
# 计算所有市场数据的技术指标
python scripts/calculate_indicators.py --all

# 计算指定 symbol
python scripts/calculate_indicators.py --symbols AAPL,TSLA,NVDA

# 强制重新计算
python scripts/calculate_indicators.py --all --force
```

### 6. score_positions.py

执行交易质量评分。

```bash
# 评分所有已平仓交易
python scripts/score_positions.py --all

# 评分指定 position
python scripts/score_positions.py --positions 1,2,3

# 仅查看已有评分
python scripts/score_positions.py --show-only --limit 50

# 重新评分所有
python scripts/score_positions.py --all --rescore
```

### 7. analyze_scores.py

分析评分结果，生成统计报告。

```bash
# 生成评分分析报告
python scripts/analyze_scores.py

# 按等级分组
python scripts/analyze_scores.py --by-grade

# 导出为 CSV
python scripts/analyze_scores.py --export scores_report.csv
```

### 8. classify_strategies.py

自动分类交易策略。

```bash
# 分类所有持仓
python scripts/classify_strategies.py --all

# 分类指定持仓
python scripts/classify_strategies.py --positions 1,2,3
```

### 9. calculate_post_exit.py

计算离场后价格走势（5/10/20 日）。

```bash
# 计算所有已平仓持仓
python scripts/calculate_post_exit.py --all

# 指定计算天数
python scripts/calculate_post_exit.py --all --days 5,10,20,60
```

### 10. check_data_coverage.py

检查市场数据覆盖情况。

```bash
# 检查数据覆盖
python scripts/check_data_coverage.py

# 检查指定 symbol
python scripts/check_data_coverage.py --symbol AAPL
```

## 完整流水线

按顺序执行完整的数据处理流程：

```bash
# 1. 初始化数据库
python scripts/init_db.py

# 2. 导入交易数据
python scripts/import_trades.py --file original_data/历史-保证金综合账户*.csv

# 3. FIFO 配对
python scripts/run_matching.py --all

# 4. 预加载市场数据
python scripts/preload_market_data.py --all

# 5. 计算技术指标
python scripts/calculate_indicators.py --all

# 6. 质量评分
python scripts/score_positions.py --all

# 7. 查看结果
python scripts/analyze_scores.py
```

## 日志配置

所有脚本的日志输出到 `logs/` 目录：

```
logs/
├── import_trades.log
├── run_matching.log
├── preload_market_data.log
├── calculate_indicators.log
└── score_positions.log
```

## 通用参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 预览模式，不实际修改数据 |
| `--verbose`, `-v` | 详细输出 |
| `--quiet`, `-q` | 静默模式 |
| `--help`, `-h` | 显示帮助 |

## 错误处理

脚本执行失败时：
1. 检查日志文件获取详细错误
2. 确认依赖步骤已完成
3. 检查数据库连接配置

```bash
# 查看最近的错误日志
tail -100 logs/score_positions.log
```

## 开发新脚本

```python
#!/usr/bin/env python3
"""
脚本描述
"""

import argparse
import logging
from src.models.base import init_database, get_session

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='脚本描述')
    parser.add_argument('--all', action='store_true', help='处理所有')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    args = parser.parse_args()

    # 初始化数据库
    init_database('sqlite:///data/tradingcoach.db')
    session = get_session()

    try:
        # 业务逻辑
        pass
    finally:
        session.close()

if __name__ == '__main__':
    main()
```
