"""Domain models: roles, classifications, and access policy (RBAC simulation).

Roles (stage 1):
  admin          -> full access (all classifications, read + write)
  data_engineer  -> read/write on technical data (INTERNAL and below + CONFIDENTIAL read)
  data_analyst   -> read-only on analytical data (PUBLIC + INTERNAL)
  auditor        -> read-only on logs/metadata (PUBLIC + audit tables)

Classifications: PUBLIC < INTERNAL < CONFIDENTIAL < SENSITIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Classification(str, Enum):
    """Data sensitivity levels (ordered)."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SENSITIVE = "SENSITIVE"


@dataclass(frozen=True)
class Role:
    """A named role with allowed classifications and write flag."""

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

# Tables the auditor may always read (logs/metadata), regardless of classification.
AUDIT_TABLES = frozenset({"audit_log", "data_assets", "access_grants"})


def can_read(role_name: str, classification: Classification, table: str) -> bool:
    """Return True if role may read a table with the given classification."""
    role = ROLES.get(role_name)
    if role is None:
        return False
    if role_name == "auditor" and table in AUDIT_TABLES:
        return True
    return classification in role.readable


def can_write(role_name: str, classification: Classification) -> bool:
    """Return True if role may write data with the given classification."""
    role = ROLES.get(role_name)
    if role is None:
        return False
    if role_name == "auditor":
        return False  # auditors are strictly read-only
    if classification == Classification.SENSITIVE and role_name != "admin":
        return False  # only admin writes SENSITIVE
    return role.writable and classification in role.readable
