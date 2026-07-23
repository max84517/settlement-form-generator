"""
LoginDialog – the first window shown on startup.

Lets the user select an existing profile, add a new one, or delete one.
Each profile remembers its own UI state (paths, filter selections, etc.).

Returns a username string via get_result(); None means the user closed
the window without logging in (app should exit).
"""
from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from settlement_form.config import settings


class LoginDialog(ctk.CTk):
    """Standalone CTk window shown before the main window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Settlement Form Generator — Select User")
        self.resizable(False, False)

        self._result: str | None = None
        self._selected_var = ctk.StringVar()
        self._user_rows: dict[str, ctk.CTkFrame] = {}   # username → row frame

        self._build_ui()
        self._center()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def get_result(self) -> str | None:
        return self._result

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="Settlement Form Generator",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=28, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text="Please select a user to continue",
            text_color=("gray50", "gray70"),
        ).pack(padx=28, pady=(0, 12))

        # ── User list (scrollable) ─────────────────────────────────────
        ctk.CTkLabel(self, text="Select User:", anchor="w",
                     font=ctk.CTkFont(weight="bold")).pack(
            fill="x", padx=28, pady=(0, 4))

        self._list_frame = ctk.CTkScrollableFrame(self, height=200, width=340)
        self._list_frame.pack(fill="x", padx=28, pady=(0, 8))

        self._refresh_user_list()

        # ── Add new user ───────────────────────────────────────────────
        sep = ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray35"))
        sep.pack(fill="x", padx=28, pady=(4, 8))

        ctk.CTkLabel(self, text="Add New User:", anchor="w",
                     font=ctk.CTkFont(weight="bold")).pack(
            fill="x", padx=28)

        add_row = ctk.CTkFrame(self, fg_color="transparent")
        add_row.pack(fill="x", padx=28, pady=(4, 0))

        self._new_name_var = ctk.StringVar()
        self._new_entry = ctk.CTkEntry(
            add_row,
            textvariable=self._new_name_var,
            placeholder_text="Enter name…",
            width=220,
        )
        self._new_entry.pack(side="left", padx=(0, 8))
        self._new_entry.bind("<Return>", lambda _e: self._add_user())

        ctk.CTkButton(add_row, text="Add User", width=110,
                      command=self._add_user).pack(side="left")

        # ── Login button ───────────────────────────────────────────────
        ctk.CTkButton(
            self,
            text="Login",
            height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._login,
        ).pack(fill="x", padx=28, pady=(16, 24))

    # ------------------------------------------------------------------
    # User list rendering
    # ------------------------------------------------------------------

    def _refresh_user_list(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._user_rows.clear()

        users = settings.load_users()
        last = settings.get_last_user()

        if not users:
            ctk.CTkLabel(
                self._list_frame,
                text="No users yet — add one below",
                text_color=("gray50", "gray60"),
            ).pack(pady=8)
            return

        for username in users:
            row = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkRadioButton(
                row,
                text=username,
                variable=self._selected_var,
                value=username,
            ).pack(side="left", padx=(4, 0))

            ctk.CTkButton(
                row,
                text="Delete",
                width=68,
                height=26,
                fg_color=("gray70", "gray30"),
                hover_color=("#c0392b", "#922b21"),
                command=lambda u=username: self._delete_user(u),
            ).pack(side="right", padx=(0, 4))

            self._user_rows[username] = row

        # Pre-select last user (or first if last not in list)
        if last in users:
            self._selected_var.set(last)
        elif users:
            self._selected_var.set(users[0])

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _add_user(self) -> None:
        name = self._new_name_var.get().strip()
        if not name:
            return
        users = settings.load_users()
        if name in users:
            messagebox.showwarning("Duplicate", f'User "{name}" already exists.',
                                   parent=self)
            return
        users.append(name)
        settings.save_users(users)
        self._new_name_var.set("")
        self._refresh_user_list()
        self._selected_var.set(name)   # auto-select the new user

    def _delete_user(self, username: str) -> None:
        if not messagebox.askyesno(
            "Delete User",
            f'Delete user "{username}" and all their settings?\n\nThis cannot be undone.',
            parent=self,
        ):
            return
        settings.delete_user(username)
        self._refresh_user_list()

    def _login(self) -> None:
        username = self._selected_var.get()
        if not username:
            messagebox.showwarning("No User Selected",
                                   "Please select or add a user first.",
                                   parent=self)
            return
        # Add to list if it doesn't exist yet (shouldn't happen normally)
        users = settings.load_users()
        if username not in users:
            users.append(username)
            settings.save_users(users)
        settings.set_last_user(username)
        self._result = username
        self.destroy()

    def _on_close(self) -> None:
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
