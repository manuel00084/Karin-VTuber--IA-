"""Stream Tools settings — quotes, raffle, queue, schedule, keywords, link blocking."""
import customtkinter as ctk
from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, GRN, GRN_T, RED, RED_T_LIGHT as RED_T, TXT, TXT_DIM as MUT
from src.ui.widgets import mk, lb
from src.utils.stream_tools import (
    quote_count, schedule_set, schedule_get, DAYS,
    keyword_add, keyword_remove, keyword_list,
    linkblock_set_whitelist, linkblock_get_whitelist, linkblock_set_action, linkblock_get_action,
    so_is_enabled, soset_enabled,
)


def build_tab_stream_tools(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(
        parent, fg_color=BG, corner_radius=0,
        scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
    )

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🛠  Herramientas del Stream", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Quotes, sorteos, cola, horario, keywords, links",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    # ── Schedule ──
    sched_card = mk(tab)
    sched_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(sched_card, "📅  Horario de streams", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))
    sched_data = schedule_get()

    sched_entries = {}
    sched_grid = ctk.CTkFrame(sched_card, fg_color="transparent")
    sched_grid.pack(fill="x", padx=14, pady=(0, 6))
    sched_grid.grid_columnconfigure(1, weight=1)

    for i, day in enumerate(DAYS):
        lb(sched_grid, day.capitalize() + ":", sz=10, col=MUT).grid(row=i, column=0, sticky="w", pady=2)
        ent = ctk.CTkEntry(sched_grid, font=("Consolas", 10), fg_color=CARD,
                            text_color=TXT, border_color=BORD,
                            placeholder_text="ej: 20:00 - 23:00")
        if sched_data.get(day):
            ent.insert(0, sched_data[day])
        ent.grid(row=i, column=1, sticky="ew", padx=(8, 0), pady=2)
        sched_entries[day] = ent

    def save_schedule():
        for day, ent in sched_entries.items():
            schedule_set(day, ent.get().strip())
        self.log("✅  Horario guardado")

    ctk.CTkButton(sched_grid, text="💾  Guardar horario", fg_color=GRN, text_color=GRN_T,
                   height=28, corner_radius=8, command=save_schedule
                   ).grid(row=len(DAYS), column=1, sticky="w", padx=(8, 0), pady=(6, 4))

    # ── Keywords ──
    kw_card = mk(tab)
    kw_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(kw_card, "🔑  Alertas por palabra clave", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    kw_add_frame = ctk.CTkFrame(kw_card, fg_color="transparent")
    kw_add_frame.pack(fill="x", padx=14, pady=(0, 4))
    kw_add_frame.grid_columnconfigure(1, weight=1)
    kw_add_frame.grid_columnconfigure(3, weight=1)

    lb(kw_add_frame, "Palabra:", sz=10, col=MUT).grid(row=0, column=0, sticky="w", pady=2)
    kw_word = ctk.CTkEntry(kw_add_frame, font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD)
    kw_word.grid(row=0, column=1, sticky="ew", padx=(8, 4), pady=2)

    lb(kw_add_frame, "Respuesta:", sz=10, col=MUT).grid(row=1, column=0, sticky="w", pady=2)
    kw_resp = ctk.CTkEntry(kw_add_frame, font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD)
    kw_resp.grid(row=1, column=1, sticky="ew", padx=(8, 4), pady=2)

    def do_add_kw():
        w = kw_word.get().strip().lower()
        r = kw_resp.get().strip()
        if w and r:
            keyword_add(w, r)
            kw_word.delete(0, "end")
            kw_resp.delete(0, "end")
            refresh_kw()
            self.log(f"✅  Keyword '{w}' agregada")

    ctk.CTkButton(kw_add_frame, text="➕  Agregar", fg_color=GRN, text_color=GRN_T,
                   height=28, corner_radius=8, command=do_add_kw
                   ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(4, 0))

    kw_list_frame = ctk.CTkFrame(kw_card, fg_color="transparent")
    kw_list_frame.pack(fill="x", padx=14, pady=(0, 8))

    def refresh_kw():
        for w in kw_list_frame.winfo_children():
            w.destroy()
        kws = keyword_list()
        if not kws:
            lb(kw_list_frame, "No hay keywords configuradas", sz=10, col=MUT).pack(pady=4)
            return
        for word, resp in sorted(kws.items()):
            row = ctk.CTkFrame(kw_list_frame, fg_color=CARD2)
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure(0, weight=1)
            lb(row, f"🔑  {word}  →  {resp[:50]}", sz=10, col=TXT).grid(row=0, column=0, sticky="w", padx=8, pady=4)
            ctk.CTkButton(row, text="🗑", fg_color="#7f1d1d", text_color=RED_T,
                           height=24, corner_radius=6, width=28,
                           command=lambda w=word: do_del_kw(w)
                           ).grid(row=0, column=1, sticky="e", padx=6, pady=2)

    def do_del_kw(word):
        keyword_remove(word)
        refresh_kw()
        self.log(f"🗑  Keyword '{word}' eliminada")

    refresh_kw()

    # ── Link blocking ──
    lb_card = mk(tab)
    lb_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(lb_card, "🔗  Bloqueo de enlaces", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    lbf = ctk.CTkFrame(lb_card, fg_color="transparent")
    lbf.pack(fill="x", padx=14, pady=(0, 8))
    lbf.grid_columnconfigure(1, weight=1)

    lb(lbf, "Acción:", sz=10, col=MUT).grid(row=0, column=0, sticky="w", pady=2)
    link_action_var = ctk.StringVar(value=linkblock_get_action())
    link_action_menu = ctk.CTkOptionMenu(
        lbf, values=["log", "delete", "timeout"],
        fg_color=CARD2, text_color=TXT, button_color=PURP, button_hover_color=BORD,
        font=("Segoe UI", 10), height=28,
    )
    link_action_menu.set(linkblock_get_action())
    link_action_menu.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=2)

    lb(lbf, "Whitelist (separado por coma):", sz=10, col=MUT).grid(row=1, column=0, sticky="w", pady=2)
    whitelist_ent = ctk.CTkEntry(lbf, font=("Consolas", 10), fg_color=CARD, text_color=TXT, border_color=BORD,
                                  placeholder_text="ej: twitch.tv, discord.gg")
    whitelist_ent.insert(0, ", ".join(linkblock_get_whitelist()))
    whitelist_ent.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=2)

    def save_linkblock():
        linkblock_set_action(link_action_menu.get())
        domains = [d.strip() for d in whitelist_ent.get().split(",") if d.strip()]
        linkblock_set_whitelist(domains)
        self.log(f"✅  Bloqueo de enlaces guardado (acción: {link_action_menu.get()})")

    ctk.CTkButton(lbf, text="💾  Guardar", fg_color=GRN, text_color=GRN_T,
                   height=28, corner_radius=8, command=save_linkblock
                   ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(4, 0))

    # ── Auto-shoutout toggle ──
    so_card = mk(tab)
    so_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(so_card, "⚡  Auto-Shoutout al recibir raid", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    so_var = ctk.BooleanVar(value=so_is_enabled())
    so_sw = ctk.CTkSwitch(so_card, text="  Activar auto-shoutout", variable=so_var,
                           onvalue=True, offvalue=False,
                           fg_color=CARD2, progress_color=BORD, button_color=PURP,
                           font=("Segoe UI", 11))
    so_sw.pack(anchor="w", padx=14, pady=(0, 8))

    def so_toggle():
        soset_enabled(so_var.get())
        self.log(f"✅  Auto-shoutout {'activado' if so_var.get() else 'desactivado'}")

    so_var.trace_add("write", lambda *_: so_toggle())

    # ── Chat translation toggle ──
    trans_card = mk(tab)
    trans_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(trans_card, "🌐  Traducción automática del chat", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    from src.core.config import load_config, save_config
    _cfg = load_config()
    trans_var = ctk.BooleanVar(value=_cfg.get("CHAT_TRANSLATE", "0") == "1")

    def trans_toggle():
        c = load_config()
        c["CHAT_TRANSLATE"] = "1" if trans_var.get() else "0"
        save_config(c)
        self.log(f"🌐  Traducción automática {'activada' if trans_var.get() else 'desactivada'}")

    trans_var.trace_add("write", lambda *_: trans_toggle())

    trans_sw = ctk.CTkSwitch(trans_card, text="  Traducir mensajes y responder en el mismo idioma",
                              variable=trans_var, onvalue=True, offvalue=False,
                              fg_color=CARD2, progress_color=BORD, button_color=PURP,
                              font=("Segoe UI", 11))
    trans_sw.pack(anchor="w", padx=14, pady=(0, 4))
    lb(trans_card, "Detecta el idioma, muestra traducción y responde en el idioma original del usuario.",
       sz=9, col=MUT).pack(anchor="w", padx=14, pady=(0, 8))

    # ── Stats card ──
    stats_card = mk(tab)
    stats_card.pack(fill="x", padx=14, pady=(0, 12))
    lb(stats_card, "📊  Estadísticas", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    def refresh_stats():
        qc = quote_count()
        stats_label.configure(text=f"Quotes guardados: {qc}")

    stats_label = lb(stats_card, "", sz=10, col=TXT)
    stats_label.pack(anchor="w", padx=14, pady=(0, 8))
    refresh_stats()

    return tab
