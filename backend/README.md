# backend - FastAPI 后端服务

基于 FastAPI 的 RESTful API 服务，为前端 React 应用提供数据接口。

## 设计思路

采用分层架构，将 API 路由、业务逻辑和数据访问分离：

```
backend/
├── app/
│   ├── main.py           # 应用入口
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库连接
│   ├── api/v1/           # API 路由
│   │   ├── router.py     # 路由聚合
│   │   └── endpoints/    # 各端点实现
│   ├── schemas/          # Pydantic 数据模型
│   └── services/         # 业务逻辑层 (计划中)
└── tests/                # API 测试
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 数据验证 | Pydantic |
| ORM | SQLAlchemy (复用 src/models) |
| API 文档 | Swagger / ReDoc |
| 跨域 | CORS Middleware |

## API 端点

### Dashboard `/api/v1/dashboard`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/overview` | 获取总览统计 |
| GET | `/kpis` | 获取 KPI 指标 |
| GET | `/recent-trades` | 获取最近交易 |
| GET | `/equity-curve` | 获取权益曲线数据 |

### Positions `/api/v1/positions`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 获取持仓列表 (分页+过滤) |
| GET | `/{id}` | 获取单个持仓详情 |
| GET | `/symbols` | 获取所有股票代码 |

### Trades `/api/v1/trades`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 获取交易列表 |
| GET | `/{id}` | 获取单笔交易详情 |

### Statistics `/api/v1/statistics`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/summary` | 获取统计摘要 |
| GET | `/by-symbol` | 按股票统计 |
| GET | `/by-month` | 按月份统计 |
| GET | `/by-strategy` | 按策略统计 |

### Market Data `/api/v1/market-data`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/{symbol}` | 获取股票市场数据 |
| GET | `/{symbol}/indicators` | 获取技术指标 |

### System `/api/v1/system`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/database/stats` | 数据库统计 |

## 启动服务

```bash
# 开发模式
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 文档

启动后访问：
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

## 配置

环境变量或 `config.py`:

```python
APP_NAME = "Trading Coach API"
APP_VERSION = "1.0.0"
API_V1_PREFIX = "/api/v1"

# 数据库
DATABASE_URL = "sqlite:///data/tradingcoach.db"

# CORS
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
]
```

## Schemas (数据模型)

### Position Schema
```python
class PositionResponse(BaseModel):
    id: int
    symbol: str
    direction: str
    open_price: float
    close_price: Optional[float]
    quantity: int
    net_pnl: Optional[float]
    overall_score: Optional[float]
    score_grade: Optional[str]
    # ...
```

### Pagination
```python
class PaginatedResponse(BaseModel):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

## 过滤参数

Positions 端点支持多种过滤：
- `symbol`: 股票代码
- `direction`: long/short
- `status`: open/closed
- `is_option`: 0/1
- `min_score` / `max_score`: 评分范围
- `start_date` / `end_date`: 日期范围
- `sort_by` / `sort_order`: 排序

## 测试

```bash
# 运行 API 测试
cd backend
python -m pytest tests/ -v
```

## 架构改进计划

当前 endpoints 直接包含业务逻辑，计划重构为：

```
Request → Endpoint → Service → Repository → Database
```

- **Service 层**: 封装业务逻辑
- **Repository 层**: 封装数据访问
- **Mapper 层**: 数据转换
