"""
Fiscal-year / quarter utilities.

HP fiscal year calendar:
  Q1 = Nov, Dec, Jan   (first month of Q1 = Nov of *previous* calendar year)
  Q2 = Feb, Mar, Apr
  Q3 = May, Jun, Jul
  Q4 = Aug, Sep, Oct

FY year rule:  if month >= 11  →  FY = calendar_year + 1
               else            →  FY = calendar_year
"""
from __future__ import annotations

from datetime import date
from typing import TypedDict


QUARTER_MONTHS: dict[int, list[int]] = {
    1: [11, 12, 1],
    2: [2, 3, 4],
    3: [5, 6, 7],
    4: [8, 9, 10],
}

# First month of each quarter (calendar month number)
QUARTER_START_MONTH: dict[int, int] = {1: 11, 2: 2, 3: 5, 4: 8}

MONTH_ABBR = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


class QuarterInfo(TypedDict):
    label: str          # e.g. "FY26 Q1"
    fy: int             # e.g. 26
    q: int              # 1-4
    effective_date: str # e.g. "Nov 1, 2025"


def _fy_from_date(d: date) -> int:
    return d.year + 1 if d.month >= 11 else d.year


def _quarter_from_month(month: int) -> int:
    for q, months in QUARTER_MONTHS.items():
        if month in months:
            return q
    raise ValueError(f"Unexpected month: {month}")


def _effective_date(fy: int, q: int) -> str:
    """Return the first day of the quarter as a human-readable string."""
    start_month = QUARTER_START_MONTH[q]
    # For Q1, the start month (Nov) belongs to calendar year fy-1
    if q == 1:
        cal_year = fy - 1
    else:
        cal_year = fy
        # For Q2/Q3/Q4 we also need to account for whether they fall in the
        # part of the calendar year that still belongs to the same FY:
        # FY = year means months 2..10 of `year` and 11,12 of `year-1`
        # Q2(Feb), Q3(May), Q4(Aug) all start in calendar year == fy
        cal_year = fy

    return f"{MONTH_ABBR[start_month]} 1, {cal_year}"


def get_current_fy_quarter(today: date | None = None) -> tuple[int, int]:
    """Return (fy_2digit, quarter) for the given date (default: today)."""
    d = today or date.today()
    fy_full = _fy_from_date(d)
    fy2 = fy_full % 100
    q = _quarter_from_month(d.month)
    return fy2, q


def list_quarter_options(today: date | None = None) -> list[QuarterInfo]:
    """
    Return 8 QuarterInfo dicts: current FY's 4 quarters first (Q1→Q4),
    then previous FY's 4 quarters (Q1→Q4).
    """
    d = today or date.today()
    fy_full = _fy_from_date(d)
    current_fy2 = fy_full % 100
    prev_fy2 = (fy_full - 1) % 100

    options: list[QuarterInfo] = []
    for fy2 in (current_fy2, prev_fy2):
        fy_full_val = fy2 + (2000 if fy2 < 100 else 0)
        # reconstruct 4-digit year from 2-digit
        fy_full_val = 2000 + fy2
        for q in range(1, 5):
            options.append(
                QuarterInfo(
                    label=f"FY{fy2:02d} Q{q}",
                    fy=fy2,
                    q=q,
                    effective_date=_effective_date(fy_full_val, q),
                )
            )
    return options


def default_quarter_label(today: date | None = None) -> str:
    """Return the label string for the current quarter."""
    fy2, q = get_current_fy_quarter(today)
    return f"FY{fy2:02d} Q{q}"
