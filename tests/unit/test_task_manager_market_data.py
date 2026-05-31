"""
Regression tests for task market-data fallback.

input: missing optional market data dependency
output: task manager returns limited-data stats instead of raising
pos: unit test - protects async upload analysis from failing when yfinance is absent

一旦我被更新，务必更新我所属文件夹的 README.md
"""

import builtins

from backend.app.services.task_manager import TaskManager


def test_fetch_market_data_handles_missing_optional_dependency(monkeypatch):
    manager = TaskManager()
    logs = []

    monkeypatch.setattr(
        manager,
        "_add_log",
        lambda task_id, message, level="info", category=None: logs.append(
            {
                "task_id": task_id,
                "message": message,
                "level": level,
                "category": category,
            }
        ),
    )

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "src.data_sources.batch_fetcher":
            raise ModuleNotFoundError("No module named 'yfinance'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    # Regression: ISSUE-001 - upload analysis failed at 70% before scoring when
    # yfinance was not installed in the local backend runtime.
    # Found by /qa on 2026-05-24.
    # Report: .gstack/qa-reports/qa-report-127-0-0-1-5174-2026-05-24.md
    result = manager._fetch_market_data_with_logs("task-1", object())

    assert result["symbols_fetched"] == 0
    assert result["records_fetched"] == 0
    assert "yfinance" in result["error"]
    assert any(
        log["level"] == "warning"
        and log["category"] == "data"
        and "市场数据获取不可用" in log["message"]
        for log in logs
    )
