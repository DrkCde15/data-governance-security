"""Testes: matriz da política RBAC + trilha de auditoria em SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from data_governance.authz import AccessRequest, check_access, log_and_check
from data_governance.models import AUDIT_TABLES, Classification


def test_audit_tables_exist_in_schema() -> None:
    """Toda tabela em AUDIT_TABLES existe em sql/schema.sql (regressão G4)."""
    import data_governance.config as cfg

    settings = cfg.load_settings()
    schema = (settings.project_root / "sql" / "schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(schema)
        existing = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert set(AUDIT_TABLES) <= existing, f"missing: {set(AUDIT_TABLES) - existing}"


def test_admin_full_access() -> None:
    """Admin lê e escreve tudo."""
    for cls in Classification:
        assert check_access(AccessRequest("a", "admin", "t", cls, "read"))
        assert check_access(AccessRequest("a", "admin", "t", cls, "write"))


def test_analyst_read_only_internal() -> None:
    """Analista lê PUBLIC/INTERNAL, nunca escreve, nunca lê CONFIDENTIAL."""
    assert check_access(AccessRequest("c", "data_analyst", "gold", Classification.INTERNAL, "read"))
    assert not check_access(AccessRequest("c", "data_analyst", "gold", Classification.INTERNAL, "write"))
    assert not check_access(
        AccessRequest("c", "data_analyst", "bronze", Classification.CONFIDENTIAL, "read")
    )


def test_engineer_cannot_write_sensitive() -> None:
    """Só admin escreve SENSITIVE."""
    assert not check_access(
        AccessRequest("b", "data_engineer", "dim", Classification.SENSITIVE, "write")
    )


def test_auditor_reads_audit_tables_only() -> None:
    """Auditor lê audit_log/catálogo, nunca escreve."""
    assert check_access(
        AccessRequest("d", "auditor", "audit_log", Classification.PUBLIC, "read")
    )
    assert not check_access(
        AccessRequest("d", "auditor", "gold", Classification.INTERNAL, "write")
    )


def test_unknown_role_denied() -> None:
    """Roles desconhecidas não têm acesso."""
    assert not check_access(AccessRequest("x", "ghost", "t", Classification.PUBLIC, "read"))


def test_restricted_tables_auditor_admin_only() -> None:
    """audit_log/access_grants legíveis só por auditor/admin (G1)."""
    for table in ("audit_log", "access_grants"):
        assert check_access(
            AccessRequest("d", "auditor", table, Classification.PUBLIC, "read")
        )
        assert check_access(
            AccessRequest("a", "admin", table, Classification.PUBLIC, "read")
        )
        assert not check_access(
            AccessRequest("c", "data_analyst", table, Classification.PUBLIC, "read")
        )
        assert not check_access(
            AccessRequest("b", "data_engineer", table, Classification.PUBLIC, "read")
        )


def test_catalog_readable_for_discovery() -> None:
    """data_assets segue legível por todos (descoberta do catálogo)."""
    assert check_access(
        AccessRequest("c", "data_analyst", "data_assets", Classification.PUBLIC, "read")
    )


def test_audit_log_records_decisions(tmp_path: Path, monkeypatch) -> None:
    """log_and_check persiste uma linha por tentativa (permitido + negado)."""
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
