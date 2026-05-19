"""
交易数据导入脚本

从 CSV 文件导入交易记录到数据库（支持中英文富途，以及未来接入的其它券商）。

Usage:
    python scripts/import_trades.py <csv_path>
    python scripts/import_trades.py original_data/历史-保证金综合账户*.csv
    python scripts/import_trades.py "Orders-Margin Universal Account-...csv" --dry-run

input: 富途中文/英文 CSV
output: trades + import_history 写入数据库；命令行总结
pos: CLI 入口 — 复用 backend HTTP 上传同一条路径（IncrementalImporter + adapter system），
     避免 CLI 和 HTTP 走不同代码导致行为分裂

一旦我被更新，务必更新所属文件夹的 README.md
"""

import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.importers.incremental_importer import IncrementalImporter
from src.models.base import init_database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_DIR / "import_trades.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Import Futu trade history into TradingCoach (CN/EN auto-detect)."
    )
    parser.add_argument("csv_path", help="Path to the Futu CSV export")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report but don't write to DB",
    )
    parser.add_argument(
        "--broker",
        default=None,
        help="Force broker_id (default: auto-detect). e.g. futu_cn, futu_en",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        logger.error(f"CSV not found: {csv_path}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("TradingCoach CSV importer")
    logger.info(f"File:     {csv_path}")
    logger.info(f"Dry run:  {args.dry_run}")
    logger.info(f"Broker:   {args.broker or 'auto-detect'}")
    logger.info("=" * 60)

    # Ensure schema exists (idempotent — same call backend.app.database.init_db uses)
    init_database(config.DATABASE_URL, echo=False)
    # Importing src.models registers all ORM models against Base.metadata.
    from src.models import Base  # noqa: F401
    from src.models.base import get_engine
    Base.metadata.create_all(get_engine())

    importer = IncrementalImporter(
        str(csv_path),
        dry_run=args.dry_run,
        broker_id=args.broker,
    )
    result = importer.run()

    # Pretty summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("IMPORT SUMMARY")
    logger.info("=" * 60)
    if getattr(result, "broker_name", None):
        logger.info(
            f"Broker detected:       {result.broker_name} "
            f"(confidence {result.detection_confidence:.0%})"
        )
    logger.info(f"CSV total rows:        {result.total_rows}")
    logger.info(f"Completed trades:      {result.completed_trades}")
    logger.info(f"New trades imported:   {result.new_trades}")
    logger.info(f"Duplicates skipped:    {result.duplicates_skipped}")
    logger.info(f"Errors:                {result.errors}")
    logger.info(f"Processing time:       {result.processing_time_ms} ms")

    # Compute trades that were neither imported nor flagged as duplicates nor
    # logged as errors — these are silently dropped (eg. unknown direction).
    accounted = result.new_trades + result.duplicates_skipped + result.errors
    if accounted < result.completed_trades:
        gap = result.completed_trades - accounted
        logger.warning(
            f"⚠ {gap} completed trades were dropped silently "
            f"(not imported, not duplicate, not error). "
            f"Check WARNING logs above for 'Unknown direction', 'Skipped row', etc."
        )

    if result.error_messages:
        logger.info("")
        logger.info("First 10 error messages:")
        for msg in result.error_messages[:10]:
            logger.info(f"  - {msg}")

    sys.exit(0 if result.errors == 0 else 2)


if __name__ == "__main__":
    main()
