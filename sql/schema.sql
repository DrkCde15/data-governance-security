-- Governance schema (SQLite-compatible; PostgreSQL migration is future work).
-- Tables: roles/users, data catalog (assets), grants, append-only audit log (triggers).

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

-- PII demo (G6): dados 100% fictícios. Raw SENSITIVE (só admin lê);
-- consumo analítico pela view mascarada (INTERNAL, legível por analyst).
CREATE TABLE IF NOT EXISTS customers_raw (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    cpf TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS dim_customers_masked AS
SELECT
    customer_id,
    substr(full_name, 1, 1) || '.***' AS full_name,
    substr(email, 1, 1) || '***@***' AS email,
    '***.***.***-' || substr(cpf, -2, 2) AS cpf,
    created_at
FROM customers_raw;

-- Trilha de auditoria append-only por enforcement (G2): UPDATE/DELETE abortam.
-- Dissuasão em arquivo local; garantia real só no Postgres futuro com grants.
CREATE TRIGGER IF NOT EXISTS audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log e append-only');
END;

CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log e append-only');
END;
