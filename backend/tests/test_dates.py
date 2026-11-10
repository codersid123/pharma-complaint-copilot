from datetime import date

import pytest

from app.dates import parse_date


@pytest.mark.parametrize("text, expected", [
    ("2025-06-01", date(2025, 6, 1)),
    ("01/06/2025", date(2025, 6, 1)),     # day first, not US order
    ("1 June 2025", date(2025, 6, 1)),
    ("June 2025", date(2025, 6, 1)),      # month only -> first of month
    ("Feb 2027", date(2027, 2, 1)),
    ("  2025-06-01  ", date(2025, 6, 1)),
])
def test_formats(text, expected):
    assert parse_date(text) == expected


@pytest.mark.parametrize("blank", [None, "", "   "])
def test_blank_is_none(blank):
    assert parse_date(blank) is None


def test_garbage_raises():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_date("sometime last year")
