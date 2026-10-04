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
    ('audit_log', 'PUBLIC', 'Access audit trail (auditor-readable)'),
    ('data_assets', 'PUBLIC', 'Data catalog (auditor-readable)'),
    ('customers_raw', 'SENSITIVE', 'Customer PII raw — admin only (ALL fictitious)');

-- dim_customers_masked virou view mascarada (G6): INTERNAL para leitura analítica.
INSERT INTO data_assets (table_name, classification, description) VALUES
    ('dim_customers_masked', 'INTERNAL', 'Customer PII — masked view for analytics')
ON CONFLICT(table_name) DO UPDATE SET
    classification = excluded.classification,
    description = excluded.description;

-- Clientes 100% fictícios (nomes/e-mails/CPFs inválidos, só para demo de masking).
INSERT OR IGNORE INTO customers_raw (customer_id, full_name, email, cpf, created_at) VALUES
    ('c001', 'Fulana de Tal', 'fulana@example.com', '000.000.001-91', '2024-02-01T09:00:00+00:00'),
    ('c002', 'Beltrano Silva', 'beltrano@example.com', '000.000.002-72', '2024-02-02T09:00:00+00:00'),
    ('c003', 'Sicrana Souza', 'sicrana@example.com', '000.000.003-53', '2024-02-03T09:00:00+00:00');
