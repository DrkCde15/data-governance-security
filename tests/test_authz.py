"""Tests: RBAC policy matrix + SQLite audit trail."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from data_governance.authz import AccessRequest, check_access, log_and_check
from data_governance.models import Classification


def test_admin_full_access() -> None:
    """Admin reads and writes everything."""
    for cls in Classification:
        assert check_access(AccessRequest("a", "admin", "t", cls, "read"))
        assert check_access(AccessRequest("a", "admin", "t", cls, "write"))


def test_analyst_read_only_internal() -> None:
    """Analyst reads PUBLIC/INTERNAL, never writes, never reads CONFIDENTIAL."""
    assert check_access(AccessRequest("c", "data_analyst", "gold", Classification.INTERNAL, "read"))
    assert not check_access(AccessRequest("c", "data_analyst", "gold", Classification.INTERNAL, "write"))
    assert not check_access(
        AccessRequest("c", "data_analyst", "bronze", Classification.CONFIDENTIAL, "read")
    )


def test_engineer_cannot_write_sensitive() -> None:
    """Only admin writes SENSITIVE."""
    assert not check_access(
        AccessRequest("b", "data_engineer", "dim", Classification.SENSITIVE, "write")
    )


def test_auditor_reads_audit_tables_only() -> None:
    """Auditor reads audit_log/catalog, never writes."""
    assert check_access(
        AccessRequest("d", "auditor", "audit_log", Classification.PUBLIC, "read")
    )
    assert not check_access(
        AccessRequest("d", "auditor", "gold", Classification.INTERNAL, "write")
    )


def test_unknown_role_denied() -> None:
    """Unknown roles get no access."""
    assert not check_access(AccessRequest("x", "ghost", "t", Classification.PUBLIC, "read"))


def test_audit_log_records_decisions(tmp_path: Path, monkeypatch) -> None:
    """log_and_check persists one row per attempt (allowed + denied)."""
    import data_governance.config as cfg

    db = tmp_path / "gov.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    settings = cfg.load_settings()
    assert settings.database_path == db

    schema = (settings.project_root / "sql" / "schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(db) as conn:
        conn.executescript(schema)

    assert log_and_check(db, AccessRequest("alice_admin", "admin", "t", Classification.PUBLIC, "read"))
    assert not log_and_check(
        db, AccessRequest("carol_analyst", "data_analyst", "t", Classification.SENSITIVE, "read")
    )
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT allowed FROM audit_log ORDER BY id").fetchall()
    assert [r[0] for r in rows] == [1, 0]
