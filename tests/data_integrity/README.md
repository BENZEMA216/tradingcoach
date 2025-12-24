# data_integrity - 数据完整性测试

一旦我所属的文件夹有所变化，请更新我

## 架构说明

基于 `project_docs/DATA_INTEGRITY_CHECKLIST.md` 定义的 36 项检查点，验证数据库中 trades/positions 等表的数据一致性和业务规则正确性。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| conftest.py | Fixtures | 数据库连接、查询工具函数 |
| test_trade_integrity.py | Trade 检查 | 7 项：指纹唯一、必填字段、方向枚举、费用计算 |
| test_position_integrity.py | Position 检查 | 12 项：字段完整、盈亏计算、评分范围 |
| test_matching_integrity.py | FIFO/FK 检查 | 7 项：配对关联、方向一致、外键有效 |
| test_business_rules.py | 业务规则检查 | 7 项：时序一致、数量价格、市场数据 |

## 运行测试

```bash
# 运行所有检查
python -m pytest tests/data_integrity/ -v

# 只看失败项
python -m pytest tests/data_integrity/ --tb=short

# 生成报告
python -m pytest tests/data_integrity/ --html=reports/integrity_report.html
```

## 检查项优先级

- **P0**: 核心数据完整性，必须通过
- **P1**: 重要业务规则，应该通过
- **P2**: 数据质量检查，建议通过

详见 `project_docs/DATA_INTEGRITY_CHECKLIST.md`
