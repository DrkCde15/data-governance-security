# Governança e Segurança de Dados

## Objetivo

Demonstrar controle de acesso (RBAC), classificação de dados, auditoria e
rastreabilidade — **simulados localmente**, sem nenhum recurso AWS pago.

**Escopo desta versão (v0.1.0 — Etapa 1):** modelo de roles, política de
acesso pura + trilha de auditoria em SQLite, schema SQL versionado e demo CLI.

## Problema

Sem governança, qualquer identidade acessa qualquer dado sem rastro. Este
projeto estabelece a fundação: quem pode ler/escrever o quê, por
classificação, com cada decisão registrada em `audit_log`.

## Arquitetura

```text
sql/schema.sql + seeds.sql → SQLite local (data/governance.db, gitignored)
        │
scripts/init_db.py → cria tabelas + roles/usuários/catálogo fictícios
        │
src/data_governance/{models.py, authz.py} → can_read/can_write + log_and_check()
        │
scripts/demo_access.py → 6 acessos demo (permitido/negado) + cauda da auditoria
```

Roles: `admin` (total), `data_engineer` (técnico leitura/escrita),
`data_analyst` (analítico só leitura), `auditor` (logs/metadados só leitura).
Classificações: PUBLIC < INTERNAL < CONFIDENTIAL < SENSITIVE.

Regra de auditoria: `audit_log` e `access_grants` só são legíveis por
`auditor`/`admin` (por nome de tabela); o catálogo (`data_assets`) é legível
por todos para descoberta.

Futuro: masking, row/column-level security, lineage, data catalog, AWS IAM
como conceito, PostgreSQL/Delta Unity Catalog.

## Tecnologias

Python 3.10+ (stdlib `sqlite3`, dataclasses), SQL versionado, pytest.
Nenhum recurso AWS é criado. Sem custo.

## Estrutura do projeto

```text
data-governance-security/
├── sql/{schema.sql,seeds.sql}
├── src/data_governance/{config,models,authz}.py
├── scripts/{init_db,demo_access}.py
├── data/              # governance.db local (gitignored)
├── tests/test_authz.py
└── docs/architecture.md
```

## Como executar

```bash
cd data-governance-security
pip install -e ".[dev]"   # instala pacote + pytest (pytest também roda sem instalar, via pythonpath)
cp .env.example .env   # opcional
python scripts/init_db.py   # idempotente; cria também access_grants
python scripts/demo_access.py
pytest
```

## Próximas etapas

1. Masking de PII (views `*_masked`) + testes de vazamento.
2. Row/column-level security e grants por asset.
3. Catálogo com dono, SLA e lineage mínimo.
4. Migração do SQLite para PostgreSQL + IAM (somente conceito, sem custo).
