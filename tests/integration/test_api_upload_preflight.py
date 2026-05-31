"""
测试上传预检 API

input: multipart CSV 文件
output: 上传前预检 JSON
pos: 集成测试 - 验证 /upload/trades/preview 只读识别 CSV，不创建导入任务

一旦我被更新，务必更新我所属文件夹的 README.md
"""

from pathlib import Path
from textwrap import dedent


FIXTURE = Path(__file__).parent.parent / "fixtures" / "test_trades.csv"


def test_upload_preflight_returns_supported_broker_summary(client):
    with FIXTURE.open("rb") as file:
        response = client.post(
            "/api/v1/upload/trades/preview",
            files={"file": ("test_trades.csv", file, "text/csv")},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["can_import"] is True
    assert data["broker_id"] == "futu_cn"
    assert data["broker_name"] == "富途证券(中文)"
    assert data["total_rows"] == 8
    assert data["completed_trades"] == 7
    assert data["skipped_rows"] == 1
    assert data["error_messages"] == []


def test_upload_preflight_allows_importable_rows_with_cancelled_zero_fills(client):
    csv_content = dedent(
        """\
        Side,Symbol,Name,Order Price,Order Qty,Order Amount,Status,Filled@Avg Price,Order Time,Order Type,Markets,Currency,Fill Qty,Fill Price,Fill Amount,Fill Time,Platform Fees,Counterparty,SFC Levy
        Buy,AAPL,Apple,100,1,100,Filled,1@100,2025/01/01 09:30:00 (ET),Limit,US,USD,1,100,100,2025/01/01 09:30:01 (ET),1,,
        Buy,MSFT,Microsoft,100,1,100,Cancelled,,2025/01/02 09:30:00 (ET),Limit,US,USD,0,0,,2025/01/02 09:30:01 (ET),1,,
        """
    )

    response = client.post(
        "/api/v1/upload/trades/preview",
        files={
            "file": (
                "futu_en_with_cancelled_rows.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["can_import"] is True
    assert data["broker_id"] == "futu_en"
    assert data["total_rows"] == 2
    assert data["completed_trades"] == 1
    assert data["skipped_rows"] == 1
    assert data["error_messages"] == []
    assert "Fill quantity must be greater than 0" in data["warning_messages"]
    assert "Fill price must be greater than 0" in data["warning_messages"]


def test_upload_preflight_rejects_non_csv_file(client):
    response = client.post(
        "/api/v1/upload/trades/preview",
        files={"file": ("statement.xlsx", b"not a csv", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are supported"
