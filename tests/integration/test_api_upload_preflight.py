"""
测试上传预检 API

input: multipart CSV 文件
output: 上传前预检 JSON
pos: 集成测试 - 验证 /upload/trades/preview 只读识别 CSV，不创建导入任务

一旦我被更新，务必更新我所属文件夹的 README.md
"""

from pathlib import Path


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


def test_upload_preflight_rejects_non_csv_file(client):
    response = client.post(
        "/api/v1/upload/trades/preview",
        files={"file": ("statement.xlsx", b"not a csv", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are supported"
