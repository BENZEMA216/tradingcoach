# Trading Coach

<div align="center">

![Trading Coach Logo](https://img.shields.io/badge/Trading-Coach-blue?style=for-the-badge&logo=chart.js)

**AI-Powered Trading Analytics & Performance Review Platform**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](#features) | [中文](#功能特性)

</div>

---

## Overview

Trading Coach is a comprehensive trading analytics platform that helps traders analyze their performance, identify patterns, and improve their trading decisions. It combines institutional-grade metrics with behavioral analysis to provide actionable insights.

### Key Highlights

- **Multi-Broker Support**: Import trades from Futu, Tiger, CITIC, Huatai and more
- **Smart Position Matching**: FIFO algorithm handles partial fills, shorts, and options
- **Quality Scoring System**: 8-dimension scoring (Entry, Exit, Trend, Risk Management, Behavior, etc.)
- **AI Trading Coach**: Rule-based insights with pattern detection across 10 dimensions
- **Rich Visualizations**: 15+ chart types including equity curves, heatmaps, and risk quadrants
- **Bilingual Support**: Full Chinese/English interface with real-time switching

---

## Features

### Data Import & Processing
- **CSV Auto-Detection**: Automatically identifies broker format (Futu CN/EN, Tiger, CITIC, Huatai)
- **Incremental Import**: Deduplication and merge with existing data
- **Options Support**: Parse complex option symbols (e.g., `NVDA260618C205`)
- **Real-time Progress**: Live processing logs with step-by-step feedback

### Position Analysis
- **FIFO Matching**: Accurate open/close pairing with partial fill support
- **MAE/MFE Tracking**: Maximum Adverse/Favorable Excursion analysis
- **Post-Exit Analysis**: Track what happened 5/10/20 days after exit
- **Options Strategy Detection**: Recognize 18+ options strategies (Covered Call, Iron Condor, etc.)

### Quality Scoring (V2 System)
| Dimension | Weight | Description |
|-----------|--------|-------------|
| Entry | 20% | Entry timing vs technical indicators |
| Exit | 20% | Profit capture efficiency |
| Trend | 15% | Alignment with market trend |
| Risk Management | 15% | Stop-loss execution, position sizing |
| Behavior | 10% | Emotional control, discipline |
| Market Environment | 10% | Context awareness |
| Execution | 5% | Slippage, fill quality |
| News Alignment | 5% | News context awareness |

### AI Coach Insights
Analyzes trading patterns across 10 dimensions:
- **Time**: Weekday/hour performance patterns
- **Holding Period**: Optimal holding duration
- **Symbol**: Best/worst performers, concentration risk
- **Direction**: Long vs short effectiveness
- **Risk**: Win/loss ratio, consecutive losses
- **Behavior**: Revenge trading, overconfidence detection
- **Fees**: Fee erosion analysis
- **Options**: Call vs Put preference
- **Trends**: Performance improvement/deterioration

### Visualizations
| Chart | Description |
|-------|-------------|
| Equity Curve | Cumulative P&L with drawdown overlay |
| Trading Heatmap | Performance by day-of-week and hour |
| Monthly Performance | Bar chart comparison by month |
| Symbol Risk Quadrant | Avg win vs avg loss scatter plot |
| Rolling Win Rate | Moving window win rate trend |
| P&L Distribution | Histogram of trade outcomes |
| Duration vs P&L | Holding period correlation |
| Strategy Performance | Breakdown by trading strategy |
| Price Chart | K-line with technical indicators |

---

## 功能特性

### 数据导入与处理
- **CSV 自动检测**: 自动识别券商格式（富途中英文、老虎、中信、华泰）
- **增量导入**: 去重合并现有数据
- **期权支持**: 解析复杂期权代码（如 `NVDA260618C205`）
- **实时进度**: 步骤式处理日志反馈

### 持仓分析
- **FIFO 配对**: 支持部分成交的精确开平仓配对
- **MAE/MFE 追踪**: 最大不利/有利偏移分析
- **出场后分析**: 追踪出场后 5/10/20 天的表现
- **期权策略识别**: 识别 18+ 种期权策略

### AI 教练洞察
跨 10 个维度分析交易模式：
- **时间**: 星期/小时表现模式
- **持仓周期**: 最优持仓时长
- **标的**: 最佳/最差表现、集中度风险
- **方向**: 做多 vs 做空效果
- **风险**: 盈亏比、连续亏损
- **行为**: 报复性交易、过度自信检测
- **费用**: 费用侵蚀分析
- **期权**: Call vs Put 偏好
- **趋势**: 表现提升/下滑

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
│           React 18 + Vite 5 + TypeScript + Tailwind             │
│              Recharts + Lightweight Charts + i18n               │
│                    http://localhost:5173                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API (40+ endpoints)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Backend                                 │
│           FastAPI + Pydantic v2 + SQLAlchemy 2.0                │
│        Task Manager + Insight Engine + Batch Fetcher            │
│                    http://localhost:8000                         │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│     SQLite       │ │   yfinance   │ │   3-Level Cache  │
│ (tradingcoach.db)│ │ Market Data  │ │  Memory/File/DB  │
└──────────────────┘ └──────────────┘ └──────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/BENZEMA216/tradingcoach.git
cd tradingcoach

# Setup Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup Frontend
cd frontend
npm install
cd ..

# Copy config template
cp config_template.py config.py
```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## Project Structure

```
tradingcoach/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/            # REST API Endpoints
│   │   │   └── endpoints/     # Dashboard, Positions, Statistics, etc.
│   │   ├── schemas/           # Pydantic Models
│   │   ├── services/          # Business Logic
│   │   │   ├── task_manager.py    # Async task processing
│   │   │   └── insight_engine.py  # AI insights generation
│   │   └── database.py        # DB Connection & Models
│   └── requirements.txt
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── api/               # API Client (Axios)
│   │   ├── components/
│   │   │   ├── charts/        # 15+ Chart Components
│   │   │   ├── common/        # Shared Components
│   │   │   ├── insights/      # AI Coach Components
│   │   │   ├── layout/        # App Layout
│   │   │   └── loading/       # Loading Page Components
│   │   ├── i18n/              # Internationalization (zh/en)
│   │   ├── pages/             # Page Components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Positions.tsx
│   │   │   ├── Statistics.tsx
│   │   │   ├── AICoach.tsx
│   │   │   └── Events.tsx
│   │   └── types/             # TypeScript Definitions
│   └── vite.config.ts
│
├── src/                        # Core Business Logic
│   ├── models/                # SQLAlchemy Models
│   ├── data_sources/          # Market Data & Caching
│   ├── indicators/            # 50+ Technical Indicators
│   ├── importers/             # CSV Parsers
│   ├── matchers/              # FIFO Position Matching
│   └── analyzers/             # Quality Scoring
│
├── scripts/                    # Utility Scripts
├── tests/                      # Test Suite
├── data/                       # SQLite Database
└── project_docs/              # Documentation
```

---

## API Reference

### Dashboard
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/dashboard/kpis` | Key performance indicators |
| `GET /api/v1/dashboard/equity-curve` | Equity curve data |
| `GET /api/v1/dashboard/recent-trades` | Recent closed positions |

### Positions
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/positions` | Paginated position list |
| `GET /api/v1/positions/{id}` | Position detail with scores |
| `GET /api/v1/positions/{id}/market-data` | K-line data for position |

### Statistics
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/statistics/overview` | Performance overview |
| `GET /api/v1/statistics/monthly-performance` | Monthly breakdown |
| `GET /api/v1/statistics/trading-heatmap` | Day/hour heatmap |
| `GET /api/v1/statistics/rolling-metrics` | Rolling win rate |

### AI Coach
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/ai-coach/proactive-insights` | Generated insights |
| `POST /api/v1/ai-coach/chat` | Chat with AI coach |

### Upload
| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/upload` | Upload CSV for processing |
| `GET /api/v1/upload/task/{task_id}` | Task status polling |

Full API documentation: http://localhost:8000/docs

---

## Technology Stack

| Category | Technology |
|----------|------------|
| **Backend** | Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| **Frontend** | React 18, Vite 5, TypeScript 5, Tailwind CSS |
| **State Management** | TanStack Query (React Query) |
| **Charts** | Recharts, Lightweight Charts |
| **Internationalization** | react-i18next |
| **Database** | SQLite |
| **Market Data** | yfinance with 3-level caching |
| **Technical Indicators** | Custom pandas implementation (50+ indicators) |

---

## Supported Brokers

| Broker | Format | Markets | Status |
|--------|--------|---------|--------|
| Futu Securities (CN) | CSV | US/HK/A-Share | ✅ |
| Futu Securities (EN) | CSV | US/HK/A-Share | ✅ |
| Tiger Brokers | CSV | US/HK/A-Share | ✅ |
| CITIC Securities | CSV | A-Share | ✅ |
| Huatai Securities | CSV | A-Share | ✅ |

---

## Development Progress

### Completed
- [x] Database schema (5 tables, 30+ indexes)
- [x] CSV import system with auto-detection
- [x] FIFO position matching algorithm
- [x] Market data fetching with 3-level cache
- [x] Technical indicators (50+ indicators)
- [x] Quality scoring system (V2, 8 dimensions)
- [x] FastAPI REST API (40+ endpoints)
- [x] React frontend with TypeScript
- [x] Dark mode support
- [x] Bilingual UI (Chinese/English)
- [x] AI Coach with rule-based insights
- [x] Event analysis timeline
- [x] Docker support
- [x] Railway deployment config

### In Progress
- [ ] AI-powered chat with LLM integration
- [ ] Advanced options analytics
- [ ] Mobile responsive optimization
- [ ] Real-time data streaming

---

## Deployment

### Docker

```bash
docker build -t tradingcoach .
docker run -p 8000:8000 tradingcoach
```

### Railway

The project includes Railway configuration for one-click deployment:
- `railway.json` - Build configuration
- `Procfile` - Start command
- Environment variables auto-configured

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact

- GitHub: [@BENZEMA216](https://github.com/BENZEMA216)
- Project: [https://github.com/BENZEMA216/tradingcoach](https://github.com/BENZEMA216/tradingcoach)

---

<div align="center">

**Version**: v0.9.0 | **Last Updated**: 2025-01-10

Made with dedication for traders who want to improve.

</div>
