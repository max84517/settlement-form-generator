"""
Load and filter the input Excel file.

Expected source columns (header row may use \\n; we normalise them):
  Platform, ODM, GBU, GTK Supplier, Sub-Category,
  GTK Liability $, Actual GTK Liability $, ESR need (Y/N),
  Status, DM #, PL, Rebate Initiative %, Actual Payment,
  Saving, DM Issued Date, DM Issued Quarter, Update Date

We keep only:
  Platform, GBU, GTK Supplier, Sub-Category, Status, Actual Payment
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


# Columns we need after normalising headers
_KEEP = ["Platform", "GBU", "GTK Supplier", "Sub-Category", "Status", "Actual Payment"]

# Regex to extract NB or DT from GBU strings like bNB, cNB, bDT, cDT
_GBU_PATTERN = re.compile(r"(NB|DT)", re.IGNORECASE)


def _normalise_header(col: str) -> str:
    """Strip whitespace and collapse embedded newlines to a single space."""
    return col.replace("\n", " ").strip()


def load_input_excel(path: str | Path) -> pd.DataFrame:
    """
    Read the input Excel, keep relevant columns, normalise GBU values
    for Chicony rows.

    Returns a DataFrame with columns:
        Platform, GBU, GTK Supplier, Sub-Category, Status, Actual Payment
    Also adds a helper column ``_supplier_key`` used throughout the app.
    """
    df = pd.read_excel(path, sheet_name="Data", engine="openpyxl")

    # Normalise headers (remove \\n, extra spaces)
    df.columns = [_normalise_header(c) for c in df.columns]

    # Keep only the columns we care about
    missing = [c for c in _KEEP if c not in df.columns]
    if missing:
        raise ValueError(f"Input Excel is missing columns: {missing}")

    df = df[_KEEP].copy()

    # Drop entirely empty rows
    df.dropna(how="all", inplace=True)

    # Ensure Status is a string (may be NaN for blank cells)
    df["Status"] = df["Status"].fillna("").astype(str).str.strip()

    # Normalise GBU: extract 'NB' or 'DT' from raw strings; keep others as-is
    df["GBU"] = df["GBU"].fillna("").astype(str).str.strip()
    df["_gbu_norm"] = df["GBU"].apply(_extract_gbu)

    # Canonicalise GTK Supplier: build a map from normalised name (lowercase,
    # no spaces) → first occurrence in the file.  This ensures "Liteon" and
    # "LiteOn" resolve to whichever spelling appears first, keeping one
    # consistent key throughout the pipeline.
    supplier_raw = df["GTK Supplier"].fillna("").astype(str).str.strip()
    norm_series = supplier_raw.str.lower().str.replace(" ", "", regex=False)
    canonical_map: dict[str, str] = {}
    for raw, norm in zip(supplier_raw, norm_series):
        if norm not in canonical_map:
            # Remove internal spaces + first-letter-upper-rest-lower
            # e.g. "Lite on" → "Liteon", "LiteOn" → "Liteon", "LITEON" → "Liteon"
            canonical_map[norm] = raw.replace(" ", "").capitalize()
    df["_canonical_supplier"] = norm_series.map(canonical_map)

    # Replace GTK Supplier with the canonical form so that casing variants
    # ("LiteOn" vs "Liteon") don't create separate contract groups later.
    df["GTK Supplier"] = df["_canonical_supplier"]

    # Build a supplier key that already accounts for Chicony NB/DT split
    df["_supplier_key"] = df.apply(_build_supplier_key, axis=1)

    # Coerce Actual Payment to numeric
    df["Actual Payment"] = pd.to_numeric(df["Actual Payment"], errors="coerce").fillna(0.0)

    return df.reset_index(drop=True)


def _extract_gbu(raw: str) -> str:
    """Return 'NB', 'DT', or the original string (uppercased)."""
    m = _GBU_PATTERN.search(raw)
    return m.group(1).upper() if m else raw.upper()


def _build_supplier_key(row: pd.Series) -> str:
    """
    For Chicony: 'Chicony - NB' or 'Chicony - DT'.
    For everyone else: canonical GTK Supplier name (first occurrence's casing).
    """
    supplier = str(row["_canonical_supplier"]).strip()
    if supplier.lower() == "chicony":
        gbu_norm = row["_gbu_norm"]
        return f"Chicony - {gbu_norm}"
    return supplier


def get_unique_subcategories(df: pd.DataFrame) -> list[str]:
    """Sorted unique Sub-Category values (empty strings excluded)."""
    vals = df["Sub-Category"].dropna().astype(str).str.strip()
    return sorted(v for v in vals.unique() if v)


def get_unique_statuses(df: pd.DataFrame) -> list[str]:
    """Sorted unique Status values (empty strings excluded)."""
    vals = df["Status"].dropna().astype(str).str.strip()
    return sorted(v for v in vals.unique() if v)


def filter_data(
    df: pd.DataFrame,
    sub_categories: list[str] | None,
    statuses: list[str] | None,
) -> pd.DataFrame:
    """
    Apply Sub-Category and Status filters, then sort by
    Sub-Category → GTK Supplier → Platform.

    Parameters
    ----------
    sub_categories : list of str | None
        If None or empty list → no Sub-Category filter (all shown).
    statuses : list of str | None
        If None or empty list → no Status filter (all shown).
    """
    result = df.copy()

    if sub_categories:
        result = result[result["Sub-Category"].isin(sub_categories)]

    if statuses:
        result = result[result["Status"].isin(statuses)]

    result = result.sort_values(
        ["Sub-Category", "GTK Supplier", "Platform"],
        na_position="last",
    ).reset_index(drop=True)

    return result
