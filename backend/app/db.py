"""Database setup. The engine is built on first use, not at import."""
import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
Base = declarative_base()


@lru_cache(maxsize=1)
def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return create_engine(url)


@lru_cache(maxsize=1)
def get_sessionmaker():
    return sessionmaker(bind=get_engine(), autoflush=False)


def get_db():
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
