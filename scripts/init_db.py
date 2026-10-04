"""CLI: initialize local SQLite governance DB (schema + seeds, idempotent).

Usage:
    python scripts/init_db.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_governance.config import load_settings, setup_logging

logger = setup_logging()


def main() -> int:
    """Create schema and seeds. Returns exit code."""
    settings = load_settings()
    root = settings.project_root
    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    for name in ("schema.sql", "seeds.sql"):
        sql = (root / "sql" / name).read_text(encoding="utf-8")
        with sqlite3.connect(db_path) as conn:
            conn.executescript(sql)
    logger.info("Governance DB ready at %s", db_path)
    print(f"Governance DB ready at {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
