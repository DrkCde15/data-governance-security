"""Testes: a view mascarada não vaza PII (G6)."""

from __future__ import annotations

import sqlite3

import pytest

import data_governance.config as cfg
from data_governance.authz import AccessRequest, check_access
from data_governance.models import Classification


@pytest.fixture()
def seeded_db() -> sqlite3.Connection:
    """Banco :memory: com schema + seeds aplicados."""
    settings = cfg.load_settings()
    conn = sqlite3.connect(":memory:")
    for name in ("schema.sql", "seeds.sql"):
        conn.executescript((settings.project_root / "sql" / name).read_text(encoding="utf-8"))
    yield conn
    conn.close()


def test_masked_view_hides_pii(seeded_db: sqlite3.Connection) -> None:
    """Nenhum valor bruto de e-mail/CPF aparece na view mascarada."""
    raw = seeded_db.execute("SELECT email, cpf FROM customers_raw").fetchall()
    masked = seeded_db.execute("SELECT customer_id, full_name, email, cpf FROM dim_customers_masked").fetchall()
    assert len(masked) == len(raw) == 3
    for m in masked:
        assert m[2].endswith("***@***") and "@" not in m[2].replace("***@***", "")
        assert m[3].startswith("***.***.***-")
    raw_emails = {r[0] for r in raw}
    assert not any(m[2] in raw_emails for m in masked)
    raw_cpfs = {r[1] for r in raw}
    assert not any(m[3] in raw_cpfs for m in masked)


def test_raw_pii_admin_only(seeded_db: sqlite3.Connection) -> None:
    """Raw SENSITIVE só admin; analista lê a view INTERNAL."""
    _ = seeded_db
    assert check_access(
        AccessRequest("a", "admin", "customers_raw", Classification.SENSITIVE, "read")
    )
    assert not check_access(
        AccessRequest("c", "data_analyst", "customers_raw", Classification.SENSITIVE, "read")
    )
    assert not check_access(
        AccessRequest("b", "data_engineer", "customers_raw", Classification.SENSITIVE, "write")
    )
    assert check_access(
        AccessRequest("c", "data_analyst", "dim_customers_masked", Classification.INTERNAL, "read")
    )
