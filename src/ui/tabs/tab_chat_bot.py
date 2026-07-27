"""Chat Bot Tab — combines Bot Speaker, Alertas, Moderación, Permisos, Stream Tools, and Voice Commands as sub-tabs."""
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    TXT,
)
from src.ui.tabs.tab_bot_speaker import build_tab_bot_speaker
from src.ui.tabs.tab_alertas import build_tab_alertas
from src.ui.tabs.tab_moderacion import build_tab_moderacion
from src.ui.tabs.tab_permisos import build_tab_permisos
from src.ui.tabs.tab_stream_tools import build_tab_stream_tools
from src.ui.tabs.tab_voice_commands import build_tab_voice_commands
from src.ui.tabs.tab_chat_overlay import build_tab_chat_overlay
from src.ui.tabs.tab_discord import build_tab_discord


def build_tab_chat_bot(parent, app):
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
        ("Bot Speaker", build_tab_bot_speaker),
        ("Alertas", build_tab_alertas),
        ("Moderación", build_tab_moderacion),
        ("Permisos", build_tab_permisos),
        ("Stream Tools", build_tab_stream_tools),
        ("Voz", build_tab_voice_commands),
        ("Chat Overlay", build_tab_chat_overlay),
        ("Discord", build_tab_discord),
    ]:
        sub = tabview.add(label)
        sf = ctk.CTkScrollableFrame(
            sub, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
        )
        sf.pack(fill="both", expand=True)
        builder(sub, app, frame=sf)

    return tab
