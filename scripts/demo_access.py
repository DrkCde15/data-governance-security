"""CLI demo: a few allowed/denied accesses + audit tail.

Usage:
    python scripts/demo_access.py
Requires: python scripts/init_db.py (first).
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_governance.authz import AccessRequest, log_and_check
from data_governance.config import load_settings, setup_logging
from data_governance.models import Classification

logger = setup_logging()

DEMO = [
    ("alice_admin", "admin", "dim_customers_masked", Classification.SENSITIVE, "read"),
    ("bob_engineer", "data_engineer", "bronze_transactions", Classification.CONFIDENTIAL, "write"),
    ("carol_analyst", "data_analyst", "gold_daily_volume", Classification.INTERNAL, "read"),
    ("carol_analyst", "data_analyst", "bronze_transactions", Classification.CONFIDENTIAL, "read"),
    ("dave_auditor", "auditor", "audit_log", Classification.PUBLIC, "read"),
    ("dave_auditor", "auditor", "gold_daily_volume", Classification.INTERNAL, "write"),
]


def main() -> int:
    """Run demo accesses and print the audit tail. Returns exit code."""
    settings = load_settings()
    if not settings.database_path.exists():
        logger.error("DB not found. Run python scripts/init_db.py first.")
        return 1
    for username, role, table, cls, action in DEMO:
        allowed = log_and_check(
            settings.database_path,
            AccessRequest(username, role, table, cls, action),
        )
        print(f"  - {username:<14} {action:<5} {table:<22} -> {'ALLOWED' if allowed else 'DENIED'}")
    with sqlite3.connect(settings.database_path) as conn:
        rows = conn.execute(
            "SELECT COUNT(*) c, SUM(allowed) ok FROM audit_log"
        ).fetchone()
    print(f"Audit: {rows[0]} events, {rows[1]} allowed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
