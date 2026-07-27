"""Moderación — lista de palabras prohibidas con acciones configurables."""
import customtkinter as ctk
from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, GRN, GRN_T, RED, RED_T_LIGHT as RED_T, AMB as YLW, TXT, TXT_DIM as MUT
from src.ui.widgets import mk, lb
from src.utils.moderation import (
    get_words, add_word, remove_word,
    get_default_action, set_default_action,
    get_timeout_seconds, set_timeout_seconds,
)

ACTION_OPTIONS = ["log", "delete", "timeout"]
ACTION_LABELS = {"log": "📝 Solo registro", "delete": "🗑 Borrar mensaje", "timeout": "⏱ Timeout"}


def build_tab_moderacion(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(
        parent, fg_color=BG, corner_radius=0,
        scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
    )

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🛡  Moderación", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Palabras prohibidas y acciones automáticas", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    # ── Global config ──
    cfg_card = mk(tab)
    cfg_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(cfg_card, "⚙  Configuración global", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    cfg_frame = ctk.CTkFrame(cfg_card, fg_color="transparent")
    cfg_frame.pack(fill="x", padx=14, pady=(0, 10))
    cfg_frame.grid_columnconfigure(3, weight=1)

    lb(cfg_frame, "Acción por defecto:", sz=10, col=MUT).grid(row=0, column=0, sticky="w", pady=3)
    default_action_var = ctk.StringVar(value=get_default_action())
    def_action_menu = ctk.CTkOptionMenu(
        cfg_frame, values=[ACTION_LABELS[a] for a in ACTION_OPTIONS],
        fg_color=CARD2, text_color=TXT, button_color=PURP, button_hover_color=BORD,
        font=("Segoe UI", 10), height=28,
        command=lambda v: None,
    )
    def_action_menu.set(ACTION_LABELS[get_default_action()])
    def_action_menu.grid(row=0, column=1, sticky="w", padx=(8, 4), pady=3)

    def save_default():
        label = def_action_menu.get()
        for a, l in ACTION_LABELS.items():
            if l == label:
                set_default_action(a)
                self.log(f"✅ Acción por defecto cambiada a: {l}")
                refresh_list()
                break

    ctk.CTkButton(cfg_frame, text="💾", fg_color=GRN, text_color=GRN_T,
                   height=26, corner_radius=6, width=32, command=save_default
                   ).grid(row=0, column=2, padx=(0, 12), pady=3)

    lb(cfg_frame, "Timeout (segundos):", sz=10, col=MUT).grid(row=1, column=0, sticky="w", pady=3)
    timeout_entry = ctk.CTkEntry(cfg_frame, font=("Consolas", 11), fg_color=CARD, text_color=TXT,
                                  border_color=BORD, width=60)
    timeout_entry.insert(0, str(get_timeout_seconds()))
    timeout_entry.grid(row=1, column=1, sticky="w", padx=(8, 4), pady=3)

    def save_timeout():
        try:
            set_timeout_seconds(int(timeout_entry.get()))
            self.log(f"✅ Timeout actualizado: {timeout_entry.get()}s")
        except ValueError:
            self.log("❌  Ingresa un número válido")

    ctk.CTkButton(cfg_frame, text="💾", fg_color=GRN, text_color=GRN_T,
                   height=26, corner_radius=6, width=32, command=save_timeout
                   ).grid(row=1, column=2, padx=(0, 12), pady=3)

    # ── Add word ──
    add_card = mk(tab)
    add_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(add_card, "➕  Agregar palabra prohibida", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    ag = ctk.CTkFrame(add_card, fg_color="transparent")
    ag.pack(fill="x", padx=14, pady=(0, 10))
    ag.grid_columnconfigure(1, weight=1)

    lb(ag, "Palabra:", sz=10, col=MUT).grid(row=0, column=0, sticky="w", pady=3)
    word_entry = ctk.CTkEntry(ag, font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD)
    word_entry.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)

    lb(ag, "Acción:", sz=10, col=MUT).grid(row=1, column=0, sticky="w", pady=3)
    action_var = ctk.StringVar(value=ACTION_LABELS[get_default_action()])
    action_menu = ctk.CTkOptionMenu(
        ag, values=[ACTION_LABELS[a] for a in ACTION_OPTIONS],
        fg_color=CARD2, text_color=TXT, button_color=PURP, button_hover_color=BORD,
        font=("Segoe UI", 10), height=28,
    )
    action_menu.set(ACTION_LABELS[get_default_action()])
    action_menu.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=3)

    def do_add():
        word = word_entry.get().strip()
        if not word:
            self.log("❌  Ingresa una palabra")
            return
        label = action_menu.get()
        action = None
        for a, l in ACTION_LABELS.items():
            if l == label:
                action = a
                break
        add_word(word, action)
        word_entry.delete(0, "end")
        refresh_list()
        self.log(f"✅  '{word}' agregada con acción: {ACTION_LABELS.get(action, action)}")

    ctk.CTkButton(ag, text="➕  Agregar", fg_color=GRN, text_color=GRN_T,
                   height=28, corner_radius=8, command=do_add
                   ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

    # ── Word list ──
    list_card = mk(tab)
    list_card.pack(fill="x", padx=14, pady=(0, 12))
    lb(list_card, "📋  Lista de palabras prohibidas", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    list_container = ctk.CTkFrame(list_card, fg_color="transparent")
    list_container.pack(fill="x", padx=14, pady=(0, 6))

    def refresh_list():
        for w in list_container.winfo_children():
            w.destroy()
        words = get_words()
        if not words:
            lb(list_container, "No hay palabras prohibidas configuradas.", sz=10, col=MUT).pack(pady=10)
            return
        for w in words:
            row = ctk.CTkFrame(list_container, fg_color=CARD2)
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=1)

            label = ACTION_LABELS.get(w["action"], w["action"])
            lb(row, f"🔴  {w['word']}  —  {label}", sz=11, col=TXT).grid(row=0, column=0, sticky="w", padx=10, pady=6)

            ctk.CTkButton(row, text="🗑", fg_color="#7f1d1d", text_color=RED_T,
                           height=26, corner_radius=6, width=32,
                           command=lambda word=w["word"]: do_remove(word)
                           ).grid(row=0, column=1, sticky="e", padx=6, pady=4)

    def do_remove(word):
        remove_word(word)
        refresh_list()
        self.log(f"🗑  '{word}' eliminada")

    refresh_list()

    return tab
