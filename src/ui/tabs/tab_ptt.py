"""PTT Tab — Push-to-Talk control."""
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T, RED, RED_T_LIGHT as RED_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, bt


def build_tab_ptt(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    cv = mk(tab, accent=True)
    cv.pack(fill="x", padx=14, pady=(12, 6))
    inner = ctk.CTkFrame(cv, fg_color="transparent")
    inner.pack(fill="x", padx=14, pady=(10, 10))
    lb(inner, "🎤  Push-to-Talk", sz=11, bold=True, col=PURP).pack(side="left", padx=(0, 12))
    lb(inner, "CTRL +", sz=11, col=TXT).pack(side="left", padx=(0, 4))
    self.ptt_key_entry = ctk.CTkEntry(inner, width=60, font=("Consolas", 12, "bold"),
                                       fg_color=BG, text_color=TXT, border_color=BORD,
                                       justify="center")
    self.ptt_key_entry.pack(side="left", padx=(0, 12))
    from src.core.config import load_config as _lc
    saved_ptt_key = _lc().get("PTT_KEY", "F9")
    self.ptt_key_entry.insert(0, saved_ptt_key)
    lb(inner, "Mantén para hablar", sz=10, col=MUT).pack(side="left", padx=(0, 12))
    bt(inner, "🗑  Borrar memoria", RED, RED_T, self._borrar_memoria, h=32).pack(side="right", padx=(3, 0))
    bt(inner, "💾 Guardar config", GRN, GRN_T, self._guardar_config_panel, h=32).pack(side="right", padx=(3, 0))
    bt(inner, "🎤 Hablar", GRN, GRN_T, self.ptt_click, h=32).pack(side="right", padx=(3, 0))

    return tab
