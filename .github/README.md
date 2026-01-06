# .github - GitHub 配置

一旦我所属的文件夹有所变化，请更新我

## 架构说明

GitHub Actions CI/CD 配置，自动化测试、代码检查和构建流程。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `workflows/ci.yml` | CI 流水线 | 自动测试、代码检查、前端构建 |

## CI 流水线说明

### 触发条件

- `push` 到 `main` 或 `dev/*` 分支
- `pull_request` 到 `main` 分支

### Jobs

| Job | 说明 | 运行条件 |
|-----|------|---------|
| `test` | Python 单元测试 + 覆盖率 | 始终运行 |
| `data-integrity` | 数据完整性测试 | 仅 main 分支 |
| `lint` | 代码风格检查 (Ruff) | 始终运行 |
| `frontend` | 前端类型检查 + 构建 | 始终运行 |

### 测试覆盖

```yaml
# 单元测试
python -m pytest tests/ -v --ignore=tests/data_integrity/ --cov=src

# 数据完整性测试 (仅 main)
python -m pytest tests/data_integrity/ -v
```

### 前端检查

```yaml
# 类型检查
npx tsc --noEmit

# 构建
npm run build
```

## 本地运行

模拟 CI 环境运行：

```bash
# Python 测试
python -m pytest tests/ -v --ignore=tests/data_integrity/

# 数据完整性测试
python -m pytest tests/data_integrity/ -v

# 代码检查
pip install ruff && ruff check src/

# 前端
cd frontend && npm ci && npm run typecheck && npm run build
```
