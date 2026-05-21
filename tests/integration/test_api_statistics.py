"""
API Integration Tests - Statistics Endpoints

input: backend/app/api/v1/endpoints/statistics.py
output: 验证 Statistics API 端点的完整请求-响应流程
pos: 集成测试 - 测试统计 API 端点的实际行为

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import pytest
from datetime import date, datetime

from src.models import Position
from src.models.position import PositionStatus


def _add_closed_position(
    test_db,
    *,
    symbol: str,
    close_day: date,
    net_pnl: float,
    realized_pnl: float | None = None,
    total_fees: float = 0.0,
    score_grade: str | None = "C",
    currency: str = "USD",
) -> Position:
    position = Position(
        symbol=symbol,
        symbol_name=f"{symbol} Inc.",
        direction="long",
        status=PositionStatus.CLOSED,
        open_time=datetime(close_day.year, close_day.month, close_day.day, 9, 30),
        close_time=datetime(close_day.year, close_day.month, close_day.day, 16, 0),
        open_date=close_day,
        close_date=close_day,
        holding_period_days=0,
        open_price=100,
        close_price=110,
        quantity=10,
        realized_pnl=realized_pnl if realized_pnl is not None else net_pnl + total_fees,
        net_pnl=net_pnl,
        total_fees=total_fees,
        overall_score=70,
        score_grade=score_grade,
        market="美股",
        currency=currency,
    )
    test_db.add(position)
    return position


class TestStatisticsAPI:
    """测试 Statistics API 端点"""

    def test_get_performance_metrics_empty(self, client):
        """测试空数据库的性能指标"""
        response = client.get("/api/v1/statistics/performance")
        assert response.status_code == 200
        data = response.json()
        assert data["total_pnl"] == 0.0
        assert data["total_trades"] == 0
        assert data["win_rate"] == 0.0

    def test_get_performance_metrics_with_data(self, client_with_data):
        """测试有数据时的性能指标"""
        response = client_with_data.get("/api/v1/statistics/performance")
        assert response.status_code == 200
        data = response.json()
        assert "total_pnl" in data
        assert "total_trades" in data
        assert "win_rate" in data
        assert "avg_win" in data
        assert "avg_loss" in data
        assert data["total_trades"] > 0

    def test_get_symbol_breakdown_empty(self, client):
        """测试空数据库的标的分解"""
        response = client.get("/api/v1/statistics/by-symbol")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_symbol_breakdown_with_data(self, client_with_data):
        """测试有数据时的标的分解"""
        response = client_with_data.get("/api/v1/statistics/by-symbol")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            item = data[0]
            assert "symbol" in item
            assert "count" in item
            assert "total_pnl" in item
            assert "win_rate" in item

    def test_get_grade_breakdown(self, client_with_data):
        """测试评分等级分解"""
        response = client_with_data.get("/api/v1/statistics/by-grade")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "grade" in item
            assert "count" in item
            assert "total_pnl" in item

    def test_get_grade_breakdown_includes_incomplete_grade_suffixes(self, client, test_db):
        """真实数据中的 C? 等降级评分不应被 by-grade 静默丢弃"""
        _add_closed_position(
            test_db,
            symbol="AAPL",
            close_day=date(2026, 1, 2),
            net_pnl=100,
            score_grade="C+?",
        )
        _add_closed_position(
            test_db,
            symbol="MSFT",
            close_day=date(2026, 1, 3),
            net_pnl=-40,
            score_grade="C?",
        )
        _add_closed_position(
            test_db,
            symbol="NVDA",
            close_day=date(2026, 1, 4),
            net_pnl=25,
            score_grade="C-?",
        )
        _add_closed_position(
            test_db,
            symbol="TSLA",
            close_day=date(2026, 1, 5),
            net_pnl=10,
            score_grade=None,
        )
        test_db.commit()

        response = client.get("/api/v1/statistics/by-grade")

        assert response.status_code == 200
        grades = {item["grade"] for item in response.json()}
        assert {"C+?", "C?", "C-?", "N/A"}.issubset(grades)

    def test_performance_and_risk_metrics_use_same_sharpe_ratio(self, client, test_db):
        """同一份数据下 performance 和 risk-metrics 的 Sharpe 必须一致"""
        for index, pnl in enumerate([100, -30, 80, -20, 60], start=1):
            _add_closed_position(
                test_db,
                symbol=f"T{index}",
                close_day=date(2026, 2, index),
                net_pnl=pnl,
                score_grade="B",
            )
        test_db.commit()

        performance = client.get("/api/v1/statistics/performance").json()
        risk = client.get("/api/v1/statistics/risk-metrics").json()

        assert performance["sharpe_ratio"] is not None
        assert performance["sharpe_ratio"] == risk["sharpe_ratio"]

    def test_fee_percentage_uses_realized_pnl_when_net_pnl_is_small(self, client, test_db):
        """手续费占比应使用更稳定的未扣费盈亏，避免净盈亏接近 0 时夸大"""
        _add_closed_position(
            test_db,
            symbol="FEE",
            close_day=date(2026, 3, 1),
            realized_pnl=1000,
            net_pnl=100,
            total_fees=900,
            score_grade="C",
        )
        test_db.commit()

        response = client.get("/api/v1/statistics/performance")

        assert response.status_code == 200
        assert response.json()["fees_pct_of_pnl"] == 90.0

    def test_get_direction_breakdown(self, client_with_data):
        """测试方向分解"""
        response = client_with_data.get("/api/v1/statistics/by-direction")
        assert response.status_code == 200
        data = response.json()
        directions = [item["direction"] for item in data]
        # 应该只有 long 或 short
        for d in directions:
            assert d in ["long", "short", "unknown"]

    def test_get_holding_period_breakdown(self, client_with_data):
        """测试持仓周期分解"""
        response = client_with_data.get("/api/v1/statistics/by-holding-period")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "period_label" in item
            assert "min_days" in item
            assert "max_days" in item
            assert "count" in item

    def test_get_monthly_pnl(self, client_with_data):
        """测试月度盈亏"""
        response = client_with_data.get("/api/v1/statistics/monthly-pnl")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "year" in item
            assert "month" in item
            assert "pnl" in item
            assert 1 <= item["month"] <= 12


class TestStatisticsAPIAdvanced:
    """测试高级统计 API 端点"""

    def test_get_equity_drawdown(self, client_with_data):
        """测试权益回撤数据"""
        response = client_with_data.get("/api/v1/statistics/equity-drawdown")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            item = data[0]
            assert "date" in item
            assert "cumulative_pnl" in item
            assert "drawdown" in item

    def test_get_pnl_distribution(self, client_with_data):
        """测试盈亏分布"""
        response = client_with_data.get("/api/v1/statistics/pnl-distribution")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "min_value" in item
            assert "max_value" in item
            assert "count" in item
            assert item["count"] >= 0

    def test_get_duration_pnl(self, client_with_data):
        """测试持仓时长与盈亏关系"""
        response = client_with_data.get("/api/v1/statistics/duration-pnl")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "holding_days" in item
            assert "pnl" in item
            assert "symbol" in item

    def test_get_symbol_risk(self, client_with_data):
        """测试标的风险数据"""
        response = client_with_data.get("/api/v1/statistics/symbol-risk?min_trades=1")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "symbol" in item
            assert "avg_win" in item
            assert "avg_loss" in item
            assert "trade_count" in item

    def test_get_hourly_performance(self, client_with_data):
        """测试小时绩效"""
        response = client_with_data.get("/api/v1/statistics/hourly-performance")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "hour" in item
            assert 0 <= item["hour"] <= 23
            assert "trade_count" in item
            assert "win_rate" in item

    def test_get_trading_heatmap(self, client_with_data):
        """测试交易热力图"""
        response = client_with_data.get("/api/v1/statistics/trading-heatmap")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "day_of_week" in item
            assert 0 <= item["day_of_week"] <= 6
            assert "hour" in item
            assert "trade_count" in item

    def test_get_asset_type_breakdown(self, client_with_data):
        """测试资产类型分解"""
        response = client_with_data.get("/api/v1/statistics/by-asset-type")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "asset_type" in item
            assert item["asset_type"] in ["stock", "option"]
            assert "count" in item
            assert "total_pnl" in item


class TestStatisticsAPIFilters:
    """测试统计 API 的日期筛选"""

    def test_performance_with_date_range(self, client_with_data):
        """测试带日期范围的性能指标"""
        response = client_with_data.get(
            "/api/v1/statistics/performance?date_start=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 200

    def test_symbol_breakdown_with_limit(self, client_with_data):
        """测试标的分解的数量限制"""
        response = client_with_data.get("/api/v1/statistics/by-symbol?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_rolling_metrics(self, client_with_data):
        """测试滚动指标"""
        response = client_with_data.get("/api/v1/statistics/rolling-metrics?window=5")
        assert response.status_code == 200
        # 窗口大小可能大于数据量，可能返回空


class TestRiskMetricsAPI:
    """测试风险指标 API"""

    def test_get_risk_metrics_empty(self, client):
        """测试空数据库的风险指标"""
        response = client.get("/api/v1/statistics/risk-metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["max_drawdown"] == 0.0

    def test_get_risk_metrics_with_data(self, client_with_data):
        """测试有数据时的风险指标"""
        response = client_with_data.get("/api/v1/statistics/risk-metrics")
        assert response.status_code == 200
        data = response.json()
        assert "max_drawdown" in data
        assert "sharpe_ratio" in data
        assert "sortino_ratio" in data
        assert "expectancy" in data

    def test_get_risk_metrics_custom_risk_free_rate(self, client_with_data):
        """测试自定义无风险利率"""
        response = client_with_data.get("/api/v1/statistics/risk-metrics?risk_free_rate=0.03")
        assert response.status_code == 200

    def test_get_drawdowns(self, client_with_data):
        """测试回撤周期列表"""
        response = client_with_data.get("/api/v1/statistics/drawdowns")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert "start_date" in item
            assert "drawdown" in item
            assert item["drawdown"] >= 0
