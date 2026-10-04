-- Seeds: roles, demo users, sample catalog (ALL fictitious).

INSERT OR IGNORE INTO roles (role_name) VALUES
    ('admin'), ('data_engineer'), ('data_analyst'), ('auditor');

INSERT OR IGNORE INTO users (username, role_name, created_at) VALUES
    ('alice_admin', 'admin', '2024-01-10T09:00:00+00:00'),
    ('bob_engineer', 'data_engineer', '2024-01-11T09:00:00+00:00'),
    ('carol_analyst', 'data_analyst', '2024-01-12T09:00:00+00:00'),
    ('dave_auditor', 'auditor', '2024-01-13T09:00:00+00:00');

INSERT OR IGNORE INTO data_assets (table_name, classification, description) VALUES
    ('bronze_transactions', 'CONFIDENTIAL', 'Raw ingested transactions (technical)'),
    ('gold_daily_volume', 'INTERNAL', 'Analytical aggregate: daily volume'),
    ('dim_customers_masked', 'SENSITIVE', 'Customer PII — masked views only (future)'),
    ('audit_log', 'PUBLIC', 'Access audit trail (auditor-readable)'),
    ('data_assets', 'PUBLIC', 'Data catalog (auditor-readable)');
