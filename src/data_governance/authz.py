"""Autorização + helpers de auditoria sobre SQLite (só stdlib).

Cada verificação de acesso grava uma linha em audit_log (permitido/negado),
dando rastreabilidade desde a etapa 1. Masking por linha/coluna e IAM real
são trabalhos futuros.
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
    """Uma tentativa de acesso."""

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
    """Verificação pura da política (sem I/O): True se permitido."""
    if request.action == "read":
        return can_read(request.role, request.classification, request.table)
    if request.action == "write":
        return can_write(request.role, request.classification)
    return False


def log_and_check(db_path: Path, request: AccessRequest) -> bool:
    """Verifica a política E registra a decisão em audit_log. Retorna permitido."""
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
