import pytest

from app.llm import pick_model

AVAILABLE = {"openai/gpt-oss-20b", "openai/gpt-oss-120b"}


def test_picks_first_available():
    assert pick_model(AVAILABLE, "gemma2-9b-it", "openai/gpt-oss-20b") == "openai/gpt-oss-20b"


def test_skips_none_and_empty():
    assert pick_model(AVAILABLE, None, "", "openai/gpt-oss-120b") == "openai/gpt-oss-120b"


def test_raises_when_nothing_available():
    with pytest.raises(RuntimeError, match="None of"):
        pick_model(AVAILABLE, "gemma2-9b-it")