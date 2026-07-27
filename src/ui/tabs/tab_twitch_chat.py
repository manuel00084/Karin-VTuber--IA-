"""Twitch Chat Viewer — live chat messages with badges and colors."""
import customtkinter as ctk
from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, RED_T_LIGHT as RED_T, TXT, TXT_DIM as MUT
from src.ui.widgets import mk, lb
from src.bot.twitch_bot import get_chat_viewer_messages, clear_chat_viewer


def build_tab_twitch_chat(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(
        parent, fg_color=BG, corner_radius=0,
        scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
    )

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "💬  Chat de Twitch", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Mensajes en vivo del chat", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    chat_frame = ctk.CTkFrame(
        tab, fg_color=CARD, corner_radius=8, border_width=1, border_color=BORD,
    )
    chat_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

    chat_text = ctk.CTkTextbox(
        chat_frame, fg_color="transparent", text_color=TXT,
        font=("Segoe UI", 12), wrap="word", state="disabled",
        scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
    )
    chat_text.pack(fill="both", expand=True, padx=6, pady=6)

    def render_messages():
        msgs = get_chat_viewer_messages()
        chat_text.configure(state="normal")
        chat_text.delete("1.0", "end")
        for m in msgs[-150:]:
            color = m.get("color") or MUT
            badges_str = ""
            b = m.get("badges", {})
            if b.get("broadcaster"):
                badges_str += "🔴"
            elif b.get("mod"):
                badges_str += "🛡"
            elif b.get("vip"):
                badges_str += "⭐"
            elif b.get("subscriber"):
                badges_str += "🌟"

            name = m.get("display_name", m.get("user", "?"))
            msg = m.get("message", "")
            chat_text.insert("end", f"{badges_str} {name}: ")
            chat_text.insert("end", f"{msg}\n")
        chat_text.see("end")
        chat_text.configure(state="disabled")
        self.after(2000, render_messages)

    def do_clear():
        clear_chat_viewer()
        chat_text.configure(state="normal")
        chat_text.delete("1.0", "end")
        chat_text.configure(state="disabled")

    bottom = ctk.CTkFrame(tab, fg_color="transparent")
    bottom.pack(fill="x", padx=14, pady=(0, 12))

    ctk.CTkButton(bottom, text="🗑  Limpiar chat", fg_color="#7f1d1d", text_color=RED_T,
                   height=28, corner_radius=8, command=do_clear
                   ).pack(side="left")

    self.after(2000, render_messages)

    return tab
