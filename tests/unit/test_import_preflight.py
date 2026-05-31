"""
测试导入预检服务

input: 券商 CSV 文件
output: 不写数据库的导入预检结果
pos: 单元测试 - 验证上传前格式识别、行数统计和错误反馈

一旦我被更新，务必更新我所属文件夹的 README.md
"""

from pathlib import Path
from textwrap import dedent

from src.importers.import_preflight import preview_import_file


FIXTURE = Path(__file__).parent.parent / "fixtures" / "test_trades.csv"


def test_preview_recognizes_supported_futu_csv_without_writing_db():
    result = preview_import_file(FIXTURE, file_name="test_trades.csv")

    assert result.can_import is True
    assert result.broker_id == "futu_cn"
    assert result.broker_name == "富途证券(中文)"
    assert result.detection_confidence == 1.0
    assert result.total_rows == 8
    assert result.completed_trades == 7
    assert result.skipped_rows == 1
    assert result.error_messages == []


def test_preview_returns_actionable_error_for_unsupported_csv(tmp_path):
    unsupported = tmp_path / "unknown.csv"
    unsupported.write_text("foo,bar\n1,2\n", encoding="utf-8")

    result = preview_import_file(unsupported, file_name="unknown.csv")

    assert result.can_import is False
    assert result.broker_id is None
    assert result.total_rows == 1
    assert result.completed_trades == 0
    assert result.error_messages == [
        "Unsupported CSV format. No broker adapter matched this file."
    ]
    assert result.detected_columns == ["foo", "bar"]


def test_preview_allows_import_when_cancelled_rows_have_empty_fills(tmp_path):
    csv_path = tmp_path / "futu_en_with_cancelled_rows.csv"
    csv_path.write_text(
        dedent(
            """\
            Side,Symbol,Name,Order Price,Order Qty,Order Amount,Status,Filled@Avg Price,Order Time,Order Type,Markets,Currency,Fill Qty,Fill Price,Fill Amount,Fill Time,Platform Fees,Counterparty,SFC Levy
            Buy,AAPL,Apple,100,1,100,Filled,1@100,2025/01/01 09:30:00 (ET),Limit,US,USD,1,100,100,2025/01/01 09:30:01 (ET),1,,
            Buy,MSFT,Microsoft,100,1,100,Cancelled,,2025/01/02 09:30:00 (ET),Limit,US,USD,0,0,,2025/01/02 09:30:01 (ET),1,,
            """
        ),
        encoding="utf-8",
    )

    result = preview_import_file(csv_path, file_name=csv_path.name)

    assert result.can_import is True
    assert result.broker_id == "futu_en"
    assert result.total_rows == 2
    assert result.completed_trades == 1
    assert result.skipped_rows == 1
    assert result.error_messages == []
    assert "Fill quantity must be greater than 0" in result.warning_messages
    assert "Fill price must be greater than 0" in result.warning_messages
