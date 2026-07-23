"""
Entry point for Settlement Form Generator.

customtkinter appearance settings MUST be set at module level,
before any CTk widget is instantiated.
"""
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def main() -> None:
    from settlement_form.ui.login_dialog import LoginDialog
    from settlement_form.ui.main_window import MainWindow

    # ── Step 1: user login ────────────────────────────────────────────
    login = LoginDialog()
    login.mainloop()
    username = login.get_result()

    if not username:
        return   # user closed the login window → exit

    # ── Step 2: main application ──────────────────────────────────────
    app = MainWindow(username=username)
    app.mainloop()


if __name__ == "__main__":
    main()
