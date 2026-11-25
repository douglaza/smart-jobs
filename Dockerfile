FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev

COPY alembic.ini ./
COPY migrations ./migrations
COPY tests ./tests

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "smart_jobs.main:app", "--host", "0.0.0.0", "--port", "8000"]
