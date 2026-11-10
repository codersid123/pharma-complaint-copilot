"""One place that turns date text into a real date.

Used when saving a complaint (Day 3) and when importing spreadsheets (Day 4).
"""
from datetime import date, datetime
from typing import Optional

# Tried in order. Month-only formats become the 1st of that month, which
# matches the rule in the extraction prompt.
FORMATS = [
    "%Y-%m-%d",   # 2025-06-01  (what the LLM is told to return)
    "%d-%m-%Y",   # 01-06-2025
    "%d/%m/%Y",   # 01/06/2025  (Indian / UK order, not US)
    "%d.%m.%Y",   # 01.06.2025
    "%d %B %Y",   # 1 June 2025
    "%d %b %Y",   # 1 Jun 2025
    "%B %d, %Y",  # June 1, 2025
    "%B %Y",      # June 2025
    "%b %Y",      # Jun 2025
    "%m/%Y",      # 06/2025
    "%Y-%m",      # 2025-06
]


def parse_date(value) -> Optional[date]:
    """Return a date, None for blank input, or raise ValueError."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date '{text}' (use YYYY-MM-DD)")
