from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db_models import Base


def build_engine(database_url: str):
    return create_engine(database_url, future=True)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def get_session(engine) -> Session:
    return Session(engine)
