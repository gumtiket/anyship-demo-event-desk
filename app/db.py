import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

engine = create_engine(
    os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg2://", 1),
    pool_pre_ping=True,
    pool_timeout=5,
    connect_args={"connect_timeout": 5, "options": "-c statement_timeout=5000"},
)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session
