from app.agent import safe_json


def test_plain_json():
    assert safe_json('{"a": 1}') == {"a": 1}


def test_markdown_fence():
    assert safe_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_preamble_text():
    assert safe_json('Sure! Here is the result: {"a": 1}') == {"a": 1}


def test_broken_json_returns_empty():
    assert safe_json('{"a": 1,,}') == {}


def test_no_json_returns_empty():
    assert safe_json("I could not find anything.") == {}
