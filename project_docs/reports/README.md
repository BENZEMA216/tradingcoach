# reports - 测试与质量报告目录

一旦我所属的文件夹有所变化，请更新我

## 架构说明

存放自动生成的测试报告和数据质量报告。报告由 CI/CD 流程或手动运行脚本生成，用于追踪项目质量状态。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| TEST_REPORT.md | 测试报告 | 全量测试执行结果，包含单元测试、集成测试、E2E 测试 |
| DATA_QUALITY_REPORT.md | 质量报告 | 数据质量检查结果，包含完整性、准确性、一致性分析 |

## 生成命令

```bash
# 运行全量测试并更新 TEST_REPORT.md
./scripts/run_full_test_suite.sh

# 运行数据质量检查并更新 DATA_QUALITY_REPORT.md
python scripts/check_data_quality.py
```

## 报告更新频率

| 报告 | 建议频率 |
|------|----------|
| TEST_REPORT.md | 每次发布前 / PR 合并前 |
| DATA_QUALITY_REPORT.md | 每周 / 数据导入后 |
