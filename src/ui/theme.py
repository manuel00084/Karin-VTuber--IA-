"""Karin VTuber — Glassmorphism Theme Constants."""
import customtkinter as ctk

# ── Core Colors ──
BG = "#0a0a0f"
BG_SECONDARY = "#111118"
CARD_BG = "rgba(255,255,255,0.03)"  # CTk uses hex, approximate
CARD_BG_HEX = "#14141f"
CARD2 = "#1e1e2e"
CARD_BORDER = "#252540"
CARD_HOVER = "#1a1a2e"
BORD = "#252540"

# ── Accent Colors ──
PURP = "#8b5cf6"
PURP_DARK = "#6d28d9"
PURP_LIGHT = "#a78bfa"
CYAN = "#06b6d4"
CYAN_DARK = "#0891b2"
PINK = "#ec4899"
PINK_DARK = "#db2777"
GREEN = "#22c55e"
GRN = "#059669"
GRN_T = "#a7f3d0"
RED = "#dc2626"
RED_T = "#ef4444"
RED_T_LIGHT = "#fca5a5"
BLU = "#2563eb"
BLU_T = "#93c5fd"
AMB = "#d97706"
AMB_T = "#fcd34d"
YELLOW = "#eab308"

# ── Text ──
TXT = "#e2e8f0"
TXT_DIM = "#94a3b8"
TXT_MUTED = "#64748b"
MUT = "#94a3b8"
WHITE = "#ffffff"

# ── Layout ──
SIDE = "#12121e"
LOGBG = "#080812"

# ── Component Sizes ──
CORNER = 12
CORNER_SM = 8
CORNER_LG = 16
PAD = 14
PAD_SM = 8
PAD_XS = 4

# ── Fonts ──
FONT = ("Segoe UI", 12)
FONT_BOLD = ("Segoe UI", 13, "bold")
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 14)
FONT_MONO = ("Consolas", 11)
FONT_SMALL = ("Segoe UI", 10)
FONT_TINY = ("Segoe UI", 9)

# ── CTk Theme ──
def apply_theme():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

# ── Card Styles ──
CARD_STYLE = {
    "fg_color": CARD_BG_HEX,
    "corner_radius": CORNER,
    "border_width": 1,
    "border_color": CARD_BORDER,
}

# ── Button Styles ──
BTN_PRIMARY = {"fg_color": PURP, "hover_color": PURP_DARK, "corner_radius": CORNER_SM, "font": FONT}
BTN_DANGER = {"fg_color": "#dc2626", "hover_color": "#b91c1c", "corner_radius": CORNER_SM, "font": FONT}
BTN_SECONDARY = {"fg_color": "#374151", "hover_color": "#4b5563", "corner_radius": CORNER_SM, "font": FONT}
BTN_SUCCESS = {"fg_color": GREEN, "hover_color": "#16a34a", "corner_radius": CORNER_SM, "font": FONT}

# ── Entry Styles ──
ENTRY_STYLE = {
    "fg_color": "#1e1e2e",
    "border_color": CARD_BORDER,
    "text_color": TXT,
    "font": FONT_MONO,
    "corner_radius": CORNER_SM,
}
