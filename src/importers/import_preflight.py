"""
导入预检服务

input: 券商 CSV 文件路径
output: 不写数据库的导入预检结果
pos: 数据导入层 - 上传前识别券商格式、统计可导入行数、返回可解释错误

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional
import hashlib

import pandas as pd

from src.importers.core.adapter_registry import AdapterRegistry


@dataclass
class ImportPreflightResult:
    """只读导入预检结果。"""

    can_import: bool
    file_name: str
    file_hash: str
    broker_id: Optional[str] = None
    broker_name: Optional[str] = None
    detection_confidence: float = 0.0
    total_rows: int = 0
    completed_trades: int = 0
    skipped_rows: int = 0
    detected_columns: list[str] = field(default_factory=list)
    error_messages: list[str] = field(default_factory=list)
    warning_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def preview_import_file(file_path: str | Path, file_name: Optional[str] = None) -> ImportPreflightResult:
    """解析 CSV 并返回上传前预检信息，不写入数据库。"""
    path = Path(file_path)
    display_name = file_name or path.name
    file_hash = _calculate_file_hash(path)
    registry = AdapterRegistry()

    adapter, confidence = registry.detect_and_get_adapter(str(path))
    if adapter is None:
        sample = _read_sample(path)
        return ImportPreflightResult(
            can_import=False,
            file_name=display_name,
            file_hash=file_hash[:16],
            total_rows=len(sample) if sample is not None else 0,
            detected_columns=list(sample.columns) if sample is not None else [],
            error_messages=[
                "Unsupported CSV format. No broker adapter matched this file."
            ],
        )

    df = adapter.parse(str(path))
    completed_df = adapter.filter_completed_trades()
    stats = adapter.get_statistics()
    completed_trades = len(completed_df)

    return ImportPreflightResult(
        can_import=completed_trades > 0 and len(adapter.errors) == 0,
        file_name=display_name,
        file_hash=file_hash[:16],
        broker_id=adapter.config.broker_id,
        broker_name=adapter.config.broker_name_cn,
        detection_confidence=round(confidence, 4),
        total_rows=len(df),
        completed_trades=completed_trades,
        skipped_rows=max(len(df) - completed_trades, 0),
        detected_columns=list(adapter.raw_df.columns) if adapter.raw_df is not None else [],
        error_messages=stats["error_messages"],
        warning_messages=stats["warning_messages"],
    )


def _calculate_file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _read_sample(path: Path) -> Optional[pd.DataFrame]:
    for encoding in ["utf-8-sig", "utf-8", "gb18030", "gbk", "gb2312"]:
        try:
            return pd.read_csv(path, encoding=encoding, nrows=20)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    return None
