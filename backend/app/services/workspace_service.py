"""
Anonymous workspace service

input: workspace token / filesystem registry
output: isolated SQLite database URL and token lifecycle operations
pos: backend service layer - Product Hunt beta anonymous data isolation
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import create_engine

import config
from src.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class WorkspaceRecord:
    workspace_id: str
    token_hash: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    db_path: Path
    token: Optional[str] = None

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    def public_dict(self) -> dict:
        data = {
            "workspace_id": self.workspace_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ttl_hours": int((self.expires_at - self.created_at).total_seconds() // 3600),
        }
        if self.token:
            data["workspace_token"] = self.token
        return data


@dataclass(frozen=True)
class WorkspaceDeleteResult:
    deleted: bool
    workspace_id: Optional[str]
    deleted_counts: dict


class WorkspaceService:
    """Filesystem-backed registry for temporary anonymous workspaces."""

    def __init__(
        self,
        root_dir: Optional[Path] = None,
        ttl_hours: Optional[int] = None,
        clock: Callable[[], datetime] = _utcnow,
    ):
        self.root_dir = Path(
            root_dir
            or os.getenv("WORKSPACE_DATA_DIR")
            or (config.DATA_DIR / "workspaces")
        )
        self.ttl_hours = int(
            ttl_hours
            if ttl_hours is not None
            else os.getenv("WORKSPACE_TTL_HOURS", "72")
        )
        self.clock = clock
        self._lock = threading.RLock()

    @property
    def registry_path(self) -> Path:
        return self.root_dir / "registry.json"

    def create_workspace(self) -> WorkspaceRecord:
        """Create a workspace, initialize its SQLite schema, and return its token once."""
        with self._lock:
            self.root_dir.mkdir(parents=True, exist_ok=True)
            registry = self._load_registry()
            registry = self._cleanup_expired_locked(registry)

            workspace_id = uuid.uuid4().hex[:16]
            token = secrets.token_urlsafe(32)
            now = self.clock()
            expires_at = now + timedelta(hours=self.ttl_hours)
            db_path = self.root_dir / workspace_id / "tradingcoach.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)

            record = WorkspaceRecord(
                workspace_id=workspace_id,
                token_hash=_token_hash(token),
                created_at=now,
                last_seen_at=now,
                expires_at=expires_at,
                db_path=db_path,
                token=token,
            )
            registry[workspace_id] = self._serialize_record(record)
            self._write_registry(registry)
            self.ensure_schema(record)
            return record

    def resolve_token(self, token: Optional[str], *, touch: bool = True) -> Optional[WorkspaceRecord]:
        """Resolve an active token. Expired workspaces are lazily deleted."""
        if not token:
            return None

        with self._lock:
            registry = self._load_registry()
            registry = self._cleanup_expired_locked(registry)
            hashed = _token_hash(token)
            for workspace_id, item in registry.items():
                if item.get("token_hash") != hashed:
                    continue
                record = self._deserialize_record(workspace_id, item)
                if record.expires_at <= self.clock():
                    self._delete_record_files(record)
                    registry.pop(workspace_id, None)
                    self._write_registry(registry)
                    return None
                if touch:
                    item["last_seen_at"] = self.clock().isoformat()
                    registry[workspace_id] = item
                    self._write_registry(registry)
                self.ensure_schema(record)
                return record
            self._write_registry(registry)
            return None

    def delete_workspace(self, token: Optional[str]) -> WorkspaceDeleteResult:
        """Delete the current workspace and invalidate its token."""
        if not token:
            return WorkspaceDeleteResult(False, None, {})

        with self._lock:
            registry = self._load_registry()
            hashed = _token_hash(token)
            for workspace_id, item in list(registry.items()):
                if item.get("token_hash") != hashed:
                    continue
                record = self._deserialize_record(workspace_id, item)
                deleted_counts = self._count_workspace_rows(record)
                self._delete_record_files(record)
                registry.pop(workspace_id, None)
                self._write_registry(registry)
                return WorkspaceDeleteResult(True, workspace_id, deleted_counts)
            return WorkspaceDeleteResult(False, None, {})

    def cleanup_expired(self) -> int:
        """Remove expired workspaces and return how many were deleted."""
        with self._lock:
            registry = self._load_registry()
            before = len(registry)
            registry = self._cleanup_expired_locked(registry)
            self._write_registry(registry)
            return before - len(registry)

    def ensure_schema(self, record: WorkspaceRecord) -> None:
        record.db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            record.database_url,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        engine.dispose()

    def _count_workspace_rows(self, record: WorkspaceRecord) -> dict:
        if not record.db_path.exists():
            return {}

        engine = create_engine(record.database_url)
        counts = {}
        try:
            with engine.connect() as connection:
                for table in ("positions", "trades", "import_history", "tasks"):
                    try:
                        counts[table] = connection.exec_driver_sql(
                            f"SELECT COUNT(*) FROM {table}"
                        ).scalar() or 0
                    except Exception:
                        counts[table] = 0
        finally:
            engine.dispose()
        return counts

    def _cleanup_expired_locked(self, registry: dict) -> dict:
        now = self.clock()
        active = {}
        for workspace_id, item in registry.items():
            record = self._deserialize_record(workspace_id, item)
            if record.expires_at <= now:
                self._delete_record_files(record)
            else:
                active[workspace_id] = item
        return active

    def _delete_record_files(self, record: WorkspaceRecord) -> None:
        workspace_dir = record.db_path.parent
        if workspace_dir.exists() and workspace_dir.is_dir():
            shutil.rmtree(workspace_dir, ignore_errors=True)

    def _load_registry(self) -> dict:
        if not self.registry_path.exists():
            return {}
        try:
            with self.registry_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _write_registry(self, registry: dict) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.registry_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(registry, file, ensure_ascii=False, indent=2, sort_keys=True)
        tmp_path.replace(self.registry_path)

    def _serialize_record(self, record: WorkspaceRecord) -> dict:
        return {
            "token_hash": record.token_hash,
            "created_at": record.created_at.isoformat(),
            "last_seen_at": record.last_seen_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "db_path": str(record.db_path),
        }

    def _deserialize_record(self, workspace_id: str, item: dict) -> WorkspaceRecord:
        return WorkspaceRecord(
            workspace_id=workspace_id,
            token_hash=item["token_hash"],
            created_at=_parse_iso(item["created_at"]),
            last_seen_at=_parse_iso(item.get("last_seen_at", item["created_at"])),
            expires_at=_parse_iso(item["expires_at"]),
            db_path=Path(item["db_path"]),
        )


workspace_service = WorkspaceService()
