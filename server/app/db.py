"""Datenbankverbindung (PostgreSQL in Produktion, SQLite lokal)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from . import config


class Base(DeclarativeBase):
    pass


_engine_kwargs = {"pool_pre_ping": True}
if config.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

elif config.DB_SCHEMA:
    _engine_kwargs["connect_args"] = {"options": f"-csearch_path={config.DB_SCHEMA}"}
engine = create_engine(config.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    from . import models  # noqa: F401  (registriert die Tabellen)
    if config.DB_SCHEMA and not config.DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{config.DB_SCHEMA}"'))
    Base.metadata.create_all(engine)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
