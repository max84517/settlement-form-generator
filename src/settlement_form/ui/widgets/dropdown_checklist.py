"""
DropdownChecklist – a custom customtkinter widget that looks like a
ComboBox but opens a scrollable checklist of checkboxes.

Usage:
    widget = DropdownChecklist(parent, options=["A", "B", "C"],
                               on_change=my_callback)
    # get selected values
    selected = widget.get_selected()
    # set programmatically
    widget.set_selected(["A", "C"])
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk


class DropdownChecklist(ctk.CTkFrame):
    """A button that, when clicked, opens a floating checklist popup."""

    def __init__(
        self,
        master: ctk.CTkFrame | ctk.CTk | ctk.CTkToplevel,
        options: list[str] | None = None,
        on_change: Callable[[list[str]], None] | None = None,
        placeholder: str = "Select…",
        width: int = 260,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._opt_list: list[str] = options or []
        self._selected: set[str] = set(self._opt_list)  # all selected by default
        self._on_change = on_change
        self._placeholder = placeholder
        self._popup: ctk.CTkToplevel | None = None
        self._root_click_id: str | None = None   # root <Button-1> binding id

        self._btn = ctk.CTkButton(
            self,
            text=self._label_text(),
            width=width,
            anchor="w",
            command=self._toggle_popup,
        )
        self._btn.pack(fill="x", expand=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_selected(self) -> list[str]:
        return sorted(self._selected)

    def set_selected(self, values: list[str]) -> None:
        self._selected = set(values)
        self._btn.configure(text=self._label_text())

    def set_options(self, options: list[str], selected: list[str] | None = None) -> None:
        """Replace the option list and optionally set the selection."""
        self._opt_list = options
        if selected is None:
            self._selected = set(options)   # default: all selected
        else:
            self._selected = set(selected) & set(options)
        self._btn.configure(text=self._label_text())
        if self._popup and self._popup.winfo_exists():
            self._close_popup()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _label_text(self) -> str:
        n_selected = len(self._selected)
        n_total = len(self._opt_list)
        if n_total == 0:
            return self._placeholder
        if n_selected == 0:
            return "(none selected)"
        if n_selected == n_total:
            return f"All ({n_total})"
        if n_selected <= 3:
            return ", ".join(sorted(self._selected))
        return f"{n_selected} / {n_total} selected"

    def _toggle_popup(self) -> None:
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
            return
        self._open_popup()

    def _open_popup(self) -> None:
        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        # NOTE: do NOT call grab_set() – it intercepts all mouse events
        # (including the toggle button), making the popup impossible to close.
        self._popup = popup

        # Position below the button
        self.update_idletasks()
        x = self._btn.winfo_rootx()
        y = self._btn.winfo_rooty() + self._btn.winfo_height() + 2
        popup.geometry(f"+{x}+{y}")
        popup.lift()

        frame = ctk.CTkFrame(popup)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Select All / Clear All buttons
        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=6, pady=(6, 2))
        ctk.CTkButton(
            btn_row, text="Select All", width=100,
            command=lambda: self._bulk_select(True, vars_),
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            btn_row, text="Clear All", width=100,
            command=lambda: self._bulk_select(False, vars_),
        ).pack(side="left")

        # Scrollable checklist
        scroll = ctk.CTkScrollableFrame(frame, height=200, width=280)
        scroll.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        vars_: dict[str, ctk.BooleanVar] = {}
        for opt in self._opt_list:
            var = ctk.BooleanVar(value=(opt in self._selected))
            vars_[opt] = var
            ctk.CTkCheckBox(
                scroll,
                text=opt,
                variable=var,
                command=lambda o=opt, v=var: self._on_check(o, v),
            ).pack(anchor="w", pady=2)

        # After the popup is fully drawn, register an app-level click watcher.
        # We delay slightly so the current ButtonRelease that opened the popup
        # does not immediately trigger the watcher.
        popup.after(150, self._register_root_click)

    # ------------------------------------------------------------------
    # Outside-click detection via root window binding
    # ------------------------------------------------------------------

    def _register_root_click(self) -> None:
        """Bind a <Button-1> listener on the root window to close the popup
        when the user clicks anywhere outside it."""
        if not (self._popup and self._popup.winfo_exists()):
            return
        root = self.winfo_toplevel()
        self._root_click_id = root.bind("<Button-1>", self._on_root_click, add="+")

    def _on_root_click(self, event) -> None:
        """Called whenever <Button-1> fires anywhere in the main window."""
        if not (self._popup and self._popup.winfo_exists()):
            self._cleanup_root_binding()
            return

        self._popup.update_idletasks()
        px = self._popup.winfo_rootx()
        py = self._popup.winfo_rooty()
        pw = self._popup.winfo_width()
        ph = self._popup.winfo_height()
        inside_popup = (px <= event.x_root <= px + pw and
                        py <= event.y_root <= py + ph)
        if inside_popup:
            return  # click is inside the popup – do nothing

        # Click is outside popup. If it landed on the toggle button itself,
        # let _toggle_popup handle the close so it doesn't reopen.
        bx = self._btn.winfo_rootx()
        by = self._btn.winfo_rooty()
        bw = self._btn.winfo_width()
        bh = self._btn.winfo_height()
        on_button = (bx <= event.x_root <= bx + bw and
                     by <= event.y_root <= by + bh)
        if on_button:
            return  # _toggle_popup will fire and close the popup

        # Genuine outside click – close the popup
        self._close_popup()

    def _close_popup(self) -> None:
        self._cleanup_root_binding()
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None

    def _cleanup_root_binding(self) -> None:
        if self._root_click_id:
            try:
                root = self.winfo_toplevel()
                root.unbind("<Button-1>", self._root_click_id)
            except Exception:
                pass
            self._root_click_id = None

    def _on_check(self, option: str, var: ctk.BooleanVar) -> None:
        if var.get():
            self._selected.add(option)
        else:
            self._selected.discard(option)
        self._btn.configure(text=self._label_text())
        if self._on_change:
            self._on_change(self.get_selected())

    def _bulk_select(self, select_all: bool, vars_: dict[str, ctk.BooleanVar]) -> None:
        for opt, var in vars_.items():
            var.set(select_all)
            if select_all:
                self._selected.add(opt)
            else:
                self._selected.discard(opt)
        self._btn.configure(text=self._label_text())
        if self._on_change:
            self._on_change(self.get_selected())


