"""Modelos de domínio: roles, classificações e política de acesso (simulação RBAC).

Roles (etapa 1):
  admin          -> acesso total (todas as classificações, leitura + escrita)
  data_engineer  -> leitura/escrita em dados técnicos (INTERNAL e abaixo + leitura CONFIDENTIAL)
  data_analyst   -> somente leitura em dados analíticos (PUBLIC + INTERNAL)
  auditor        -> somente leitura em logs/metadados (PUBLIC + tabelas de auditoria)

Classificações: PUBLIC < INTERNAL < CONFIDENTIAL < SENSITIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Classification(str, Enum):
    """Níveis de sensibilidade dos dados (ordenados)."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SENSITIVE = "SENSITIVE"


@dataclass(frozen=True)
class Role:
    """Uma role nomeada, com classificações legíveis e flag de escrita."""

    name: str
    readable: frozenset[Classification]
    writable: bool


ROLES: dict[str, Role] = {
    "admin": Role(
        name="admin",
        readable=frozenset(Classification),
        writable=True,
    ),
    "data_engineer": Role(
        name="data_engineer",
        readable=frozenset(
            {Classification.PUBLIC, Classification.INTERNAL, Classification.CONFIDENTIAL}
        ),
        writable=True,
    ),
    "data_analyst": Role(
        name="data_analyst",
        readable=frozenset({Classification.PUBLIC, Classification.INTERNAL}),
        writable=False,
    ),
    "auditor": Role(
        name="auditor",
        readable=frozenset({Classification.PUBLIC}),
        writable=False,
    ),
}

# Tabelas que o auditor sempre pode ler (logs/metadados), independente da classificação.
AUDIT_TABLES = frozenset({"audit_log", "data_assets", "access_grants"})

# Trilha de auditoria + grants são restritos: só auditor/admin podem lê-las,
# mesmo classificadas como PUBLIC nos seeds. O catálogo (data_assets) segue
# legível por todos para descoberta.
RESTRICTED_TABLES = frozenset({"audit_log", "access_grants"})


def can_read(role_name: str, classification: Classification, table: str) -> bool:
    """Retorna True se a role pode ler a tabela com a classificação dada."""
    role = ROLES.get(role_name)
    if role is None:
        return False
    if table in RESTRICTED_TABLES:
        return role_name in ("auditor", "admin")
    if role_name == "auditor" and table in AUDIT_TABLES:
        return True
    return classification in role.readable


def can_write(role_name: str, classification: Classification) -> bool:
    """Retorna True se a role pode escrever dados com a classificação dada."""
    role = ROLES.get(role_name)
    if role is None:
        return False
    if role_name == "auditor":
        return False  # auditors are strictly read-only
    if classification == Classification.SENSITIVE and role_name != "admin":
        return False  # only admin writes SENSITIVE
    return role.writable and classification in role.readable
