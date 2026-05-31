"""
Anonymous workspace API

input: X-Workspace-Token header or no-auth create request
output: temporary workspace token, sample import, delete-current-workspace result
pos: backend API layer - Product Hunt beta anonymous workspace lifecycle
"""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from backend.app.services.sample_data import import_sample_dataset
from backend.app.services.workspace_service import workspace_service

router = APIRouter()


class WorkspaceResponse(BaseModel):
    workspace_id: str
    workspace_token: str
    created_at: str
    expires_at: str
    ttl_hours: int


class WorkspaceCurrentResponse(BaseModel):
    workspace_id: str
    created_at: str
    expires_at: str
    ttl_hours: int


class WorkspaceDeleteResponse(BaseModel):
    deleted: bool
    workspace_id: Optional[str]
    deleted_counts: dict


class SampleWorkspaceResponse(WorkspaceResponse):
    sample: dict


def _require_workspace_token(token: Optional[str]):
    workspace = workspace_service.resolve_token(token)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired workspace token.",
        )
    return workspace


@router.post("", response_model=WorkspaceResponse)
async def create_workspace():
    """Create a new anonymous temporary workspace."""
    workspace = workspace_service.create_workspace()
    return WorkspaceResponse(**workspace.public_dict())


@router.get("/current", response_model=WorkspaceCurrentResponse)
async def get_current_workspace(
    x_workspace_token: Optional[str] = Header(None, alias="X-Workspace-Token"),
):
    """Return metadata for the current workspace token."""
    workspace = _require_workspace_token(x_workspace_token)
    return WorkspaceCurrentResponse(**workspace.public_dict())


@router.delete("/current", response_model=WorkspaceDeleteResponse)
async def delete_current_workspace(
    x_workspace_token: Optional[str] = Header(None, alias="X-Workspace-Token"),
):
    """Delete the current workspace data and invalidate the token."""
    result = workspace_service.delete_workspace(x_workspace_token)
    if not result.deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired workspace token.",
        )
    return WorkspaceDeleteResponse(
        deleted=result.deleted,
        workspace_id=result.workspace_id,
        deleted_counts=result.deleted_counts,
    )


@router.post("/sample", response_model=SampleWorkspaceResponse)
async def create_sample_workspace():
    """Create a new workspace and import bundled anonymous sample trades."""
    workspace = workspace_service.create_workspace()
    try:
        sample_result = import_sample_dataset(workspace.database_url)
    except Exception:
        workspace_service.delete_workspace(workspace.token)
        raise

    payload = workspace.public_dict()
    payload["sample"] = sample_result
    return SampleWorkspaceResponse(**payload)
