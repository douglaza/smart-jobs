# Runbook

## Estado atual

A Fase 1 fornece API e PostgreSQL locais por Docker Compose. Não há dados de domínio
ainda, coleta externa ou automação.

## Start, prontidão e backup

```bash
docker compose up --build -d
docker compose exec api uv run alembic upgrade head
curl --fail http://127.0.0.1:8000/api/v1/health/live
curl --fail http://127.0.0.1:8000/api/v1/health/ready
```

O banco não publica porta no host no Compose padrão. Para backup, use `pg_dump` a partir
de um container autorizado. Não execute comandos que removam o volume sem aprovação
humana explícita.

## Diagnóstico local da fundação

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv build
```
