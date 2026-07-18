"""
Entry point for Settlement Form Generator.

customtkinter appearance settings MUST be set at module level,
before any CTk widget is instantiated.
"""
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def main() -> None:
    from settlement_form.ui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
