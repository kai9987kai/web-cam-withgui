import tkinter as tk
from tkinter import ttk


class StudioTheme:
    """
    Studio Pro Obsidian Dark Palette & Modern TTK Styling.
    """

    BG_DARK = "#0C0D14"
    BG_SIDEBAR = "#141622"
    BG_CARD = "#1C1F30"
    BG_CARD_LIGHT = "#25293E"
    BORDER = "#2B3048"

    ACCENT_CYAN = "#00D2FF"
    ACCENT_PURPLE = "#8B5CF6"
    RECORD_RED = "#EF4444"
    RECORD_ACTIVE = "#DC2626"
    SUCCESS_GREEN = "#10B981"
    WARNING_AMBER = "#F59E0B"

    TEXT_MAIN = "#F8FAFC"
    TEXT_MUTED = "#94A3B8"
    TEXT_DIM = "#64748B"

    @classmethod
    def apply(cls, root: tk.Tk):
        """Apply dark styling across all ttk widgets."""
        root.configure(bg=cls.BG_DARK)
        style = ttk.Style(root)
        style.theme_use("clam")

        # Generic Frames
        style.configure("TFrame", background=cls.BG_DARK)
        style.configure("Sidebar.TFrame", background=cls.BG_SIDEBAR)
        style.configure("Card.TFrame", background=cls.BG_CARD)
        style.configure("CardLight.TFrame", background=cls.BG_CARD_LIGHT)

        # Labels
        style.configure("TLabel", background=cls.BG_DARK, foreground=cls.TEXT_MAIN, font=("Segoe UI", 9))
        style.configure("Sidebar.TLabel", background=cls.BG_SIDEBAR, foreground=cls.TEXT_MAIN, font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=cls.BG_CARD, foreground=cls.TEXT_MAIN, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=cls.BG_SIDEBAR, foreground=cls.ACCENT_CYAN, font=("Segoe UI", 11, "bold"))
        style.configure("Subheader.TLabel", background=cls.BG_CARD, foreground=cls.TEXT_MAIN, font=("Segoe UI", 10, "bold"))
        style.configure("Title.TLabel", background=cls.BG_SIDEBAR, foreground=cls.TEXT_MAIN, font=("Segoe UI", 14, "bold"))
        style.configure("Muted.TLabel", background=cls.BG_CARD, foreground=cls.TEXT_MUTED, font=("Segoe UI", 8))
        style.configure("Badge.TLabel", background=cls.BG_CARD_LIGHT, foreground=cls.ACCENT_CYAN, font=("Segoe UI", 9, "bold"))

        # Buttons
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6,
                        background=cls.BG_CARD, foreground=cls.TEXT_MAIN, borderwidth=1, focusthickness=0)
        style.map("TButton",
                  background=[("active", cls.BG_CARD_LIGHT), ("disabled", cls.BORDER)],
                  foreground=[("disabled", cls.TEXT_DIM)])

        # Photo Action Button (Vibrant Emerald)
        style.configure("Photo.TButton", background=cls.SUCCESS_GREEN, foreground="#FFFFFF",
                        font=("Segoe UI", 11, "bold"), padding=8)
        style.map("Photo.TButton",
                  background=[("active", "#059669")])

        # Record Button (Vibrant Coral Red)
        style.configure("Record.TButton", background=cls.RECORD_RED, foreground="#FFFFFF",
                        font=("Segoe UI", 11, "bold"), padding=8)
        style.map("Record.TButton",
                  background=[("active", cls.RECORD_ACTIVE)])

        # Primary Action Button (Electric Cyan)
        style.configure("Primary.TButton", background=cls.ACCENT_CYAN, foreground="#0A101D",
                        font=("Segoe UI", 9, "bold"), padding=6)
        style.map("Primary.TButton",
                  background=[("active", "#00B4D8")])

        # Small Utility Button
        style.configure("Small.TButton", font=("Segoe UI", 8), padding=3,
                        background=cls.BG_CARD_LIGHT, foreground=cls.TEXT_MAIN)
        style.map("Small.TButton",
                  background=[("active", cls.BORDER)])

        # Combobox
        style.configure("TCombobox", fieldbackground=cls.BG_CARD, background=cls.BG_CARD_LIGHT,
                        foreground=cls.TEXT_MAIN, borderwidth=1, padding=5)
        style.map("TCombobox",
                  fieldbackground=[("readonly", cls.BG_CARD)],
                  selectbackground=[("readonly", cls.ACCENT_CYAN)],
                  selectforeground=[("readonly", "#0A101D")])

        # Notebook / Tabs
        style.configure("TNotebook", background=cls.BG_SIDEBAR, borderwidth=0)
        style.configure("TNotebook.Tab", background=cls.BG_CARD, foreground=cls.TEXT_MUTED,
                        padding=[12, 6], font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", cls.BG_SIDEBAR), ("active", cls.BG_CARD_LIGHT)],
                  foreground=[("selected", cls.ACCENT_CYAN), ("active", cls.TEXT_MAIN)])

        # Checkbutton & Radiobutton
        style.configure("TCheckbutton", background=cls.BG_CARD, foreground=cls.TEXT_MAIN, font=("Segoe UI", 9))
        style.map("TCheckbutton",
                  background=[("active", cls.BG_CARD)],
                  foreground=[("active", cls.ACCENT_CYAN)])

        style.configure("TRadiobutton", background=cls.BG_CARD, foreground=cls.TEXT_MAIN, font=("Segoe UI", 9))
        style.map("TRadiobutton",
                  background=[("active", cls.BG_CARD)],
                  foreground=[("active", cls.ACCENT_CYAN)])

        # Slider / Scale
        style.configure("Horizontal.TScale", background=cls.BG_CARD, troughcolor=cls.BG_DARK,
                        sliderrelief="flat", sliderthickness=14)

        # Progressbar
        style.configure("Horizontal.TProgressbar", background=cls.ACCENT_CYAN, troughcolor=cls.BG_DARK, borderwidth=0)

        # Separator
        style.configure("TSeparator", background=cls.BORDER)
