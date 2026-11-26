# Progresso

Fase atual: 3
Objetivo: Avaliação explicada por IA com bloqueio seguro enquanto decisões prévias
não forem confirmadas.

Entregas concluídas:
- Repositório inicial com pacote instalável `smart_jobs`.
- `pyproject.toml`, `.python-version`, `uv.lock` e ambiente virtual gerenciado por uv.
- Configuração de pytest, Ruff e mypy.
- README, AGENTS, segurança, runbook e catálogo inicial de fontes.
- ADR inicial em `docs/adr/0001-foundation-and-tooling.md`.
- Workflow de CI que sincroniza pelo lockfile e executa testes, lint, tipos e build.
- Estrutura mínima de testes e documentação criada; sem banco, API, LLM, coleta, painel
  ou worker.
- Configuração validada com Pydantic Settings.
- Engine SQLAlchemy síncrono com `pool_pre_ping`.
- FastAPI com saúde viva e prontidão dependente de PostgreSQL.
- Alembic com migração baseline `20261125_0001`.
- Dockerfile e Compose com API, banco e serviço de migração.
- Banco em rede interna do Compose, API limitada a `127.0.0.1:8000`.
- Volume `smart_jobs_db` para dados locais.
- Testes HTTP e integração PostgreSQL dentro da rede Compose.
- Migração `20261125_0002` para perfil, fatos, preferências e oportunidades.
- Endpoints para consentimento, perfil, fatos confirmados e preferências versionadas.
- Importação manual de vagas por texto/URL sem busca automática.
- Listagem paginada, filtros por estado/texto e detalhe de vaga.
- Deduplicação exata por impressão normalizada da entrada manual.
- Contrato tipado para extração estruturada de requisitos.
- Adaptador Ollama com timeout, JSON estrito e modelo exigido explicitamente.
- Rubrica versionável com validação de pesos somando 100.
- Migração `20261125_0003` para avaliações duráveis.
- Endpoints de solicitação e consulta de avaliação.
- Solicitação humana persiste estado `blocked` enquanto rubrica e retenção estiverem pendentes.

Testes e comandos executados:
- `uv python install 3.13`
- `uv lock && uv sync --locked`
- `uv run pytest`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy`
- `uv build`
- `docker compose config`
- `docker compose up --build -d`
- `curl --fail http://127.0.0.1:8000/api/v1/health/live`
- `curl --fail http://127.0.0.1:8000/api/v1/health/ready`
- `docker compose exec api uv run alembic current`
- `docker compose exec api env DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/smart_jobs uv run pytest tests/integration`
- `docker compose stop db` seguido de verificação de prontidão HTTP 503
- `docker compose restart db` seguido de recuperação HTTP 200
- `uv run pytest`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy`
- Migração real até `20261125_0002`.
- Cadastro HTTP de perfil com consentimento.
- Importação HTTP de vaga sintética e rejeição HTTP 409 da duplicata exata.
- Consulta da vaga após reinício do banco PostgreSQL.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy`
- `uv run pytest`
- Migração real até `20261125_0003`.
- Solicitação HTTP de avaliação persistiu estado `blocked` sem chamada externa.

Evidências da verificação:
- Python do ambiente: 3.13.18.
- Local: 2 testes aprovados e 1 integração isolada marcada para execução com banco.
- Fase 2 local: 4 testes aprovados e 1 integração isolada marcada para execução com banco.
- Fase 2 unitário: salário inválido rejeitado e impressão determinística verificadas.
- Compose: integração PostgreSQL real com 1 teste aprovado.
- Compose: migração baseline aplicada e confirmada como revisão head.
- Compose: migração manual aplicada como revisão `20261125_0002`.
- Compose: perfil criado com consentimento; vaga sintética persistida; duplicata exata
  respondeu HTTP 409.
- Compose: vaga continuou listável após reinício do banco.
- Compose: prontidão respondeu 503 com banco parado e 200 após reinício.
- Reinício do banco preservou a migração head no volume.
- Ruff lint: sem erros.
- Ruff format: 17 arquivos já formatados.
- mypy strict: nenhum problema em 7 arquivos de código.
- Build: wheel e source distribution gerados em `dist/`.
- Renomeação aplicada: projeto e pacote passaram de `vaga-com-criterio` /
  `vaga_com_criterio` para `smart-jobs` / `smart_jobs`.
- Revalidação após renomeação: pytest, Ruff, Ruff format, mypy e build passaram.
- Fase 3 local: 7 testes aprovados e 1 integração isolada sem banco.
- Fase 3: validação de pesos da rubrica e parsing JSON do adaptador Ollama aprovados.
- Compose: migração `20261125_0003` aplicada no PostgreSQL real.
- Compose: solicitação de avaliação persistiu `blocked` com
  `rubric_and_retention_pending`; nenhuma chamada ao Ollama foi realizada.

Decisões/ADRs:
- [ADR 0001](adr/0001-foundation-and-tooling.md): Python 3.13, uv, layout `src/`,
  pytest, Ruff e mypy; ferramentas posteriores não iniciadas nesta fase.
- [ADR 0002](adr/0002-local-llm-blocking.md): Ollama local candidato, modelo explícito,
  avaliação bloqueada até rubrica e retenção serem confirmadas.

Pendências e bloqueios:
- Nome adotado: `Smart Jobs`; registro de marca ou domínio não foi solicitado nesta fase.
- Nota de corte 65/100 confirmada pelo usuário; pesos da rubrica ainda pendentes.
- Currículo, preferências profissionais, remuneração, idioma e dados pessoais permanecem
  pendentes e serão pedidos somente nas fases que exigirem.
- Nenhuma fonte possui autorização ou integração validada nesta fase.
- Dados reais não foram cadastrados; os registros HTTP usados foram sintéticos.
- Rubrica confirmada: obrigatório 50, desejável 30 e experiência 20; corte 65/100.
- Retenção confirmada: excluir trechos após a resposta do modelo.
- Modelo Ollama confirmado: `llama3.2:3b`.
- Orçamento real ainda não autorizado; nenhuma chamada foi feita ao Ollama.
- Commit local criado: `78ea059 feat: establish smart-jobs phases 0-3`.
- Remoto configurado para `https://github.com/douglaza/smart-jobs.git`.
- Push pendente: ambiente não possui credenciais GitHub para autenticar HTTPS.

Próxima fase proposta:
- Fase 4: rascunhos, aprovação vinculada a hash e acompanhamento manual.

Aprovação para avançar: aguardando
