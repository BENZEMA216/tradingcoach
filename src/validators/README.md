# Validators - 数据验证模块

一旦我所属的文件夹有所变化，请更新我

## 架构说明

数据验证模块提供全面的数据质量保障功能，包括质量监控、异常检测、血缘追踪和自动修复。确保交易数据的准确性、完整性和一致性。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出验证器类 |
| `data_quality.py` | 基础检查器 | Position/MarketData 完整性检查 |
| `data_quality_monitor.py` | 监控仪表板 | 全面质量指标、异常检测、报告生成 |
| `data_lineage.py` | 血缘追踪 | 数据来源追踪、转换历史记录 |
| `data_fixer.py` | 自动修复 | 常见问题自动修复、回滚支持 |

---

## 快速使用

```bash
# 检查数据质量
python scripts/check_data_quality.py

# 运行自动修复 (预览)
python scripts/check_data_quality.py --fix

# 应用修复
python scripts/check_data_quality.py --fix --apply

# 追踪数据血缘
python scripts/check_data_quality.py --trace 123
```

## 质量等级

| 等级 | 分数范围 |
|------|---------|
| EXCELLENT | 95%+ |
| GOOD | 85-95% |
| FAIR | 70-85% |
| POOR | 50-70% |
| CRITICAL | <50% |

## 异常类型

| 类型 | 说明 |
|------|------|
| `OUTLIER_VALUE` | 统计异常值 |
| `MISSING_DATA` | 缺失数据 |
| `DUPLICATE_DATA` | 重复数据 |
| `INCONSISTENT_DATA` | 不一致数据 |
| `ORPHAN_RECORD` | 孤儿记录 |
| `BUSINESS_RULE_VIOLATION` | 业务规则违反 |

## 自动修复项

| 修复项 | 说明 |
|--------|------|
| 重复交易 | 删除重复记录 (保留最早) |
| 无效外键 | 清除无效 position_id |
| 评分范围 | 限制在 0-100 |
| 净盈亏 | 重算 net_pnl |
| 持仓天数 | 重算 holding_period |
