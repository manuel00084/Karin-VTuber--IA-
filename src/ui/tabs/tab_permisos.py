"""Permisos de comandos — quién puede usar cada comando."""
import customtkinter as ctk
from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, GRN, GRN_T, TXT, TXT_DIM as MUT
from src.ui.widgets import mk, lb
from src.utils.command_perms import (
    get_all_permissions, get_default, set_default, set_permission,
    remove_permission, LEVELS, LEVEL_LABELS,
)


def build_tab_permisos(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(
        parent, fg_color=BG, corner_radius=0,
        scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
    )

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🔐  Permisos de comandos", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Controla quién puede usar cada comando en Twitch",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    # ── Default ──
    def_card = mk(tab)
    def_card.pack(fill="x", padx=14, pady=(0, 6))

    default_var = ctk.StringVar(value=get_default())
    lb(def_card, "🏷  Permiso por defecto (comandos sin configurar)",
       sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    df = ctk.CTkFrame(def_card, fg_color="transparent")
    df.pack(fill="x", padx=14, pady=(0, 10))

    def_menu = ctk.CTkOptionMenu(
        df, values=[LEVEL_LABELS[l] for l in LEVELS],
        fg_color=CARD2, text_color=TXT, button_color=PURP, button_hover_color=BORD,
        font=("Segoe UI", 10), height=28,
    )
    def_menu.set(LEVEL_LABELS[get_default()])
    def_menu.pack(side="left", padx=(0, 8))

    def save_default():
        label = def_menu.get()
        for l, lb in LEVEL_LABELS.items():
            if lb == label:
                set_default(l)
                self.log(f"✅ Permiso por defecto cambiado a: {lb}")
                refresh_list()
                break

    ctk.CTkButton(df, text="💾  Guardar", fg_color=GRN, text_color=GRN_T,
                   height=28, corner_radius=8, command=save_default
                   ).pack(side="left")

    # ── Add / edit command ──
    add_card = mk(tab)
    add_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(add_card, "➕  Configurar comando", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    ag = ctk.CTkFrame(add_card, fg_color="transparent")
    ag.pack(fill="x", padx=14, pady=(0, 10))
    ag.grid_columnconfigure(1, weight=1)

    lb(ag, "Comando:", sz=10, col=MUT).grid(row=0, column=0, sticky="w", pady=3)
    cmd_entry = ctk.CTkEntry(ag, font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD,
                              placeholder_text="ej: sp, showtime, juegos")
    cmd_entry.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)

    lb(ag, "Permiso:", sz=10, col=MUT).grid(row=1, column=0, sticky="w", pady=3)
    perm_menu = ctk.CTkOptionMenu(
        ag, values=[LEVEL_LABELS[l] for l in LEVELS],
        fg_color=CARD2, text_color=TXT, button_color=PURP, button_hover_color=BORD,
        font=("Segoe UI", 10), height=28,
    )
    perm_menu.set(LEVEL_LABELS[get_default()])
    perm_menu.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=3)

    def do_add():
        cmd = cmd_entry.get().strip().lstrip("!")
        if not cmd:
            self.log("❌  Ingresa un nombre de comando")
            return
        label = perm_menu.get()
        level = None
        for l, lb in LEVEL_LABELS.items():
            if lb == label:
                level = l
                break
        set_permission(cmd, level)
        cmd_entry.delete(0, "end")
        refresh_list()
        self.log(f"✅  !{cmd} → {LEVEL_LABELS[level]}")

    ctk.CTkButton(ag, text="➕  Agregar / Actualizar", fg_color=GRN, text_color=GRN_T,
                   height=28, corner_radius=8, command=do_add
                   ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

    # ── List ──
    list_card = mk(tab)
    list_card.pack(fill="x", padx=14, pady=(0, 12))
    lb(list_card, "📋  Comandos configurados", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    list_container = ctk.CTkFrame(list_card, fg_color="transparent")
    list_container.pack(fill="x", padx=14, pady=(0, 6))

    def refresh_list():
        for w in list_container.winfo_children():
            w.destroy()
        perms, default = get_all_permissions(), get_default()
        if not perms:
            lb(list_container,
               f"No hay comandos configurados. Por defecto: {LEVEL_LABELS[default]}",
               sz=10, col=MUT).pack(pady=10)
            return
        for cmd, level in sorted(perms.items()):
            row = ctk.CTkFrame(list_container, fg_color=CARD2)
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=1)

            lb(row, f"!{cmd}  →  {LEVEL_LABELS.get(level, level)}", sz=11, col=TXT
               ).grid(row=0, column=0, sticky="w", padx=10, pady=6)

            bf = ctk.CTkFrame(row, fg_color="transparent")
            bf.grid(row=0, column=1, sticky="e", padx=6, pady=4)

            def make_edit(c=cmd):
                cmd_entry.delete(0, "end")
                cmd_entry.insert(0, c)
                perm_menu.set(LEVEL_LABELS.get(get_permission(c), LEVEL_LABELS[get_default()]))

            ctk.CTkButton(bf, text="✏️", fg_color="#1e3a5f", text_color="#93c5fd",
                           height=24, corner_radius=6, width=32,
                           command=make_edit).pack(side="left", padx=1)

            ctk.CTkButton(bf, text="🗑", fg_color="#7f1d1d", text_color="#fca5a5",
                           height=24, corner_radius=6, width=32,
                           command=lambda c=cmd: do_remove(c)).pack(side="left", padx=1)

    def do_remove(cmd):
        remove_permission(cmd)
        refresh_list()
        self.log(f"🗑  Permiso de !{cmd} eliminado (usará el default)")

    from src.utils.command_perms import get_permission
    refresh_list()

    return tab
