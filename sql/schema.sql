-- Governance schema (SQLite-compatible; PostgreSQL migration is future work).
-- Tables: roles/users, data catalog (assets), grants, immutable-by-convention audit log.

CREATE TABLE IF NOT EXISTS roles (
    role_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    role_name TEXT NOT NULL REFERENCES roles(role_name),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_assets (
    table_name TEXT PRIMARY KEY,
    classification TEXT NOT NULL
        CHECK (classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','SENSITIVE')),
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    table_name TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('read','write')),
    allowed INTEGER NOT NULL CHECK (allowed IN (0,1))
);

-- Per-asset grants (Etapa 2; policy enforcement is future work).
-- Exists now so AUDIT_TABLES / docs promises hold; empty until grants are seeded.
CREATE TABLE IF NOT EXISTS access_grants (
    role_name TEXT NOT NULL REFERENCES roles(role_name),
    table_name TEXT NOT NULL REFERENCES data_assets(table_name),
    can_read INTEGER NOT NULL CHECK (can_read IN (0,1)),
    can_write INTEGER NOT NULL CHECK (can_write IN (0,1)),
    PRIMARY KEY (role_name, table_name)
);
