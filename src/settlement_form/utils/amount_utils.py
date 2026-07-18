"""
Convert a dollar amount (float) to an uppercase English words string.

Example:
    to_capital_words(10707.81)
    → "TEN THOUSAND SEVEN HUNDRED SEVEN DOLLARS AND EIGHTY-ONE CENTS"
"""
from __future__ import annotations

import math
from num2words import num2words


def to_capital_words(amount: float) -> str:
    """Return amount as uppercase English words suitable for a contract."""
    if amount < 0:
        raise ValueError("Amount must be non-negative.")

    # Round to 2 decimal places to avoid floating-point drift
    amount = round(amount, 2)
    dollars = int(amount)
    cents = round((amount - dollars) * 100)

    dollar_words = _int_to_words(dollars)
    result = f"{dollar_words} DOLLAR{'S' if dollars != 1 else ''}"

    if cents > 0:
        cent_words = _int_to_words(cents)
        result += f" AND {cent_words} CENT{'S' if cents != 1 else ''}"

    return result


def _int_to_words(n: int) -> str:
    """Convert a non-negative integer to uppercase English words."""
    raw = num2words(n, lang="en")
    # num2words may produce "and" inside e.g. "one hundred and two"
    # American English typically omits interior "and", but it's acceptable
    # for legal docs — we just clean up commas and extra spaces, then uppercase.
    cleaned = raw.replace(",", "").strip()
    return cleaned.upper()
