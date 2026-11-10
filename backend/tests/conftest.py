"""Shared test setup: a fake LLM and an in-memory database.

Nothing here touches the network or a real Postgres server.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.llm import LLMs
from app.main import app


class FakeReply:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    """Returns canned text. `replies` maps a word found in the prompt to the
    reply; the first match wins. Every prompt it receives is kept in `prompts`."""

    def __init__(self, replies: dict, default: str = "{}"):
        self.replies = replies
        self.default = default
        self.prompts = []

    def invoke(self, prompt: str):
        self.prompts.append(prompt)
        for key, reply in self.replies.items():
            if key in prompt:
                return FakeReply(reply)
        return FakeReply(self.default)


def make_llms(fast=None, reasoning=None) -> LLMs:
    return LLMs(fast=fast or FakeLLM({}), reasoning=reasoning or FakeLLM({}),
                fast_model="fake-fast", reasoning_model="fake-reasoning")


@pytest.fixture
def db_session():
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        # CI's Postgres job: a real server, emptied before each test.
        engine = create_engine(url)
        Base.metadata.drop_all(engine)
    else:
        # Default: in-memory SQLite. StaticPool + check_same_thread=False give
        # one shared database that the test and FastAPI's thread both see.
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    yield Session
    # Close any session a test left open; on Postgres an open session holds
    # a lock that would make the next test's drop_all wait forever.
    close_all_sessions()
    engine.dispose()

@pytest.fixture
def client(db_session):
    def override_get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Not used as a context manager, so the startup hook (create_all on the
    # real database) never runs.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def fake_agent(monkeypatch):
    """Replace run_agent inside main.py with a stub, for endpoint tests."""
    calls = []

    def stub(**kwargs):
        calls.append(kwargs)
        return {"patch": {"updates": {"customer_name": "Acme"}, "clear": []},
                "assistant_message": "stub", "missing_fields": [], "risk": None}

    monkeypatch.setattr("app.main.run_agent", stub)
    return calls
