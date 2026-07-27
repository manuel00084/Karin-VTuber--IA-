"""Chat IA Tab — groups Comentarista, Traductor, and API Key as sub-tabs."""
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb
from src.ui.tabs.tab_comentarista import build_tab_comentarista
from src.ui.tabs.tab_traductor import build_tab_traductor
from src.ui.tabs.tab_api_key import build_tab_api_key
from src.ui.tabs.tab_perfil_ia import build_tab_perfil_ia
from src.ui.tabs.tab_perfil_streamer import build_tab_perfil_streamer
from src.ui.tabs.tab_ptt import build_tab_ptt
from src.ui.tabs.tab_game_control import build_tab_game_control


def build_tab_chat_ia(parent, app):
    self = app
    tab = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)

    tabview = ctk.CTkTabview(
        tab, fg_color="transparent",
        segmented_button_fg_color=CARD,
        segmented_button_selected_color=PURP,
        segmented_button_unselected_color=CARD2,
        segmented_button_selected_hover_color=PURP,
        segmented_button_unselected_hover_color="#2a2a42",
        text_color=TXT,
    )
    tabview.pack(fill="both", expand=True, padx=4, pady=4)

    for label, builder in [
        ("Perfil IA", build_tab_perfil_ia),
        ("Perfil Streamer", build_tab_perfil_streamer),
        ("PTT", build_tab_ptt),
        ("Juegos", build_tab_game_control),
        ("Comentarista", build_tab_comentarista),
        ("Traductor", build_tab_traductor),
        ("API Key", build_tab_api_key),
    ]:
        sub = tabview.add(label)
        sf = ctk.CTkScrollableFrame(
            sub, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
        )
        sf.pack(fill="both", expand=True)
        builder(sub, app, frame=sf)

    return tab
