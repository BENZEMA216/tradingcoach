# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ 文档维护规范 (CRITICAL)

**任何功能、架构、代码变更完成后，必须同步更新相关文档：**

1. **修改代码文件时** → 更新该文件的开头注释（input/output/pos）
2. **修改目录结构时** → 更新该目录的 README.md（文件清单）
3. **修改模块功能时** → 更新模块的架构说明
4. **新增文件时** → 在文件开头添加标准注释，并更新目录 README.md

### 文件注释格式
```python
"""
input: 依赖的模块/数据
output: 提供的功能/数据
pos: 在系统中的角色定位

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
```

### 目录 README.md 格式
```markdown
# 目录名

一旦我所属的文件夹有所变化，请更新我

## 架构说明（3行以内）
简述本目录的核心职责和设计思路

## 文件清单
| 文件名 | 角色 | 功能 |
|--------|------|------|
| file.py | xxx | xxx |
```

---

## Project Overview

TradingCoach 是一个交易复盘分析系统，帮助交易者分析历史交易数据、识别交易行为模式、评估交易质量。

### 核心功能
- **数据导入**: 支持中英文富途CSV格式，增量导入去重
- **持仓配对**: FIFO算法自动配对开仓/平仓交易
- **质量评分**: 8维度V2评分系统（技术、行为、风控等）
- **统计分析**: 多维度盈亏归因、行为模式检测
- **持仓对账**: 券商持仓快照与系统计算对账

### 技术架构
- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: React + TypeScript + Vite + TailwindCSS
- **数据处理**: Python + Pandas

---

## Repository Structure

```
tradingcoach/
├── CLAUDE.md              # 本文件 - Claude Code 指南
├── config.py              # 项目配置
├── requirements.txt       # Python 依赖
│
├── backend/               # FastAPI 后端服务
│   ├── app/
│   │   ├── api/v1/        # REST API 端点
│   │   ├── schemas/       # Pydantic 数据模型
│   │   └── services/      # 业务逻辑服务
│   └── README.md
│
├── frontend/              # React 前端应用
│   ├── src/
│   │   ├── components/    # React 组件
│   │   ├── pages/         # 页面组件
│   │   ├── api/           # API 客户端
│   │   └── i18n/          # 国际化
│   └── README.md
│
├── src/                   # 核心数据处理模块
│   ├── importers/         # CSV 解析、增量导入
│   ├── matchers/          # FIFO 持仓配对
│   ├── analyzers/         # 质量评分、行为分析
│   ├── reconciler/        # 持仓对账
│   ├── models/            # SQLAlchemy 数据模型
│   └── README.md
│
├── data/                  # SQLite 数据库
├── original_data/         # 原始 CSV 数据文件
├── scripts/               # 数据处理脚本
├── tests/                 # 测试代码
├── logs/                  # 日志文件
└── project_docs/          # 项目文档
```

---

## Development Notes

### 启动服务
```bash
# 后端 (端口 8000)
cd backend && uvicorn app.main:app --reload

# 前端 (端口 5173)
cd frontend && npm run dev
```

### 数据处理
```bash
# 导入交易数据（增量去重）
python scripts/import_trades.py

# 配对持仓
python scripts/match_positions.py

# 计算评分
python scripts/score_positions.py
```

### CSV 数据格式
- **中文版**: UTF-8-BOM 编码，字段如"方向"、"代码"、"成交价格"
- **英文版**: UTF-8 编码，字段如"Side"、"Symbol"、"Fill Price"
- 支持 HKT/ET 时区自动解析
- 支持期权符号解析（如 NVDA260618C205）

### 关键配置
- 数据库路径: `data/tradingcoach.db`
- API 前缀: `/api/v1`
- 默认端口: 后端 8000, 前端 5173

---

## Testing

```bash
# 后端 API 测试
python -m pytest tests/

# 前端 E2E 测试
cd frontend && npx playwright test

# 类型检查
cd frontend && npx tsc --noEmit
```
