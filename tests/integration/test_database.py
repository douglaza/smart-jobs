import os

import pytest
from sqlalchemy import text

from smart_jobs.persistence.database import engine


@pytest.mark.integration
def test_postgres_accepts_queries() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for the PostgreSQL integration test")

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
