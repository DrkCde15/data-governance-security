# Revisão de Engenharia de Dados — data-governance-security

**Data:** 2026-10-04
**Escopo:** `README.md`, `docs/architecture.md`, `sql/schema.sql`, `sql/seeds.sql`, `src/data_governance/{models,authz,config}.py`, `scripts/{init_db,demo_access}.py`, `tests/test_authz.py`, `pyproject.toml`, `.env.example`, `.gitignore` + varredura somente-leitura (sem executar pipeline contra serviço real).
**Maturidade assumida:** Estágio 1 — portfólio/estudo que entrega o primeiro valor (RBAC + auditoria simulados em SQLite), declarado como `v0.1.0 — Etapa 1` em `README.md:8`.

## Veredito

Isto não é um pipeline end-to-end; é um componente transversal de governança (política de acesso + trilha de auditoria) simulado localmente, e nisso ele é honesto e bem delimitado. A política pura em `models.py` é testável, os seeds são idempotentes e não há segredo nem over-engineering — o acerto central para o estágio 1. O que mais importa agora: (1) a trilha de auditoria que o projeto promete como fundação é legível por qualquer role e mutável por qualquer pessoa com o arquivo `.db`; (2) `pytest` quebra seguindo o README sem instalação prévia; (3) há uma tabela fantasma (`access_grants`) prometida em código e docs mas inexistente no schema.

## Mapa do ciclo de vida

| Etapa do ciclo | Onde está no repo | Tecnologia | Observação |
|---|---|---|---|
| Geração (fontes) | `sql/seeds.sql:1-17` | Fixtures SQL fictícias | **Parcial/ad hoc.** Sem fonte externa; sem contrato, sem CDC/incremental. Adequado como fixture de estágio 1, mas sem dono de fonte real. |
| Armazenamento | `sql/schema.sql`, `data/governance.db` (gitignored) | SQLite local via stdlib | Schema versionado + `CREATE TABLE IF NOT EXISTS`. Bruto/audit sem enforcement de imutabilidade; sem retenção/backup. |
| Ingestão | `scripts/init_db.py` | `executescript(schema+seeds)` com `INSERT OR IGNORE` | **Ad hoc.** Carga manual idempotente; sem validação, retry, checkpoint, log de volume ou backfill por intervalo. |
| Transformação | `src/data_governance/models.py`, `authz.py` | Política RBAC pura em Python | Sem modelagem dimensional/ELT (não se aplica aqui). Política em si é pura e testada — ver Pontos fortes. |
| Disponibilização | `scripts/demo_access.py`, SQLite | CLI demo + `audit tail` | Manual, sem BI, sem frescor visível, sem dicionário de métricas. Esperado no estágio 1. |

## Scorecard

| Dimensão | Nota (0–3) | Esperado no estágio | Resumo em uma linha |
|---|---|---|---|
| Geração | 1 | 1 | Fixtures fictícias documentadas, sem fonte real nem contrato. |
| Armazenamento | 1 | 1–2 | Versionado e ignorado pelo git, mas audit mutável e sem retenção. |
| Ingestão | 1 | 1 | `init_db` idempotente e manual; sem robustez de ingestão. |
| Transformação | 2 | 1–2 | Política pura e legível; modelagem analítica N/A por desenho. |
| Disponibilização | 1 | 1 | Demo CLI funcional; sem consumo real. |
| Segurança e privacidade | 1 | 1–2 | Sem segredos, mas audit legível por todos e sem enforcement. |
| Gerenciamento de dados | 1 | 1 | README/arquitetura honestos + catálogo mínimo; sem dono/SLA/linhagem. |
| DataOps | 1 | 1 | Testes locais existem; sem CI, monitoramento ou ambientes. |
| Arquitetura | 2 | 1–2 | Simples, stdlib, reversível e documentada; sem over-engineering. |
| Orquestração | 0 | 0–1 | Ausente por desenho; CLI manual, sem DAG/retry/backfill. |
| Engenharia de software | 2 | 1–2 | Modular e configurável; sem lockfile/linter e com `pytest` frágil. |

## Pontos fortes verificados

- Política pura sem I/O em `src/data_governance/models.py:65-84`, coberta por matriz de testes em `tests/test_authz.py:12-47`.
- Seeds idempotentes (`INSERT OR IGNORE`, `CREATE TABLE IF NOT EXISTS`) — `sql/schema.sql:4`, `sql/seeds.sql:3`, `scripts/init_db.py:26-29`. Reprocessar não corrompe (inegociável 2 atendido para este escopo).
- Timestamp de auditoria com fuso explícito (`datetime.now(timezone.utc)`) — `src/data_governance/authz.py:50`. Sem `datetime.now()` ingênuo nem `SELECT *` no repo.
- `.gitignore:18-19` ignora `data/*.db`; `.env.example:1-3` sem segredo; varredura de segredos não achou nada versionado. `data/governance.db` (36K) existe só localmente.
- Escopo honesto: `README.md:6,33-34` e `docs/architecture.md:17-19` declaram o que é simulação e o que é futuro (masking, RLS, lineage). Sem fingir segurança cloud.

## Achados

### G1 Trilha de auditoria legível por qualquer role — Alta · Esforço P
- **Local:** `src/data_governance/models.py:54-58,65-72` + `sql/seeds.sql:16-17`
- **Status:** verificado
- **Evidência:** `audit_log` e `data_assets` são `PUBLIC` nos seeds; `can_read()` retorna `True` para qualquer role com `PUBLIC` no seu `readable`. Logo `data_analyst` e `data_engineer` leem `audit_log`. O `docs/architecture.md:8` promete "auditor-readable", mas o código entrega world-readable.
- **Por que importa:** corrente segurança/privacidade (cap. 10, menor privilégio + pensamento negativo). Trilha de auditoria visível a todos vaza quem acessou o quê e enfraquece a própria garantia que o projeto demonstra.
- **Como corrigir:** ou reclassificar `audit_log`/`data_assets` para fora de `PUBLIC` (ex.: nova classificação `METADATA` só legível por `auditor`+`admin`), ou blindar por nome de tabela em `can_read()` como já feito para `auditor`, mas invertido (negar não-auditores). Adicionar 1 teste `analyst cannot read audit_log`.

### G2 Append-only só por convenção, sem enforcement — Alta · Esforço P
- **Local:** `sql/schema.sql:21-29` (+ `docs/architecture.md:14`)
- **Status:** verificado
- **Evidência:** `audit_log` não tem trigger contra `UPDATE/DELETE`, nem `REVOKE`, nem coluna hash/encadeada. Qualquer pessoa com o arquivo `data/governance.db` reescreve a história com um `DELETE FROM audit_log`.
- **Por que importa:** gerenciamento + segurança (caps. 2 e 10 — auditoria e linhagem só valem se tamper-evident). O erro é silencioso: nada alerta sobre a mutação.
- **Como corrigir:** trigger SQLite `BEFORE UPDATE OR DELETE ON audit_log → RAISE(ABORT)` + teste que tenta `UPDATE`/`DELETE` e espera falha. Documentar que em arquivo local isso é dissuasão, não garantia (garantia real só no Postgres futuro com grants).

### G3 `pytest` quebra seguindo o README — Alta · Esforço P
- **Local:** `tests/test_authz.py:8-9`, `pyproject.toml:17-22`, `README.md:55-62`
- **Status:** verificado (rodei `python3 -m pytest -q` → `ModuleNotFoundError: No module named 'data_governance'`)
- **Evidência:** layout `src/` sem `pythonpath` configurado no `[tool.pytest.ini_options]`; o teste só passa após `pip install -e ".[dev]"`. Não há CI para pegar a regressão (`.github/` inexistente).
- **Por que importa:** inegociável 5 (outra pessoa roda pelo README) + DataOps (cap. 2, automação). Portfólio que não roda de primeira perde o valor de demonstração.
- **Como corrigir:** adicionar `pythonpath = ["src"]` em `[tool.pytest.ini_options]` (2 linhas) ou `conftest.py`; opcionalmente um workflow mínimo `.github/workflows/ci.yml` com `pip install -e ".[dev]" && pytest`.

### G4 Tabela `access_grants` prometida mas inexistente — Média · Esforço P
- **Local:** `src/data_governance/models.py:62`, `docs/architecture.md:8` vs `sql/schema.sql:1-29`
- **Status:** verificado
- **Evidência:** `AUDIT_TABLES` inclui `access_grants` e a doc lista grants como garantidos ao auditor, mas `schema.sql` cria só `roles/users/data_assets/audit_log`. `can_read("auditor", ..., "access_grants")` retorna `True` para tabela que não existe.
- **Por que importa:** gerenciamento (cap. 2 — metadados e contrato). Referência quebrada vira bug no dia em que o roadmap item 2 ("grants por asset") começar.
- **Como corrigir:** ou criar `access_grants` mínima no schema agora, ou remover das duas referências e abrir o item como roadmap explícito. 1 teste de consistência (tabelas em `AUDIT_TABLES` existem no schema) evita reincidência.

### G5 Sem CI, linter, formatter ou lockfile — Média · Esforço M
- **Local:** *não encontrado no repositório* (sem `.github/`, sem `.pre-commit-config.yaml`, `pyproject.toml:7` com `python-dotenv>=1.0` aberto)
- **Status:** inferido (ausência verificada por listagem)
- **Evidência:** só `pytest>=8.0` como dev-dep; sem automação que rode lint/testes a cada commit.
- **Por que importa:** DataOps + engenharia de software (cap. 2). Hoje o custo é baixo, mas G3 prova que regressão boba já passou sem rede.
- **Como corrigir:** `pip freeze`/`pip-compile` ou `uv lock` + `ruff` + workflow CI de ~20 linhas. Deliberadamente pequeno; nada de matriz multi-OS.

### G6 PII/SENSITIVE sem masking — regra só nega escrita — Média · Esforço M
- **Local:** `src/data_governance/models.py:82-83`, `sql/seeds.sql:15`, `README.md:66`
- **Status:** verificado (com atenuante: `seeds.sql:1` declara `ALL fictitious` e o README marca masking como próxima etapa)
- **Evidência:** `dim_customers_masked` é `SENSITIVE`, mas `admin` lê/escreve o valor bruto; não há view mascarada nem teste de vazamento. A proteção atual é "só admin escreve", não "ninguém vê PII em claro".
- **Por que importa:** segurança/privacidade (cap. 10 + LGPD — acréscimo desta skill, não do livro). Em dado fictício o dano é zero; o risco é o padrão ser copiado para dado real.
- **Como corrigir:** views `*_masked` + teste que afirma que `data_analyst` só enxerga a view mascarada (é exatamente o roadmap item 1 do README — manter como próximo passo, não antecipar RLS completo).

### G7 `demo_access.py` polui a auditoria a cada reexecução — Baixa · Esforço P
- **Local:** `scripts/demo_access.py:38-48`
- **Status:** verificado
- **Evidência:** cada run insere +6 linhas em `audit_log` sem marcador de sessão/demo; `SELECT COUNT(*)` cresce e mistura demo com uso real.
- **Por que importa:** gerenciamento (linhagem/proveniência, cap. 2). Erro visível, não silencioso — mas confunde a demo.
- **Como corrigir:** coluna opcional `source`/`run_id` ou flag `--tag demo`, ou documentar `init_db.py` como reset da demo.

## Roadmap

1. **Agora** — correções críticas e quick wins (P).
   - G1 (restringir leitura do audit) + teste.
   - G2 (trigger anti-UPDATE/DELETE no audit) + teste.
   - G3 (`pythonpath=["src"]` no `pyproject.toml`; verificar `pytest` limpo).
   - G4 (resolver `access_grants`: criar ou remover referência).
2. **Em seguida** — o que eleva ao próximo estágio.
   - G6: views `*_masked` + testes de vazamento (roadmap item 1 do README).
   - G5: CI mínima + ruff + dependências fixadas.
   - Catálogo mínimo com dono/SLA por asset (roadmap item 3); grants por asset (item 2).
3. **Deliberadamente adiado** — over-engineering neste estágio e por quê.
   - Migração Postgres/Unity Catalog/IAM real, lineage automatizado, Kafka/streaming, RLS/CLS completo por linha: sem volume, sem consumidor e sem decisão que exija isso agora (arquitetura caps. 3–4: pesar custo de manutenção vs. valor). Manter como "futuro" documentado está correto.

## O que esta análise não cobriu

Produção e volumes reais, custos, permissões efetivas na nuvem, qualidade real dos dados, o que vive fora do repositório (console cloud, BI, outro repo). Também não executei `init_db`/`demo_access` nem migração Postgres — análise estática + comandos somente-leitura, conforme a regra de não causar dano.

## Perguntas em aberto

1. O `audit_log` deve ser legível só por `auditor`+`admin`, ou analistas devem ver estatísticas agregadas? (Muda G1.)
2. O `.db` local é só artefato descartável de demo, ou pretende ser a "fonte de verdade" da auditoria? (Muda a severidade de G2.)
3. `access_grants` entra já no próximo incremento ou sai das referências até o item 2 do roadmap? (Fecha G4.)
4. Há dado pessoal real em algum outro repo/branch que este padrão será aplicado, ou tudo segue fictício? (Muda a prioridade de G6 e obrigações LGPD.)
