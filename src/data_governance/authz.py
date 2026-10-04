"""Authorization + audit helpers over SQLite (stdlib only).

Every access check writes one row to audit_log (allowed/denied), giving
traceability from stage 1. Row/column masking and real IAM are future work.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from data_governance.models import Classification, can_read, can_write

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AccessRequest:
    """A single access attempt."""

    username: str
    role: str
    table: str
    classification: Classification
    action: str  # "read" | "write"


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def check_access(request: AccessRequest) -> bool:
    """Pure policy check (no I/O): True if allowed."""
    if request.action == "read":
        return can_read(request.role, request.classification, request.table)
    if request.action == "write":
        return can_write(request.role, request.classification)
    return False


def log_and_check(db_path: Path, request: AccessRequest) -> bool:
    """Check policy AND append the decision to audit_log. Returns allowed."""
    allowed = check_access(request)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO audit_log (occurred_at, username, role, table_name, action, allowed)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (now, request.username, request.role, request.table, request.action, int(allowed)),
        )
        conn.commit()
    logger.info(
        "Access %s: %s (%s) %s %s",
        "ALLOWED" if allowed else "DENIED", request.username, request.role,
        request.action, request.table,
    )
    return allowed
