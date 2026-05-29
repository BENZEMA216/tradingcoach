"""
Sample workspace importer

input: workspace database URL and bundled anonymous CSV
output: imported trades, matched positions, scored positions
pos: backend service layer - one-click PH beta demo data
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import text

from src.analyzers.quality_scorer import QualityScorer
from src.importers.incremental_importer import IncrementalImporter
from src.matchers.fifo_matcher import FIFOMatcher
from src.models.base import create_all_tables, get_session, init_database


SAMPLE_CSV_PATH = Path(__file__).parent.parent / "sample_data" / "ph_sample_trades.csv"


def import_sample_dataset(
    database_url: str,
    sample_path: Optional[Path] = None,
) -> dict:
    """Import bundled anonymous demo data into one workspace database."""
    csv_path = sample_path or SAMPLE_CSV_PATH
    if not csv_path.exists():
        raise FileNotFoundError(f"Sample CSV not found: {csv_path}")

    init_database(database_url, echo=False)
    create_all_tables()
    session = get_session()
    try:
        for table in ("positions", "trades", "import_history", "tasks"):
            try:
                session.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass
        session.commit()
    finally:
        session.close()

    importer = IncrementalImporter(
        str(csv_path),
        dry_run=False,
        database_url=database_url,
    )
    import_result = importer.run()

    init_database(database_url, echo=False)
    session = get_session()
    try:
        matcher = FIFOMatcher(session)
        match_result = matcher.match_all_trades()
        scorer = QualityScorer()
        score_result = scorer.score_all_positions(session, update_db=True)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {
        "total_rows": import_result.total_rows,
        "completed_trades": import_result.completed_trades,
        "new_trades": import_result.new_trades,
        "duplicates_skipped": import_result.duplicates_skipped,
        "positions_matched": match_result.get("positions_created", 0),
        "positions_scored": score_result.get("scored", 0),
        "broker_id": import_result.broker_id,
        "broker_name": import_result.broker_name,
    }
