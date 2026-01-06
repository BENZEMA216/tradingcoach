"""
API Integration Tests - Positions Endpoints

input: backend/app/api/v1/endpoints/positions.py
output: 验证 Positions API 端点的完整请求-响应流程
pos: 集成测试 - 测试 API 端点的实际行为

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import pytest


class TestPositionsAPI:
    """测试 Positions API 端点"""

    def test_list_positions_empty(self, client):
        """测试空数据库返回空列表"""
        response = client.get("/api/v1/positions")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_positions_with_data(self, client_with_data):
        """测试有数据时返回正确的列表"""
        response = client_with_data.get("/api/v1/positions")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert data["total"] > 0

        # 验证响应结构
        item = data["items"][0]
        assert "id" in item
        assert "symbol" in item
        assert "direction" in item
        assert "net_pnl" in item

    def test_list_positions_pagination(self, client_with_data):
        """测试分页功能"""
        response = client_with_data.get("/api/v1/positions?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_list_positions_filter_direction(self, client_with_data):
        """测试按方向筛选"""
        response = client_with_data.get("/api/v1/positions?direction=long")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["direction"] == "long"

    def test_list_positions_filter_is_winner(self, client_with_data):
        """测试按盈亏筛选"""
        response = client_with_data.get("/api/v1/positions?is_winner=true")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["net_pnl"] is None or item["net_pnl"] > 0

    def test_list_positions_sorting(self, client_with_data):
        """测试排序功能"""
        response = client_with_data.get("/api/v1/positions?sort_by=net_pnl&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        if len(items) > 1:
            pnl_values = [i["net_pnl"] or float('-inf') for i in items]
            assert pnl_values == sorted(pnl_values, reverse=True)

    def test_get_position_detail_not_found(self, client):
        """测试获取不存在的持仓返回 404"""
        response = client.get("/api/v1/positions/99999")
        assert response.status_code == 404

    def test_get_position_summary_empty(self, client):
        """测试空数据库的统计摘要"""
        response = client.get("/api/v1/positions/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_positions"] == 0
        assert data["total_pnl"] == 0

    def test_get_position_summary_with_data(self, client_with_data):
        """测试有数据时的统计摘要"""
        response = client_with_data.get("/api/v1/positions/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_positions"] > 0
        assert "win_rate" in data
        assert "avg_pnl" in data


class TestPositionsAPIValidation:
    """测试 Positions API 参数验证"""

    def test_invalid_page_number(self, client):
        """测试无效页码"""
        response = client.get("/api/v1/positions?page=0")
        assert response.status_code == 422  # Validation error

    def test_invalid_page_size(self, client):
        """测试无效页面大小"""
        response = client.get("/api/v1/positions?page_size=999")
        assert response.status_code == 422

    def test_invalid_sort_order(self, client):
        """测试无效排序参数仍然工作（使用默认值）"""
        response = client.get("/api/v1/positions?sort_order=invalid")
        # 应该接受并使用默认排序或忽略无效值
        assert response.status_code in [200, 422]

    def test_invalid_date_format(self, client):
        """测试无效日期格式"""
        response = client.get("/api/v1/positions?date_start=invalid-date")
        assert response.status_code == 422


class TestPositionsAPIEdgeCases:
    """测试边界情况"""

    def test_large_page_number(self, client_with_data):
        """测试超大页码返回空列表"""
        response = client_with_data.get("/api/v1/positions?page=9999")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_combined_filters(self, client_with_data):
        """测试组合筛选条件"""
        response = client_with_data.get(
            "/api/v1/positions?direction=long&is_winner=true&sort_by=net_pnl&sort_order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["direction"] == "long"
            assert item["net_pnl"] is None or item["net_pnl"] > 0
