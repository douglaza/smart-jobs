# Smart Jobs

Aplicação pessoal para centralizar oportunidades profissionais, avaliar compatibilidade
com fatos confirmados e preparar materiais sujeitos a revisão humana.

Este repositório está na Fase 1. A fundação, a API local e PostgreSQL estão disponíveis;
coleta, IA, painel, e-mail e automação ainda não foram implementados.

## Requisitos

- Python 3.13 (fixado em `.python-version`)
- uv
- Git

## Configuração local

```bash
uv sync --locked
```

Não copie valores reais para o arquivo `.env.example`. Consulte `CONTEXT.md` para
diretrizes de privacidade e limites operacionais.

## Verificações da Fase 0

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv build
```

## Fase 1 — API e PostgreSQL

O ambiente local utiliza Docker Compose:

```bash
docker compose up --build -d
docker compose exec api uv run alembic upgrade head
curl --fail http://127.0.0.1:8000/api/v1/health/live
curl --fail http://127.0.0.1:8000/api/v1/health/ready
```

Os dados ficam no volume `smart_jobs_db`. Para executar integrações com PostgreSQL:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/smart_jobs \
  uv run pytest tests/integration
```

Esse teste só é executado com `DATABASE_URL` configurado e um banco isolado.

## Fase 3 — bloqueio seguro da avaliação

A avaliação não chama provedores externos enquanto a rubrica e a retenção não estiverem
confirmadas. A configuração local do Ollama pode definir `OLLAMA_MODEL`; sem modelo,
nenhuma avaliação é criada como concluída.
