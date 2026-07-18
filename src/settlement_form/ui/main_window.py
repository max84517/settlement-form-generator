"""
MainWindow – the primary application window.

Layout (top → bottom):
  1. Input Excel path row + Browse
  2. Filter row: Sub-Category dropdown-checklist
  3. Filter row: "Only 2nd Ver Complete" checkbox + optional Status dropdown-checklist
  4. Option row: "Select All" checkbox + "Turn status to Contract Generated" checkbox
  5. DataTable (fills remaining space)
  6. "Generate Consolidate Settlements" button
"""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk
import pandas as pd

from settlement_form.config import settings
from settlement_form.core import data_loader, data_merger, contract_generator
from settlement_form.ui.icertis_dialog import IcertisDialog, collect_supplier_keys
from settlement_form.ui.quarter_dialog import QuarterDialog
from settlement_form.ui.widgets.data_table import DataTable
from settlement_form.ui.widgets.dropdown_checklist import DropdownChecklist

_STATUS_2ND_VER = "2nd Ver Complete"


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Settlement Form Generator")
        self.geometry("840x580")
        self.minsize(760, 480)

        self._cfg = settings.load()
        self._raw_df: pd.DataFrame | None = None
        self._filtered_df: pd.DataFrame | None = None

        self._build_ui()
        self._restore_state()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}

        # ── Row 0: Input Excel ──────────────────────────────────────────
        row0 = ctk.CTkFrame(self, fg_color="transparent")
        row0.pack(fill="x", **pad)

        ctk.CTkLabel(row0, text="Input Excel:", width=90, anchor="w").pack(
            side="left")
        self._excel_var = ctk.StringVar()
        ctk.CTkEntry(row0, textvariable=self._excel_var,
                     width=540, placeholder_text="Path to input Excel file…").pack(
            side="left", padx=(0, 6))
        ctk.CTkButton(row0, text="Browse", width=70,
                      command=self._browse_excel).pack(side="left")

        # ── Row 1: Sub-Category filter ─────────────────────────────────
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", **pad)

        ctk.CTkLabel(row1, text="Sub-Category:", width=90, anchor="w").pack(
            side="left")
        self._subcat_widget = DropdownChecklist(
            row1, options=[], on_change=self._on_filter_change,
            placeholder="Load an Excel file first…", width=240)
        self._subcat_widget.pack(side="left")

        # ── Row 2: Status filter ───────────────────────────────────────
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", **pad)

        self._only_2nd_var = ctk.BooleanVar(value=True)
        self._only_2nd_chk = ctk.CTkCheckBox(
            row2,
            text='Only Display "2nd Ver Complete" Settlements',
            variable=self._only_2nd_var,
            command=self._on_2nd_ver_toggle,
        )
        self._only_2nd_chk.pack(side="left")

        self._status_label = ctk.CTkLabel(row2, text="  Status:", anchor="w")
        self._status_widget = DropdownChecklist(
            row2, options=[], on_change=self._on_filter_change,
            placeholder="Load an Excel file first…", width=200)
        # Hidden by default
        self._status_label.pack_forget()
        self._status_widget.pack_forget()

        # ── Row 3: Select-all + status update ─────────────────────────
        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", **pad)

        self._select_all_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            row3,
            text="Select All",
            variable=self._select_all_var,
            command=self._on_select_all_toggle,
        ).pack(side="left", padx=(0, 24))

        self._turn_status_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            row3,
            text='Turn status to "Contract Generated"',
            variable=self._turn_status_var,
            command=self._save_state,
        ).pack(side="left")

        # ── Row 4: Data table ──────────────────────────────────────────
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=4)

        ctk.CTkLabel(table_frame,
                     text="Filtered Settlements",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=8, pady=(6, 0))

        self._table = DataTable(table_frame)
        self._table.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Row 5: Generate button ─────────────────────────────────────
        self._gen_btn = ctk.CTkButton(
            self,
            text="Generate Consolidate Settlements",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_generate,
        )
        self._gen_btn.pack(fill="x", padx=12, pady=10)

    # ------------------------------------------------------------------
    # State save / restore
    # ------------------------------------------------------------------

    def _restore_state(self) -> None:
        path = self._cfg.get("input_excel_path", "")
        if path:
            self._excel_var.set(path)
            self._load_excel(path, restore=True)

        self._only_2nd_var.set(self._cfg.get("status_filter_mode", "2nd_ver") == "2nd_ver")
        self._on_2nd_ver_toggle(save=False)

        self._select_all_var.set(self._cfg.get("select_all", True))
        self._table.set_select_mode(not self._select_all_var.get())

        self._turn_status_var.set(self._cfg.get("turn_status_flag", False))

    def _save_state(self) -> None:
        self._cfg["input_excel_path"] = self._excel_var.get()
        self._cfg["sub_category_selection"] = self._subcat_widget.get_selected()
        self._cfg["status_filter_mode"] = (
            "2nd_ver" if self._only_2nd_var.get() else "custom"
        )
        self._cfg["status_selection"] = self._status_widget.get_selected()
        self._cfg["select_all"] = self._select_all_var.get()
        self._cfg["turn_status_flag"] = self._turn_status_var.get()
        settings.save(self._cfg)

    # ------------------------------------------------------------------
    # Excel loading
    # ------------------------------------------------------------------

    def _browse_excel(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Input Excel",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if path:
            self._excel_var.set(path)
            self._load_excel(path)
            self._save_state()

    def _load_excel(self, path: str, restore: bool = False) -> None:
        try:
            df = data_loader.load_input_excel(path)
        except Exception as exc:
            messagebox.showerror("Load Error", str(exc))
            return

        self._raw_df = df

        subcats = data_loader.get_unique_subcategories(df)
        saved_subcats = self._cfg.get("sub_category_selection", [])
        self._subcat_widget.set_options(
            subcats,
            selected=saved_subcats if (restore and saved_subcats) else None,
        )

        statuses = data_loader.get_unique_statuses(df)
        saved_statuses = self._cfg.get("status_selection", [])
        self._status_widget.set_options(
            statuses,
            selected=saved_statuses if (restore and saved_statuses) else None,
        )

        self._apply_filters()

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _on_filter_change(self, _: Any = None) -> None:
        self._apply_filters()
        self._save_state()

    def _on_2nd_ver_toggle(self, save: bool = True) -> None:
        if self._only_2nd_var.get():
            self._status_label.pack_forget()
            self._status_widget.pack_forget()
        else:
            self._status_label.pack(side="left", padx=(12, 0))
            self._status_widget.pack(side="left")
        self._apply_filters()
        if save:
            self._save_state()

    def _apply_filters(self) -> None:
        if self._raw_df is None:
            return

        selected_subcats = self._subcat_widget.get_selected()
        all_subcats = data_loader.get_unique_subcategories(self._raw_df)
        sub_filter = selected_subcats if len(selected_subcats) < len(all_subcats) else None

        if self._only_2nd_var.get():
            status_filter = [_STATUS_2ND_VER]
        else:
            selected_statuses = self._status_widget.get_selected()
            all_statuses = data_loader.get_unique_statuses(self._raw_df)
            status_filter = (
                selected_statuses if len(selected_statuses) < len(all_statuses) else None
            )

        self._filtered_df = data_loader.filter_data(
            self._raw_df, sub_filter, status_filter
        )
        self._table.load_data(self._filtered_df)

    # ------------------------------------------------------------------
    # Select-all toggle
    # ------------------------------------------------------------------

    def _on_select_all_toggle(self) -> None:
        self._table.set_select_mode(not self._select_all_var.get())
        self._save_state()

    # ------------------------------------------------------------------
    # Generate flow
    # ------------------------------------------------------------------

    def _on_generate(self) -> None:
        if self._filtered_df is None or self._filtered_df.empty:
            messagebox.showwarning("No Data", "No data to process after filtering.")
            return

        # Determine which rows to process
        if self._select_all_var.get():
            process_df = self._filtered_df.copy()
        else:
            process_df = self._table.get_selected_data()
            if process_df.empty:
                messagebox.showwarning("No Selection", "Please select at least one row.")
                return

        # ── Step 1: iCertis codes ──────────────────────────────────────
        supplier_keys = collect_supplier_keys(process_df)
        icertis_dlg = IcertisDialog(self, supplier_keys)
        self.wait_window(icertis_dlg)
        icertis_codes = icertis_dlg.get_result()
        if icertis_codes is None:
            return   # user cancelled

        # ── Step 2: Quarter selection ──────────────────────────────────
        quarter_dlg = QuarterDialog(self)
        self.wait_window(quarter_dlg)
        quarter_info = quarter_dlg.get_result()
        if quarter_info is None:
            return   # user cancelled

        effective_date = quarter_info["effective_date"]

        # ── Step 3: Load settlement info ──────────────────────────────
        si_path = self._cfg.get("settlement_info_path", "")
        if not si_path or not Path(si_path).exists():
            # Try default location
            base = Path(__file__).resolve().parents[3]
            default = base / "data" / "settlement info" / "settlement info.xlsx"
            if default.exists():
                si_path = str(default)
            else:
                si_path = filedialog.askopenfilename(
                    title="Select Settlement Info Excel",
                    filetypes=[("Excel files", "*.xlsx *.xls")],
                )
                if not si_path:
                    return
                self._cfg["settlement_info_path"] = si_path
                settings.save(self._cfg)

        try:
            settlement_info = data_merger.load_settlement_info(si_path)
        except Exception as exc:
            messagebox.showerror("Settlement Info Error", str(exc))
            return

        # ── Step 4: Merge + write settlement data.xlsx ─────────────────
        try:
            merged_df = data_merger.merge_data(
                process_df, settlement_info, icertis_codes, effective_date
            )
        except Exception as exc:
            messagebox.showerror("Merge Error", str(exc))
            return

        base = Path(__file__).resolve().parents[3]
        input_folder = base / "data" / "input"
        input_folder.mkdir(parents=True, exist_ok=True)
        try:
            data_merger.save_settlement_data(merged_df, input_folder)
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc))
            return

        # ── Step 5: Find Word template ─────────────────────────────────
        tmpl_folder = self._cfg.get("template_folder", "")
        template_path: Path | None = None
        if tmpl_folder:
            candidates = list(Path(tmpl_folder).glob("*.docx"))
            if candidates:
                template_path = candidates[0]

        if template_path is None:
            default_tmpl = base / "data" / "template"
            candidates = list(default_tmpl.glob("*.docx"))
            if candidates:
                template_path = candidates[0]

        if template_path is None:
            t = filedialog.askopenfilename(
                title="Select Word Template",
                filetypes=[("Word documents", "*.docx")],
            )
            if not t:
                return
            template_path = Path(t)

        # ── Step 6: Determine output folder ───────────────────────────
        output_folder = self._cfg.get("output_folder", "")
        if not output_folder:
            output_folder = str(base / "data" / "output")

        # ── Step 7: Generate contracts (in a thread to keep UI alive) ──
        self._gen_btn.configure(state="disabled", text="Generating…")
        self.update()

        def _run() -> None:
            try:
                out_paths = contract_generator.generate_contracts(
                    merged_df, template_path, output_folder
                )

                if self._turn_status_var.get():
                    excel_path = self._excel_var.get()
                    if excel_path and Path(excel_path).exists():
                        contract_generator.update_status_in_excel(
                            excel_path, self._raw_df, process_df
                        )
                        # Reload data to reflect status change
                        self.after(0, lambda: self._load_excel(excel_path))

                self.after(0, lambda: self._on_generate_done(out_paths, None))
            except Exception as exc:
                self.after(0, lambda: self._on_generate_done([], exc))

        threading.Thread(target=_run, daemon=True).start()

    def _on_generate_done(self, out_paths: list, error: Exception | None) -> None:
        self._gen_btn.configure(state="normal", text="Generate Consolidate Settlements")

        if error:
            messagebox.showerror("Generation Error", str(error))
            return

        if out_paths:
            folder = str(Path(out_paths[0]).parent)
            messagebox.showinfo(
                "Done",
                f"Generated {len(out_paths)} contract(s).\n\nOutput folder:\n{folder}",
            )
        else:
            messagebox.showwarning("No Contracts", "No contracts were generated.")

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        self._save_state()
        self.destroy()
