"""
Workspace API tests

input: anonymous workspace token API
output: isolated stats and delete semantics
pos: integration tests - PH beta temporary workspace behavior
"""

from datetime import datetime, date

from fastapi.testclient import TestClient

from backend.app.main import app
from src.models.position import Position, PositionStatus


def _create_workspace(client: TestClient):
    response = client.post("/api/v1/workspaces")
    assert response.status_code == 200
    return response.json()


def test_workspace_token_is_required_to_see_workspace_data():
    with TestClient(app) as client:
        first = _create_workspace(client)
        second = _create_workspace(client)

        from backend.app.database import get_session_factory_for_database_url
        from backend.app.services.workspace_service import workspace_service

        first_record = workspace_service.resolve_token(first["workspace_token"])
        second_record = workspace_service.resolve_token(second["workspace_token"])
        assert first_record is not None
        assert second_record is not None

        FirstSession = get_session_factory_for_database_url(first_record.database_url)
        with FirstSession() as session:
            session.add(
                Position(
                    symbol="AAPL",
                    status=PositionStatus.CLOSED,
                    direction="long",
                    open_time=datetime(2026, 1, 1, 14, 30),
                    close_time=datetime(2026, 1, 2, 14, 30),
                    open_date=date(2026, 1, 1),
                    close_date=date(2026, 1, 2),
                    open_price=100,
                    close_price=110,
                    quantity=10,
                    net_pnl=100,
                    currency="USD",
                )
            )
            session.commit()

        first_stats = client.get(
            "/api/v1/system/stats",
            headers={"X-Workspace-Token": first["workspace_token"]},
        )
        second_stats = client.get(
            "/api/v1/system/stats",
            headers={"X-Workspace-Token": second["workspace_token"]},
        )
        no_token_stats = client.get("/api/v1/system/stats")

        assert first_stats.status_code == 200
        assert first_stats.json()["database"]["positions"]["count"] == 1
        assert second_stats.status_code == 200
        assert second_stats.json()["database"]["positions"]["count"] == 0
        assert no_token_stats.status_code == 200
        assert no_token_stats.json()["database"]["positions"]["count"] == 0

        client.delete(
            "/api/v1/workspaces/current",
            headers={"X-Workspace-Token": first["workspace_token"]},
        )
        client.delete(
            "/api/v1/workspaces/current",
            headers={"X-Workspace-Token": second["workspace_token"]},
        )


def test_delete_current_workspace_invalidates_token():
    with TestClient(app) as client:
        created = _create_workspace(client)

        response = client.delete(
            "/api/v1/workspaces/current",
            headers={"X-Workspace-Token": created["workspace_token"]},
        )

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        stats = client.get(
            "/api/v1/system/stats",
            headers={"X-Workspace-Token": created["workspace_token"]},
        )

        assert stats.status_code == 401


def test_sample_workspace_imports_anonymous_demo_data():
    with TestClient(app) as client:
        response = client.post("/api/v1/workspaces/sample")

        assert response.status_code == 200
        data = response.json()
        assert data["workspace_token"]
        assert data["sample"]["positions_matched"] > 0
        assert data["sample"]["positions_scored"] > 0

        stats = client.get(
            "/api/v1/system/stats",
            headers={"X-Workspace-Token": data["workspace_token"]},
        )

        assert stats.status_code == 200
        assert stats.json()["database"]["positions"]["count"] == data["sample"]["positions_matched"]

        client.delete(
            "/api/v1/workspaces/current",
            headers={"X-Workspace-Token": data["workspace_token"]},
        )
