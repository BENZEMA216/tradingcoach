"""
Workspace service tests

input: temporary workspace registry
output: token lifecycle and isolated database URLs
pos: unit tests - anonymous beta workspace lifecycle
"""

from datetime import datetime, timedelta, timezone

from backend.app.services.workspace_service import WorkspaceService


def test_workspace_create_resolve_and_delete(tmp_path):
    service = WorkspaceService(root_dir=tmp_path, ttl_hours=72)

    created = service.create_workspace()
    resolved = service.resolve_token(created.token)

    assert created.token
    assert resolved is not None
    assert resolved.workspace_id == created.workspace_id
    assert resolved.database_url.startswith("sqlite:///")
    assert (tmp_path / created.workspace_id / "tradingcoach.db").exists()

    result = service.delete_workspace(created.token)

    assert result.deleted is True
    assert result.workspace_id == created.workspace_id
    assert service.resolve_token(created.token) is None
    assert not (tmp_path / created.workspace_id / "tradingcoach.db").exists()


def test_workspace_expired_token_is_cleaned_up(tmp_path):
    now = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)
    service = WorkspaceService(root_dir=tmp_path, ttl_hours=1, clock=lambda: now)

    created = service.create_workspace()
    assert service.resolve_token(created.token) is not None

    service.clock = lambda: now + timedelta(hours=2)

    assert service.resolve_token(created.token) is None
    assert not (tmp_path / created.workspace_id / "tradingcoach.db").exists()
