#!/bin/bash
#
# Phase 4 单元测试运行脚本
#
# 运行所有 Phase 4 FIFO Matching 相关的单元测试
#

set -e

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Phase 4 FIFO Matching - 单元测试"
echo "=========================================="
echo ""

# 运行测试
echo "运行测试..."
python3 -m pytest \
    tests/unit/test_trade_quantity.py \
    tests/unit/test_symbol_matcher.py \
    tests/unit/test_fifo_matcher.py \
    -v \
    --cov=src/matchers \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    "$@"

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "HTML覆盖率报告已生成: htmlcov/index.html"
echo "使用以下命令查看:"
echo "  open htmlcov/index.html    # macOS"
echo "  xdg-open htmlcov/index.html  # Linux"
echo ""
