"""
Merge filtered input data with settlement info, add computed columns,
and write the consolidated dataset to input/settlement data.xlsx.

Settlement info columns:
  Sub-Category, GBU, GTK Supplier,
  ICMPartyName1, ICMExternalSignatory, ICMExternalSignatoryTitle,
  ICMInternalSignatory, ICMInternalSignatoryTitle,
  ICMSRAgreementEffectiveDate, ICMSRAGREEMENTCODE

Added columns:
  ICMAgreementCode  – from user-supplied iCertis codes dict
  ICMEffectiveDate  – first day of chosen quarter (e.g. "Nov 1, 2025")
  _supplier_key     – already present on filtered_df; kept for grouping
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

_SETTLEMENT_INFO_COLS = [
    "Sub-Category",
    "GBU",
    "GTK Supplier",
    "ICMPartyName1",
    "ICMExternalSignatory",
    "ICMExternalSignatoryTitle",
    "ICMInternalSignatory",
    "ICMInternalSignatoryTitle",
    "ICMSRAgreementEffectiveDate",
    "ICMSRAGREEMENTCODE",
]


def load_settlement_info(path: str | Path) -> pd.DataFrame:
    """Load settlement info Excel and normalise column headers."""
    df = pd.read_excel(path, engine="openpyxl")
    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]

    missing = [c for c in _SETTLEMENT_INFO_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Settlement info Excel is missing columns: {missing}")

    df = df[_SETTLEMENT_INFO_COLS].copy()
    df.dropna(how="all", inplace=True)

    # Normalise GBU in settlement info (should be plain "NB" / "DT" already)
    df["GBU"] = df["GBU"].fillna("").astype(str).str.strip().str.upper()
    df["GTK Supplier"] = df["GTK Supplier"].fillna("").astype(str).str.strip()
    return df


def merge_data(
    filtered_df: pd.DataFrame,
    settlement_info: pd.DataFrame,
    icertis_codes: dict[str, str],
    effective_date: str,
) -> pd.DataFrame:
    """
    Join filtered data with settlement info, add ICMAgreementCode and
    ICMEffectiveDate.

    Matching rules:
      - Chicony:     match on GTK Supplier + normalised GBU (_gbu_norm)
      - All others:  match on GTK Supplier only
    Matching is case-insensitive and ignores all spaces.
    """
    def _key(s: str) -> str:
        """Normalise supplier name: lowercase + remove all spaces."""
        return str(s).lower().replace(" ", "")

    df = filtered_df.copy()

    # Add a normalised key column for joining
    df["_sup_key"] = df["GTK Supplier"].apply(_key)
    settlement_info = settlement_info.copy()
    settlement_info["_sup_key"] = settlement_info["GTK Supplier"].apply(_key)

    # ---------- join settlement info ----------
    chicony_mask = df["_sup_key"] == _key("chicony")

    # --- non-Chicony: join on normalised supplier key ---
    non_chicony = df[~chicony_mask].copy()
    si_non_chicony = settlement_info[
        settlement_info["_sup_key"] != _key("chicony")
    ].drop_duplicates(subset=["_sup_key"]).drop(columns=["GBU", "Sub-Category", "GTK Supplier"])

    non_chicony_merged = non_chicony.merge(
        si_non_chicony, on="_sup_key", how="left"
    )

    # --- Chicony: join on normalised supplier key + normalised GBU ---
    chicony = df[chicony_mask].copy()
    si_chicony = settlement_info[
        settlement_info["_sup_key"] == _key("chicony")
    ].drop_duplicates(subset=["_sup_key", "GBU"]).drop(columns=["Sub-Category", "GTK Supplier"])
    si_chicony = si_chicony.rename(columns={"GBU": "_gbu_norm"})

    chicony_merged = chicony.merge(
        si_chicony, on=["_sup_key", "_gbu_norm"], how="left"
    )

    merged = pd.concat([non_chicony_merged, chicony_merged], ignore_index=True)

    # Drop the temporary join key
    merged.drop(columns=["_sup_key"], inplace=True, errors="ignore")

    # ---------- add computed columns ----------
    merged["ICMAgreementCode"] = merged["_supplier_key"].map(icertis_codes).fillna("")
    merged["ICMEffectiveDate"] = effective_date

    return merged


def save_settlement_data(df: pd.DataFrame, input_folder: str | Path) -> Path:
    """Write the merged DataFrame to input/settlement data.xlsx."""
    out_path = Path(input_folder) / "settlement data.xlsx"

    # Drop internal helper columns before saving
    export_cols = [c for c in df.columns if not c.startswith("_")]
    df[export_cols].to_excel(out_path, index=False, engine="openpyxl")
    return out_path
