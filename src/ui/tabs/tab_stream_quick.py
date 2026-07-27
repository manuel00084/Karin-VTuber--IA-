"""Stream Quick Actions — clip, marker, set title/game, stream status."""
import threading
import customtkinter as ctk
from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, GRN, GRN_T, RED, RED_T_LIGHT as RED_T, BLU, BLU_T, AMB as YLW, TXT, TXT_DIM as MUT
from src.ui.widgets import mk, lb
from src.utils.twitch_api import (
    create_clip, create_marker, get_stream_info,
    set_stream_info, search_games,
)


def build_tab_stream_quick(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(
        parent, fg_color=BG, corner_radius=0,
        scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
    )

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🎬  Acciones Rápidas del Stream", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Clip, marcador, info del stream y más", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    # ── Status card ──
    status_card = mk(tab)
    status_card.pack(fill="x", padx=14, pady=(0, 6))

    status_title = lb(status_card, "📡  Estado del Stream", sz=11, bold=True, col=PURP)
    status_title.pack(anchor="w", padx=14, pady=(8, 4))

    status_frame = ctk.CTkFrame(status_card, fg_color="transparent")
    status_frame.pack(fill="x", padx=14, pady=(0, 10))
    status_frame.grid_columnconfigure(1, weight=1)

    lb(status_frame, "Título:", sz=10, col=MUT).grid(row=0, column=0, sticky="w", pady=2)
    status_title_val = lb(status_frame, "—", sz=10, col=TXT)
    status_title_val.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=2)

    lb(status_frame, "Juego:", sz=10, col=MUT).grid(row=1, column=0, sticky="w", pady=2)
    status_game_val = lb(status_frame, "—", sz=10, col=TXT)
    status_game_val.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=2)

    lb(status_frame, "Espectadores:", sz=10, col=MUT).grid(row=2, column=0, sticky="w", pady=2)
    status_viewers_val = lb(status_frame, "—", sz=10, col=TXT)
    status_viewers_val.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=2)

    def refresh_status():
        info = get_stream_info()
        if info:
            status_title_val.configure(text=info.get("title", "—")[:60])
            status_game_val.configure(text=info.get("game", "—"))
            status_viewers_val.configure(text=str(info.get("viewers", 0)))
        else:
            status_title_val.configure(text="No conectado")
            status_game_val.configure(text="—")
            status_viewers_val.configure(text="—")
        self.after(30000, refresh_status)

    refresh_status()

    # ── Quick Actions ──
    actions_card = mk(tab)
    actions_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(actions_card, "⚡  Acciones", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    actions_grid = ctk.CTkFrame(actions_card, fg_color="transparent")
    actions_grid.pack(fill="x", padx=14, pady=(0, 10))

    def _clip():
        self.log("📹  Creando clip...")
        result = create_clip()
        self.log(result)

    def _marker():
        self.log("📍  Creando marcador...")
        result = create_marker()
        self.log(result)

    ctk.CTkButton(actions_grid, text="📹  Crear Clip", fg_color=BLU, text_color=BLU_T,
                   height=36, corner_radius=8, command=_clip
                   ).pack(side="left", padx=(0, 8))

    ctk.CTkButton(actions_grid, text="📍  Marcador", fg_color=YLW, text_color=YLW_T,
                   height=36, corner_radius=8, command=_marker
                   ).pack(side="left", padx=(0, 8))

    # ── Set Info ──
    info_card = mk(tab)
    info_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(info_card, "✏️  Cambiar Info del Stream", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    ie = ctk.CTkFrame(info_card, fg_color="transparent")
    ie.pack(fill="x", padx=14, pady=(0, 10))
    ie.grid_columnconfigure(1, weight=1)

    lb(ie, "Título:", sz=10, col=MUT).grid(row=0, column=0, sticky="w", pady=3)
    title_entry = ctk.CTkEntry(ie, font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD)
    title_entry.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)

    lb(ie, "Juego:", sz=10, col=MUT).grid(row=1, column=0, sticky="w", pady=3)
    game_entry = ctk.CTkEntry(ie, font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD)
    game_entry.grid(row=1, column=1, sticky="ew", padx=(8, 12), pady=3)

    def do_set_info():
        title = title_entry.get().strip()
        game = game_entry.get().strip()
        if not title and not game:
            self.log("❌  Ingresa al menos título o juego")
            return
        game_id = None
        if game:
            results = search_games(game)
            if results:
                game_id = results[0][0]
            else:
                self.log(f"❌  Juego '{game}' no encontrado en Twitch")
                return
        result = set_stream_info(title=title or None, game_id=game_id)
        self.log(result)
        if "✅" in result:
            self.after(2000, refresh_status)

    ctk.CTkButton(ie, text="💾  Actualizar Info", fg_color=GRN, text_color=GRN_T,
                   height=30, corner_radius=8, command=do_set_info
                   ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

    return tab
