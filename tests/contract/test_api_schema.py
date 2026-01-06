"""
API Contract Tests - 验证 API 响应结构

input: backend/app/schemas/*.py, OpenAPI schema
output: 验证 API 响应符合定义的 schema
pos: 契约测试 - 确保前后端 API 契约一致性

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import pytest
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestPositionSchemaContract:
    """Position API 响应结构契约测试"""

    def test_position_list_item_schema(self):
        """测试 PositionListItem schema 结构"""
        from backend.app.schemas.position import PositionListItem
        from datetime import date, datetime

        # 有效数据应该通过验证
        valid_data = {
            "id": 1,
            "symbol": "AAPL",
            "symbol_name": "Apple Inc.",
            "direction": "long",
            "status": "closed",
            "open_date": date(2024, 1, 1),
            "close_date": date(2024, 1, 15),
            "holding_period_days": 14,
            "open_price": 150.25,
            "close_price": 160.50,
            "quantity": 100,
            "net_pnl": 1025.00,
            "net_pnl_pct": 6.82,
            "overall_score": 85.5,
            "score_grade": "B+",
            "strategy_type": "trend",
            "reviewed_at": None,
        }

        item = PositionListItem(**valid_data)
        assert item.id == 1
        assert item.symbol == "AAPL"
        assert item.direction == "long"

    def test_position_list_item_required_fields(self):
        """测试 PositionListItem 必填字段"""
        from backend.app.schemas.position import PositionListItem

        # 缺少必填字段应该失败
        invalid_data = {
            "symbol": "AAPL",
            # 缺少 id
        }

        with pytest.raises(ValidationError):
            PositionListItem(**invalid_data)

    def test_position_detail_schema(self):
        """测试 PositionDetail schema 结构"""
        from backend.app.schemas.position import PositionDetail, PositionScoreDetail, PositionRiskMetrics
        from datetime import date, datetime

        valid_data = {
            "id": 1,
            "symbol": "AAPL",
            "symbol_name": "Apple Inc.",
            "direction": "long",
            "status": "closed",
            "open_time": datetime(2024, 1, 1, 10, 30),
            "close_time": datetime(2024, 1, 15, 14, 45),
            "open_date": date(2024, 1, 1),
            "close_date": date(2024, 1, 15),
            "holding_period_days": 14,
            "holding_period_hours": 340.25,
            "open_price": 150.25,
            "close_price": 160.50,
            "quantity": 100,
            "realized_pnl": 1050.00,
            "realized_pnl_pct": 6.99,
            "total_fees": 25.00,
            "open_fee": 12.50,
            "close_fee": 12.50,
            "net_pnl": 1025.00,
            "net_pnl_pct": 6.82,
            "market": "美股",
            "currency": "USD",
            "is_option": False,
            "underlying_symbol": None,
            "scores": {
                "entry_quality_score": 80.0,
                "exit_quality_score": 85.0,
                "trend_quality_score": 75.0,
                "risk_mgmt_score": 90.0,
                "overall_score": 82.5,
                "score_grade": "B",
            },
            "risk_metrics": {
                "mae": None,
                "mae_pct": None,
                "mae_time": None,
                "mfe": None,
                "mfe_pct": None,
                "mfe_time": None,
                "risk_reward_ratio": None,
            },
            "strategy_type": "trend",
            "strategy_confidence": 75.0,
            "entry_indicators": None,
            "exit_indicators": None,
            "post_exit_5d_pct": None,
            "post_exit_10d_pct": None,
            "post_exit_20d_pct": None,
            "review_notes": None,
            "emotion_tag": None,
            "discipline_score": None,
            "reviewed_at": None,
            "analysis_notes": None,
            "news_context": None,
            "trade_ids": [1, 2],
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 15),
        }

        item = PositionDetail(**valid_data)
        assert item.id == 1
        assert item.scores.overall_score == 82.5


class TestStatisticsSchemaContract:
    """Statistics API 响应结构契约测试"""

    def test_performance_metrics_schema(self):
        """测试 PerformanceMetrics schema 结构"""
        from backend.app.schemas.statistics import PerformanceMetrics

        valid_data = {
            "total_pnl": 15000.50,
            "total_trades": 150,
            "winners": 90,
            "losers": 60,
            "win_rate": 60.0,
            "avg_win": 250.00,
            "avg_loss": -150.00,
            "avg_pnl": 100.00,
            "profit_factor": 1.67,
            "max_drawdown": 5000.00,
            "max_drawdown_pct": 8.5,
            "max_consecutive_wins": 8,
            "max_consecutive_losses": 4,
            "total_fees": 750.00,
            "fees_pct_of_pnl": 5.0,
            "avg_holding_days": 7.5,
            "avg_winner_holding_days": 5.2,
            "avg_loser_holding_days": 10.3,
        }

        metrics = PerformanceMetrics(**valid_data)
        assert metrics.total_pnl == 15000.50
        assert metrics.win_rate == 60.0

    def test_symbol_breakdown_item_schema(self):
        """测试 SymbolBreakdownItem schema 结构"""
        from backend.app.schemas.statistics import SymbolBreakdownItem

        valid_data = {
            "symbol": "AAPL",
            "symbol_name": "Apple Inc.",
            "count": 25,
            "total_pnl": 5000.00,
            "win_rate": 68.0,
            "avg_pnl": 200.00,
            "avg_holding_days": 5.5,
        }

        item = SymbolBreakdownItem(**valid_data)
        assert item.symbol == "AAPL"
        assert item.count == 25

    def test_risk_metrics_schema(self):
        """测试 RiskMetrics schema 结构"""
        from backend.app.schemas.statistics import RiskMetrics

        valid_data = {
            "max_drawdown": 5000.00,
            "max_drawdown_pct": 10.5,
            "avg_drawdown": 2500.00,
            "current_drawdown": 1000.00,
            "sharpe_ratio": 1.25,
            "sortino_ratio": 1.85,
            "calmar_ratio": 2.1,
            "var_95": 500.00,
            "expected_shortfall": 750.00,
            "profit_factor": 1.67,
            "payoff_ratio": 1.5,
            "expectancy": 100.00,
            "daily_volatility": 150.00,
            "annualized_volatility": 2400.00,
        }

        metrics = RiskMetrics(**valid_data)
        assert metrics.sharpe_ratio == 1.25


class TestPaginatedResponseContract:
    """分页响应契约测试"""

    def test_paginated_response_structure(self):
        """测试分页响应结构"""
        from backend.app.schemas.common import PaginatedResponse
        from backend.app.schemas.position import PositionListItem
        from datetime import date

        items = [
            PositionListItem(
                id=i,
                symbol="AAPL",
                direction="long",
                status="closed",
                open_date=date(2024, 1, 1),
                open_price=150.0,
                quantity=100,
            )
            for i in range(5)
        ]

        response = PaginatedResponse[PositionListItem](
            items=items,
            total=100,
            page=1,
            page_size=5,
            total_pages=20,
        )

        assert len(response.items) == 5
        assert response.total == 100
        assert response.page == 1
        assert response.total_pages == 20


class TestOpenAPISchemaContract:
    """OpenAPI Schema 契约测试"""

    def test_openapi_schema_accessible(self, client):
        """测试 OpenAPI schema 可访问"""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_openapi_paths_defined(self, client):
        """测试关键路径在 OpenAPI 中定义"""
        response = client.get("/api/v1/openapi.json")
        schema = response.json()
        paths = schema["paths"]

        # 验证关键路径存在
        expected_paths = [
            "/api/v1/positions",
            "/api/v1/statistics/performance",
            "/api/v1/dashboard/kpis",
        ]

        for path in expected_paths:
            assert path in paths, f"Path {path} not found in OpenAPI schema"

    def test_openapi_response_schemas(self, client):
        """测试响应 schema 定义"""
        response = client.get("/api/v1/openapi.json")
        schema = response.json()

        # 验证组件 schema 存在
        if "components" in schema and "schemas" in schema["components"]:
            schemas = schema["components"]["schemas"]
            expected_schemas = [
                "PositionListItem",
                "PerformanceMetrics",
            ]

            for schema_name in expected_schemas:
                assert schema_name in schemas, f"Schema {schema_name} not found"


class TestAPIResponseConsistency:
    """API 响应一致性测试"""

    def test_error_response_format(self, client):
        """测试错误响应格式一致性"""
        # 请求不存在的资源
        response = client.get("/api/v1/positions/99999")
        assert response.status_code == 404

        error = response.json()
        assert "detail" in error

    def test_validation_error_format(self, client):
        """测试验证错误响应格式"""
        response = client.get("/api/v1/positions?page=-1")
        assert response.status_code == 422

        error = response.json()
        assert "detail" in error

    def test_empty_response_format(self, client):
        """测试空数据响应格式"""
        response = client.get("/api/v1/positions")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
