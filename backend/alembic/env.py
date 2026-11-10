"""Alembic runs this file for every command (upgrade, downgrade, check)."""
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import create_engine

from alembic import context
from app import models  # noqa: F401  (registers the tables on Base.metadata)
from app.db import Base

load_dotenv()
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# What the models say the database should look like. `alembic check`
# compares this with the real database.
target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
