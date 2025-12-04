"""
API Tests for Trading Coach Backend
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.main import app

client = TestClient(app)


class TestRootEndpoints:
    """Test root and health endpoints"""

    def test_root(self):
        """Test root endpoint returns app info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert data["app"] == "Trading Coach API"

    def test_health(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestDashboardEndpoints:
    """Test dashboard API endpoints"""

    def test_get_kpis(self):
        """Test dashboard KPIs endpoint"""
        response = client.get("/api/v1/dashboard/kpis")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "total_pnl" in data
        assert "win_rate" in data
        assert "avg_score" in data
        assert "trade_count" in data
        assert "total_fees" in data
        assert "avg_holding_days" in data

        # Check types
        assert isinstance(data["total_pnl"], (int, float))
        assert isinstance(data["win_rate"], (int, float))
        assert isinstance(data["trade_count"], int)

    def test_get_kpis_with_date_filter(self):
        """Test dashboard KPIs with date filter"""
        response = client.get(
            "/api/v1/dashboard/kpis",
            params={"date_start": "2024-01-01", "date_end": "2025-12-31"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_pnl" in data

    def test_get_equity_curve(self):
        """Test equity curve endpoint"""
        response = client.get("/api/v1/dashboard/equity-curve")
        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "total_pnl" in data
        assert isinstance(data["data"], list)

    def test_get_recent_trades(self):
        """Test recent trades endpoint"""
        response = client.get("/api/v1/dashboard/recent-trades")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            trade = data[0]
            assert "id" in trade
            assert "symbol" in trade
            assert "net_pnl" in trade

    def test_get_strategy_breakdown(self):
        """Test strategy breakdown endpoint"""
        response = client.get("/api/v1/dashboard/strategy-breakdown")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "strategy" in item
            assert "count" in item
            assert "total_pnl" in item
            assert "win_rate" in item


class TestPositionsEndpoints:
    """Test positions API endpoints"""

    def test_list_positions(self):
        """Test positions list endpoint"""
        response = client.get("/api/v1/positions")
        assert response.status_code == 200
        data = response.json()

        # Check pagination structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_list_positions_with_pagination(self):
        """Test positions with pagination params"""
        response = client.get(
            "/api/v1/positions",
            params={"page": 1, "page_size": 10}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) <= 10

    def test_list_positions_with_filters(self):
        """Test positions with filters"""
        response = client.get(
            "/api/v1/positions",
            params={
                "direction": "long",
                "status": "closed",
                "is_winner": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_position_detail(self):
        """Test position detail endpoint"""
        # First get a position ID
        list_response = client.get("/api/v1/positions", params={"page_size": 1})
        assert list_response.status_code == 200
        positions = list_response.json()["items"]

        if len(positions) > 0:
            position_id = positions[0]["id"]
            response = client.get(f"/api/v1/positions/{position_id}")
            assert response.status_code == 200
            data = response.json()

            # Check required fields
            assert data["id"] == position_id
            assert "symbol" in data
            assert "direction" in data
            assert "scores" in data
            assert "risk_metrics" in data

    def test_get_position_not_found(self):
        """Test position not found"""
        response = client.get("/api/v1/positions/999999")
        assert response.status_code == 404

    def test_get_position_summary(self):
        """Test position summary endpoint"""
        response = client.get("/api/v1/positions/summary")
        assert response.status_code == 200
        data = response.json()

        assert "total_positions" in data
        assert "closed_positions" in data
        assert "total_pnl" in data
        assert "win_rate" in data


class TestTradesEndpoints:
    """Test trades API endpoints"""

    def test_list_trades(self):
        """Test trades list endpoint"""
        response = client.get("/api/v1/trades")
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_get_trade_summary(self):
        """Test trade summary endpoint"""
        response = client.get("/api/v1/trades/summary")
        assert response.status_code == 200
        data = response.json()

        assert "total_trades" in data
        assert "buy_trades" in data
        assert "sell_trades" in data
        assert "total_fees" in data


class TestMarketDataEndpoints:
    """Test market data API endpoints"""

    def test_get_market_data(self):
        """Test market data endpoint"""
        # Use a symbol that should have data
        response = client.get("/api/v1/market-data/AMZN")

        # Could be 200 or 404 depending on data
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "symbol" in data
            assert "candles" in data
            assert isinstance(data["candles"], list)


class TestStatisticsEndpoints:
    """Test statistics API endpoints"""

    def test_get_performance_metrics(self):
        """Test performance metrics endpoint"""
        response = client.get("/api/v1/statistics/performance")
        assert response.status_code == 200
        data = response.json()

        assert "total_pnl" in data
        assert "total_trades" in data
        assert "win_rate" in data
        assert "avg_win" in data
        assert "avg_loss" in data

    def test_get_symbol_breakdown(self):
        """Test symbol breakdown endpoint"""
        response = client.get("/api/v1/statistics/by-symbol")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "symbol" in item
            assert "count" in item
            assert "total_pnl" in item

    def test_get_grade_breakdown(self):
        """Test grade breakdown endpoint"""
        response = client.get("/api/v1/statistics/by-grade")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    def test_get_direction_breakdown(self):
        """Test direction breakdown endpoint"""
        response = client.get("/api/v1/statistics/by-direction")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    def test_get_monthly_pnl(self):
        """Test monthly P&L endpoint"""
        response = client.get("/api/v1/statistics/monthly-pnl")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "year" in item
            assert "month" in item
            assert "pnl" in item


class TestSystemEndpoints:
    """Test system API endpoints"""

    def test_get_system_health(self):
        """Test system health endpoint"""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_get_system_stats(self):
        """Test system stats endpoint"""
        response = client.get("/api/v1/system/stats")
        assert response.status_code == 200
        data = response.json()

        assert "database" in data
        assert "positions" in data["database"]
        assert "trades" in data["database"]
        assert "market_data" in data["database"]

    def test_list_symbols(self):
        """Test list symbols endpoint"""
        response = client.get("/api/v1/system/symbols")
        assert response.status_code == 200
        data = response.json()

        assert "symbols" in data
        assert "total" in data
        assert isinstance(data["symbols"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
