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

## Decisões

- SENSITIVE só com `admin` para escrita (base para masking futuro).
- `audit_log` append-only por convenção (sem UPDATE/DELETE na API).
- Sem AWS IAM real: simulação local explícita, sem fingir segurança cloud.

## Futuro (não implementado)

Masking, RLS/CLS, lineage, catálogo rico, Unity Catalog / Postgres RLS.
