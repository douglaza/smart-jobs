from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from smart_jobs.config import settings

engine: Engine = create_engine(settings.database_url, pool_pre_ping=True)


def database_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
