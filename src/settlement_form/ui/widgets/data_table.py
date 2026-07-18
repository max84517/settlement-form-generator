"""
DataTable – a scrollable table widget that displays settlement rows.

Columns: [checkbox] Sub-Category | GTK Supplier | Platform | Actual Payment

The checkbox column is only visible when select_mode=True.
When select_mode=False all rows are treated as selected.
"""
from __future__ import annotations

from typing import Any

import customtkinter as ctk
import pandas as pd


_HEADERS = ["Sub-Category", "GTK Supplier", "Platform", "Actual Payment"]
_COL_WIDTHS = [150, 160, 160, 120]


class DataTable(ctk.CTkFrame):
    def __init__(self, master: Any, **kwargs) -> None:
        super().__init__(master, **kwargs)

        self._select_mode: bool = False
        self._check_vars: list[ctk.BooleanVar] = []
        self._rows: list[dict] = []   # list of row data dicts

        self._build_header()
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_data(self, df: pd.DataFrame) -> None:
        """Render df rows. Clears previous content."""
        self._rows = df.to_dict("records")
        self._redraw()

    def set_select_mode(self, enabled: bool) -> None:
        """Show (True) or hide (False) the per-row checkbox column."""
        if self._select_mode == enabled:
            return
        self._select_mode = enabled
        # Update header checkbox column visibility
        if enabled:
            self._chk_header_lbl.grid()
        else:
            self._chk_header_lbl.grid_remove()
        self._redraw()

    def get_selected_indices(self) -> list[int]:
        """Return 0-based indices of selected rows."""
        if not self._select_mode:
            return list(range(len(self._rows)))
        return [i for i, v in enumerate(self._check_vars) if v.get()]

    def get_selected_data(self) -> pd.DataFrame:
        """Return a DataFrame of the currently selected rows."""
        indices = self.get_selected_indices()
        return pd.DataFrame([self._rows[i] for i in indices])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        header_frame = ctk.CTkFrame(self, fg_color=("gray75", "gray25"), corner_radius=4)
        header_frame.pack(fill="x", padx=4, pady=(4, 0))

        # Checkbox placeholder column
        self._chk_header_lbl = ctk.CTkLabel(header_frame, text="✓", width=30)
        self._chk_header_lbl.grid(row=0, column=0, padx=(4, 0), pady=4)
        if not self._select_mode:
            self._chk_header_lbl.grid_remove()

        for col_idx, (header, width) in enumerate(zip(_HEADERS, _COL_WIDTHS)):
            ctk.CTkLabel(
                header_frame,
                text=header,
                width=width,
                font=ctk.CTkFont(weight="bold"),
                anchor="w",
            ).grid(row=0, column=col_idx + 1, padx=4, pady=4, sticky="w")

    def _redraw(self) -> None:
        """Clear the scroll frame and re-render all rows."""
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._check_vars = []

        for row_idx, row_data in enumerate(self._rows):
            bg = ("gray90", "gray20") if row_idx % 2 == 0 else ("gray85", "gray17")
            row_frame = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=2)
            row_frame.pack(fill="x", padx=4, pady=1)

            # Checkbox column
            var = ctk.BooleanVar(value=True)
            self._check_vars.append(var)
            chk = ctk.CTkCheckBox(row_frame, text="", variable=var, width=30)
            chk.grid(row=0, column=0, padx=(4, 0), pady=2)
            if not self._select_mode:
                chk.grid_remove()

            # Data columns
            values = [
                str(row_data.get("Sub-Category", "")),
                str(row_data.get("GTK Supplier", "")),
                str(row_data.get("Platform", "")),
                f"${float(row_data.get('Actual Payment', 0)):,.2f}",
            ]
            for col_idx, (val, width) in enumerate(zip(values, _COL_WIDTHS)):
                ctk.CTkLabel(
                    row_frame,
                    text=val,
                    width=width,
                    anchor="w",
                    wraplength=width - 8,
                ).grid(row=0, column=col_idx + 1, padx=4, pady=2, sticky="w")
