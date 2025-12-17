"""
API v1 Router - Aggregates all endpoint routers
"""

from fastapi import APIRouter

from .endpoints import dashboard, positions, trades, market_data, statistics, system, ai_coach

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

api_router.include_router(
    positions.router,
    prefix="/positions",
    tags=["Positions"]
)

api_router.include_router(
    trades.router,
    prefix="/trades",
    tags=["Trades"]
)

api_router.include_router(
    market_data.router,
    prefix="/market-data",
    tags=["Market Data"]
)

api_router.include_router(
    statistics.router,
    prefix="/statistics",
    tags=["Statistics"]
)

api_router.include_router(
    system.router,
    prefix="/system",
    tags=["System"]
)

api_router.include_router(
    ai_coach.router,
    tags=["AI Coach"]
)
