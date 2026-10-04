"""Interface demo (só leitura): catálogo, simulador de acesso e cauda da auditoria.

Uso:
    pip install -e ".[demo]"
    streamlit run app.py

A interface nunca escreve no banco: abre o SQLite em modo read-only
(URI `mode=ro`) e o simulador usa `check_access()` puro, sem registrar
na trilha de auditoria.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st

from data_governance.authz import AccessRequest, check_access
from data_governance.config import load_settings
from data_governance.models import ROLES, Classification


def open_readonly(db_path: Path) -> sqlite3.Connection:
    """Abre o SQLite em modo somente-leitura (falha se o .db não existir)."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def main() -> None:
    """Renderiza as 3 seções da demo."""
    st.set_page_config(page_title="Governança de Dados — demo", layout="wide")
    st.title("Governança e Segurança de Dados — demo local")

    perfil = st.sidebar.selectbox(
        "Perfil (login simulado)", sorted(ROLES), index=sorted(ROLES).index("data_analyst")
    )
    st.sidebar.caption("Autenticação simulada: sem senha, só para demo da política.")
    pode_ver_auditoria = check_access(
        AccessRequest(perfil, perfil, "audit_log", Classification.PUBLIC, "read")
    )

    settings = load_settings()
    if not settings.database_path.exists():
        st.warning("Banco não encontrado. Rode `python scripts/init_db.py` primeiro.")
        return

    with open_readonly(settings.database_path) as conn:
        catalog = conn.execute(
            "SELECT table_name, classification, description FROM data_assets ORDER BY table_name"
        ).fetchall()

    tab_catalog, tab_sim, tab_audit = st.tabs(["Catálogo", "Simulador", "Auditoria"])

    with tab_catalog:
        st.subheader("Ativos de dados")
        st.dataframe(
            [
                {"tabela": r["table_name"], "classificação": r["classification"], "descrição": r["description"]}
                for r in catalog
            ],
            use_container_width=True,
        )

    with tab_sim:
        st.subheader("Simular acesso (não grava na auditoria)")
        classes = {r["table_name"]: r["classification"] for r in catalog}
        col1, col2, col3 = st.columns(3)
        role = col1.selectbox("Role", sorted(ROLES))
        table = col2.selectbox("Tabela", sorted(classes))
        action = col3.selectbox("Ação", ("read", "write"))
        allowed = check_access(
            AccessRequest("demo", role, table, Classification(classes[table]), action)
        )
        if allowed:
            st.success(f"PERMITIDO — {role} pode {action} em {table}")
        else:
            st.error(f"NEGADO — {role} não pode {action} em {table}")

    with tab_audit:
        st.subheader("Cauda da auditoria (só leitura)")
        if not pode_ver_auditoria:
            st.error(f"NEGADO — o perfil `{perfil}` não pode ler `audit_log`.")
        else:
            with open_readonly(settings.database_path) as conn:
                total = conn.execute(
                    "SELECT COUNT(*) c, COALESCE(SUM(allowed), 0) ok FROM audit_log"
                ).fetchone()
            st.caption(f"{total['c']} eventos, {total['ok']} permitidos · banco `{settings.database_path}`")
            n = st.number_input("Eventos", min_value=5, max_value=200, value=20, step=5)
            with open_readonly(settings.database_path) as conn:
                rows = conn.execute(
                    "SELECT occurred_at, username, role, table_name, action, allowed"
                    " FROM audit_log ORDER BY id DESC LIMIT ?",
                    (int(n),),
                ).fetchall()
            st.dataframe(
                [
                    {
                        "quando": r["occurred_at"],
                        "usuário": r["username"],
                        "role": r["role"],
                        "tabela": r["table_name"],
                        "ação": r["action"],
                        "permitido": bool(r["allowed"]),
                    }
                    for r in rows
                ],
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
