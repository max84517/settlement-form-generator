"""
QuarterDialog – modal popup for selecting the contract FY/Quarter.

Displays 8 options:  current FY's Q1–Q4 then previous FY's Q1–Q4.
Default selection is the current quarter.

Returns a QuarterInfo dict on Confirm, None on Cancel/close.
"""
from __future__ import annotations

from typing import Any

import customtkinter as ctk

from settlement_form.utils.fy_utils import (
    QuarterInfo,
    default_quarter_label,
    list_quarter_options,
)


class QuarterDialog(ctk.CTkToplevel):
    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self.title("Select Contract Period")
        self.resizable(False, False)
        self.grab_set()
        self.lift()

        self._result: QuarterInfo | None = None
        self._options: list[QuarterInfo] = list_quarter_options()
        self._labels: list[str] = [q["label"] for q in self._options]
        self._default = default_quarter_label()

        self._build_ui()
        self._center()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def get_result(self) -> QuarterInfo | None:
        return self._result

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="Select Contract Period",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=24, pady=(16, 8))

        ctk.CTkLabel(
            self,
            text="Choose the fiscal quarter for the settlement contracts:",
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 4))

        self._var = ctk.StringVar(value=self._default)
        self._menu = ctk.CTkOptionMenu(
            self,
            values=self._labels,
            variable=self._var,
            width=200,
        )
        self._menu.pack(padx=24, pady=8)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(8, 16))

        ctk.CTkButton(
            btn_frame, text="Cancel", width=120,
            fg_color="gray40", hover_color="gray30",
            command=self._cancel,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="Confirm", width=120,
            command=self._confirm,
        ).pack(side="left")

        self.protocol("WM_DELETE_WINDOW", self._cancel)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _confirm(self) -> None:
        label = self._var.get()
        for q in self._options:
            if q["label"] == label:
                self._result = q
                break
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
