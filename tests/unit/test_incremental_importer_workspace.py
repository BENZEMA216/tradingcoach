"""
Incremental importer workspace tests

input: importer database_url override
output: imported rows stay in the requested SQLite database
pos: unit tests - workspace-aware CSV import
"""

from pathlib import Path

from sqlalchemy import create_engine, text

from src.importers.incremental_importer import IncrementalImporter


FIXTURE = Path(__file__).parent.parent / "fixtures" / "test_trades.csv"


def test_incremental_importer_writes_to_database_url_override(tmp_path):
    db_path = tmp_path / "workspace.db"
    importer = IncrementalImporter(
        str(FIXTURE),
        dry_run=False,
        database_url=f"sqlite:///{db_path}",
    )

    result = importer.run()

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM trades")).scalar()

    assert result.completed_trades == 7
    assert result.new_trades == 6
    assert count == result.new_trades
