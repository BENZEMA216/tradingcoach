# Trading Coach

<div align="center">

![Trading Coach Logo](https://img.shields.io/badge/Trading-Coach-blue?style=for-the-badge&logo=chart.js)

**Sample-first trading review and behavior analytics for active retail traders**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](#features) | [中文](#功能特性)

</div>

---

## Overview

TradingCoach helps active retail traders review their own trade history, identify behavior patterns, and understand what their P&L alone does not explain. It is built for post-trade review: CSV import, FIFO position matching, statistics, behavior-oriented AI Coach insights, position detail review, and counterfactual backtests.

For the Product Hunt beta, TradingCoach is intentionally **sample-first**:

- Primary path: try an anonymous sample workspace.
- Secondary path: upload a supported broker CSV export.
- No broker login, no brokerage connection, no order execution.
- Not investment advice and not a return-prediction tool.
- Anonymous beta workspaces are isolated and expire after 72 hours by default.

### Key Highlights

- **Sample-first onboarding**: one click creates a temporary workspace and imports anonymous demo trades.
- **Workspace isolation**: each anonymous workspace has its own SQLite database and token.
- **CSV preflight**: validates broker format before creating an analysis task.
- **Smart position matching**: FIFO matching handles partial fills, shorts, options, and orphan closing trades.
- **Behavior-first AI Coach**: highlights habits such as revenge trading and single-trade risk.
- **Counterfactual backtests**: estimate how historical outcomes would change under simple discipline rules.
- **Bilingual UI**: Chinese and English interface with responsive desktop/mobile layouts.

## Product Hunt Beta Status

Current beta target: `beta.<domain>` with API at `api-beta.<domain>` or an equivalent Railway custom domain.

Implemented for beta:

- `Try Sample Data` landing CTA.
- `Upload Your CSV` secondary CTA with import preflight.
- Anonymous `workspace_token` stored in localStorage and sent through `X-Workspace-Token`.
- Isolated workspace databases under `data/workspaces/`.
- `Delete My Data` for the current workspace.
- 72-hour workspace TTL with lazy cleanup.
- Production-safe copy: CSV-only, no broker login, no order execution, not investment advice.

Not in beta scope:

- Broker account connection or automated sync.
- User accounts, subscriptions, or billing.
- Excel import.
- Trading execution or recommendations.
- Guaranteed performance improvement claims.

## Privacy and Data Handling

TradingCoach is designed as a review tool, not a trading terminal.

- Uploaded CSV files are parsed only for the current workspace analysis.
- The beta does not ask for broker credentials.
- Workspaces are anonymous and token-based.
- Data is isolated by workspace database, not shared across visitors.
- Temporary workspaces expire after `WORKSPACE_TTL_HOURS` hours, default `72`.
- Users can delete the current workspace through `DELETE /api/v1/workspaces/current`.

Production deployment must set:

```bash
DEBUG=false
CORS_ORIGINS=https://beta.<domain>
ADMIN_TOKEN=<openssl rand -hex 32>
WORKSPACE_TTL_HOURS=72
WORKSPACE_DATA_DIR=/app/data/workspaces
```

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
│           React 19 + Vite 7 + TypeScript + Tailwind             │
│              Recharts + Lightweight Charts + i18n               │
│                    http://localhost:5173                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API (40+ endpoints)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Backend                                 │
│           FastAPI + Pydantic v2 + SQLAlchemy 2.0                │
│    Task Manager + Workspace Service + Insight Engine            │
│                    http://localhost:8000                         │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐
│  Workspace DBs   │ │  Sample Dataset  │ │   yfinance   │
│ data/workspaces/ │ │ anonymous CSV    │ │ Market Data  │
└──────────────────┘ └──────────────────┘ └──────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.11 recommended
- Node.js 20 recommended
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/BENZEMA216/tradingcoach.git
cd tradingcoach

# Setup Python environment
python3.11 -m venv venv
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
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
VITE_API_PROXY_TARGET=http://127.0.0.1:8000 npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- API Docs in local debug mode: http://localhost:8000/api/v1/docs
- Health check: http://localhost:8000/health

For the exact dogfood setup used in QA:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
cd frontend
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1 npm run dev -- --host 127.0.0.1 --port 5174
```

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
│   │   │   ├── workspace_service.py # Anonymous beta workspace lifecycle
│   │   │   ├── sample_data.py       # One-click sample import
│   │   │   ├── task_manager.py      # Async task processing
│   │   │   └── insight_engine.py    # AI insights generation
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
├── data/                       # Local SQLite data, ignored in git
│   └── workspaces/             # Anonymous beta workspace DBs, ignored in git
└── project_docs/              # Documentation
```

---

## API Reference

### Workspaces
| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/workspaces` | Create an anonymous temporary workspace |
| `GET /api/v1/workspaces/current` | Resolve the current workspace token |
| `DELETE /api/v1/workspaces/current` | Delete current workspace data |
| `POST /api/v1/workspaces/sample` | Create a workspace and import anonymous sample data |

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
| `GET /api/v1/statistics/performance` | Performance metrics |
| `GET /api/v1/statistics/monthly-pnl` | Monthly breakdown |
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
| `POST /api/v1/upload/trades/preview` | Read-only CSV preflight |
| `POST /api/v1/tasks/create` | Upload CSV and create async analysis task |
| `GET /api/v1/tasks/{task_id}` | Task status polling |
| `DELETE /api/v1/tasks/{task_id}` | Cancel pending task |

Most data endpoints require `X-Workspace-Token` in beta mode. Without a token,
read endpoints return an empty workspace view; invalid or expired tokens return
`401`.

Full API documentation in local debug mode: http://localhost:8000/api/v1/docs

---

## Technology Stack

| Category | Technology |
|----------|------------|
| **Backend** | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| **Frontend** | React 19, Vite 7, TypeScript 5.9, Tailwind CSS |
| **State Management** | TanStack Query (React Query) |
| **Charts** | Recharts, Lightweight Charts |
| **Internationalization** | react-i18next |
| **Database** | SQLite global metadata DB + per-workspace SQLite DBs |
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
- [x] Counterfactual backtest page
- [x] Anonymous workspace isolation
- [x] Sample-first Product Hunt beta flow
- [x] Delete current workspace data
- [x] Mobile smoke-tested landing flow
- [x] Docker support
- [x] Railway deployment config

### Next
- [ ] Production beta deployment on `beta.<domain>` and `api-beta.<domain>`
- [ ] Product Hunt gallery and 30-45 second demo video
- [ ] Broker format feedback loop for beta users
- [ ] Advanced options analytics
- [ ] Excel import support
- [ ] Optional real broker connection / sync, without trading execution

---

## Deployment

### Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
```

### Product Hunt Beta Deployment

Frontend:

```bash
cd frontend
VITE_API_BASE_URL=https://api-beta.<domain>/api/v1 npm run build
```

Backend:

```bash
DEBUG=false
CORS_ORIGINS=https://beta.<domain>
ADMIN_TOKEN=<openssl rand -hex 32>
WORKSPACE_TTL_HOURS=72
WORKSPACE_DATA_DIR=/app/data/workspaces
```

See [DEPLOY.md](DEPLOY.md) and [Product Hunt beta release notes](project_docs/PRODUCT_HUNT_BETA_RELEASE_20260529.md).

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

**Version**: v1.0.0 beta | **Last Updated**: 2026-05-29

Made with dedication for traders who want to improve.

</div>
