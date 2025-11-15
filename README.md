# Trading Coach - 交易复盘系统

AI驱动的个人交易复盘工具，帮助分析交易质量、识别模式、提升交易表现。

## 功能特性

- ✅ **交易数据导入**: 支持券商CSV导入，自动解析和清洗
- ✅ **交易配对**: FIFO算法，支持部分成交、做空、期权
- ✅ **技术指标分析**: RSI, MACD, 布林带, ATR, MA等
- ✅ **质量评分系统**: 四维度评分（入场、出场、趋势、风险管理）
- ✅ **市场环境分析**: 大盘背景、波动率、行业强弱
- 🔜 **AI增强分析**: 模式识别、建议生成（未来）

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/BENZEMA216/tradingcoach.git
cd tradingcoach

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

```bash
# 复制配置模板
cp config_template.py config.py

# 编辑config.py，填入API Keys
```

**重要**: 请参考 `project_docs/api_keys_guide.md` 申请API Keys

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 导入交易数据

```bash
python scripts/import_trades.py --file original_data/历史-保证金综合账户*.csv
```

## 项目文档

完整的技术文档位于 `project_docs/` 目录:

1. **PRD.md** - 产品需求文档
2. **technical_indicators_research.md** - 技术指标研究
3. **data_extensibility_design.md** - 数据扩展性设计
4. **technical_implementation_plan.md** - 技术实现方案
5. **api_keys_guide.md** - API申请指南

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| 数据库 | SQLite (MVP) → PostgreSQL (扩展) |
| ORM | SQLAlchemy 2.0+ |
| 数据处理 | pandas, numpy |
| 技术指标 | pandas-ta, TA-Lib (可选) |
| 市场数据 | yfinance, Alpha Vantage |
| Web框架 | Streamlit |

## 开发进度

### Phase 1: 基础架构 🚧
- [x] 项目结构搭建
- [x] 配置文件和依赖管理
- [ ] 数据库Schema设计

### Phase 2-7: 核心功能开发 📋
详见 `project_docs/technical_implementation_plan.md`

## 许可证

MIT License

## 联系方式

- GitHub: [@BENZEMA216](https://github.com/BENZEMA216)
- 项目链接: https://github.com/BENZEMA216/tradingcoach

---

**版本**: v0.1.0 | **最后更新**: 2025-11-16
