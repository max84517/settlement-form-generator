"""
IcertisDialog – modal popup that asks the user to enter an iCertis code
for each supplier identified in the current filtered dataset.

Special rule: Chicony is displayed as "Chicony - NB" and/or "Chicony - DT"
depending on which GBU variants exist in the data.

Returns:
    dict[supplier_key, icertis_code]  on Confirm
    None                              on Cancel / close
"""
from __future__ import annotations

from typing import Any

import customtkinter as ctk
import pandas as pd


class IcertisDialog(ctk.CTkToplevel):
    def __init__(self, master: Any, supplier_keys: list[str]) -> None:
        super().__init__(master)
        self.title("iCertis Settlement Codes")
        self.resizable(False, False)
        self.grab_set()                 # modal
        self.lift()

        self._result: dict[str, str] | None = None
        self._entries: dict[str, ctk.CTkEntry] = {}

        self._build_ui(supplier_keys)
        self._center()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def get_result(self) -> dict[str, str] | None:
        """Call after the dialog is closed. Returns codes or None."""
        return self._result

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self, supplier_keys: list[str]) -> None:
        # --- Warning label ---
        warning = ctk.CTkLabel(
            self,
            text=(
                "Please create settlement form for each supplier on the iCertis first\n"
                "(Please choose system template)"
            ),
            text_color="red",
            font=ctk.CTkFont(size=13, weight="bold"),
            justify="center",
            wraplength=500,
        )
        warning.pack(padx=20, pady=(16, 8))

        # --- Column headers ---
        hdr_frame = ctk.CTkFrame(self, fg_color=("gray75", "gray25"), corner_radius=4)
        hdr_frame.pack(fill="x", padx=20, pady=(0, 4))
        ctk.CTkLabel(hdr_frame, text="Supplier", width=220,
                     font=ctk.CTkFont(weight="bold"), anchor="w").pack(
            side="left", padx=10, pady=4)
        ctk.CTkLabel(hdr_frame, text="iCertis Code for Settlement Form",
                     font=ctk.CTkFont(weight="bold"), anchor="w").pack(
            side="left", padx=10, pady=4)

        # --- Scrollable list ---
        scroll = ctk.CTkScrollableFrame(self, height=min(300, len(supplier_keys) * 44 + 20),
                                        width=540)
        scroll.pack(fill="both", expand=True, padx=20, pady=4)

        for key in supplier_keys:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=key, width=220, anchor="w").pack(
                side="left", padx=4)

            entry = ctk.CTkEntry(row, width=260,
                                 placeholder_text="Enter iCertis code…")
            entry.pack(side="left", padx=4)
            self._entries[key] = entry

        # --- Buttons ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(4, 16))

        ctk.CTkButton(btn_frame, text="Cancel", width=120,
                      fg_color="gray40", hover_color="gray30",
                      command=self._cancel).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="Confirm", width=120,
                      command=self._confirm).pack(side="left")

        self.protocol("WM_DELETE_WINDOW", self._cancel)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _confirm(self) -> None:
        self._result = {key: entry.get().strip()
                        for key, entry in self._entries.items()}
        self.destroy()

    def _cancel(self) -> None:
        self._result = None
        self.destroy()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _center(self) -> None:
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")


def collect_supplier_keys(df: pd.DataFrame) -> list[str]:
    """
    Extract unique supplier keys from the filtered DataFrame,
    preserving the Chicony NB/DT split.

    For Chicony: one entry per distinct _gbu_norm value present in the data.
    For others: one entry per distinct GTK Supplier value.
    """
    keys: list[str] = []
    seen: set[str] = set()

    for _, row in df.iterrows():
        key = str(row.get("_supplier_key", "")).strip()
        if key and key not in seen:
            seen.add(key)
            keys.append(key)

    return sorted(keys)
