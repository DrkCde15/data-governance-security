# Arquitetura — Governança e Segurança

## Etapa 1 (implementada)

- Política pura (`models.py`): matriz role × classificação, testável sem I/O.
- Auditoria (`authz.py`): cada `log_and_check()` persiste allowed/denied.
- SQLite local via stdlib: zero dependências, migra para PostgreSQL depois.
- Auditor com acesso garantido a `audit_log`, `data_assets`, `access_grants`
  (metadados), e escrita sempre negada.
- `audit_log` e `access_grants` são restritos a auditor/admin por nome de
  tabela (`RESTRICTED_TABLES`), mesmo classificados como PUBLIC nos seeds.
  O catálogo (`data_assets`) permanece legível por todos para descoberta.

- Masking de PII (G6): `customers_raw` (SENSITIVE, só admin) + view
  `dim_customers_masked` (INTERNAL) com e-mail/CPF mascarados e testes de
  vazamento em `tests/test_masking.py`.

## Decisões

- SENSITIVE só com `admin` para escrita; leitura do raw só admin, consumo
  analítico pela view mascarada.
- `audit_log` append-only por triggers (`audit_log_no_update`,
  `audit_log_no_delete`); dissuasão em arquivo local, garantia real só no
  Postgres futuro com grants.
- Sem AWS IAM real: simulação local explícita, sem fingir segurança cloud.

## Futuro (não implementado)

RLS/CLS, lineage, catálogo rico, Unity Catalog / Postgres RLS.
