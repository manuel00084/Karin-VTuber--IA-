"""Game Control Tab — launch and close games from the app."""
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T, RED, RED_T_LIGHT as RED_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb
from src.utils.game_launcher import get_games, add_game, remove_game, open_game, close_game, is_running, list_games, scan_games


def build_tab_game_control(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🎮  Control de Juegos", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Abre y cierra juegos desde la app, por voz o por comando de Twitch",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    add_card = mk(tab)
    add_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(add_card, "➕  Agregar juego", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    ag = ctk.CTkFrame(add_card, fg_color="transparent")
    ag.pack(fill="x", padx=14, pady=(0, 10))
    ag.grid_columnconfigure(1, weight=1)
    ag.grid_columnconfigure(3, weight=1)

    lb(ag, "Nombre:", sz=11, col=TXT).grid(row=0, column=0, sticky="w", pady=3)
    add_name = ctk.CTkEntry(ag, font=("Consolas", 11), fg_color=CARD, text_color=TXT, border_color=BORD)
    add_name.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)

    lb(ag, "Ruta .exe:", sz=11, col=TXT).grid(row=1, column=0, sticky="w", pady=3)
    add_path = ctk.CTkEntry(ag, font=("Consolas", 10), fg_color=CARD, text_color=TXT, border_color=BORD)
    add_path.grid(row=1, column=1, sticky="ew", padx=(8, 12), pady=3)

    def browse_exe():
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Seleccionar juego", filetypes=[("Ejecutables", "*.exe"), ("Todos", "*.*")])
        if path:
            add_path.delete(0, "end")
            add_path.insert(0, path)

    ctk.CTkButton(ag, text="📁  Examinar", fg_color=CARD2, text_color=TXT,
                   height=28, corner_radius=8, command=browse_exe
                   ).grid(row=1, column=2, padx=(0, 4), pady=3, sticky="w")

    lb(ag, "Argumentos:", sz=11, col=TXT).grid(row=2, column=0, sticky="w", pady=3)
    add_args = ctk.CTkEntry(ag, font=("Consolas", 10), fg_color=CARD, text_color=TXT, border_color=BORD,
                             placeholder_text="opcional: -windowed -novid")
    add_args.grid(row=2, column=1, sticky="ew", padx=(8, 12), pady=3)

    def do_add():
        name = add_name.get().strip()
        path = add_path.get().strip()
        if not name or not path:
            self.log("❌  Ingresa nombre y ruta del juego")
            return
        add_game(name, path, add_args.get().strip())
        add_name.delete(0, "end")
        add_path.delete(0, "end")
        add_args.delete(0, "end")
        refresh_list()
        self.log(f"✅  Juego agregado: {name}")

    def do_scan():
        self.log("🔍  Escaneando juegos instalados...")
        self.after(100, _scan_worker)

    def _scan_worker():
        try:
            found = scan_games()
            existing = {g["name"].lower() for g in get_games()}
            count = 0
            for g in found:
                if g["name"].lower() not in existing:
                    add_game(g["name"], g["exe_path"], g.get("args", ""))
                    count += 1
            refresh_list()
            self.log(f"✅  Escaneo completo. {count} juegos nuevos agregados.")
        except Exception as e:
            self.log(f"❌  Error en escaneo: {e}")
            import traceback
            traceback.print_exc()

    bfs = ctk.CTkFrame(ag, fg_color="transparent")
    bfs.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
    ctk.CTkButton(bfs, text="💾  Agregar juego", fg_color=GRN, text_color=GRN_T,
                   height=30, corner_radius=8, command=do_add
                   ).pack(side="left", padx=(0, 8))
    ctk.CTkButton(bfs, text="🔍  Escanear juegos", fg_color="#2563eb", text_color="#bfdbfe",
                   height=30, corner_radius=8, command=do_scan
                   ).pack(side="left")

    list_card = mk(tab)
    list_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(list_card, "📋  Mis juegos", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    games_container = ctk.CTkFrame(list_card, fg_color="transparent")
    games_container.pack(fill="x", padx=14, pady=(0, 6))

    def refresh_list():
        for w in games_container.winfo_children():
            w.destroy()
        games = get_games()
        if not games:
            lb(games_container, "No hay juegos configurados. Agrega uno arriba.", sz=10, col=MUT).pack(pady=10)
            return
        for g in games:
            row = ctk.CTkFrame(games_container, fg_color=CARD2)
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=1)

            running = is_running(g["name"])
            status = "🟢" if running else "⚫"
            name_label = lb(row, f"{status}  {g['name']}", sz=11, bold=True, col=TXT)
            name_label.grid(row=0, column=0, sticky="w", padx=10, pady=6)

            bf = ctk.CTkFrame(row, fg_color="transparent")
            bf.grid(row=0, column=1, sticky="e", padx=6, pady=4)

            if running:
                ctk.CTkButton(bf, text="⏹  Cerrar", fg_color=RED, text_color=RED_T,
                               height=26, corner_radius=6,
                               command=lambda n=g["name"]: do_close(n)
                               ).pack(side="left", padx=2)
            else:
                ctk.CTkButton(bf, text="▶  Abrir", fg_color=GRN, text_color=GRN_T,
                               height=26, corner_radius=6,
                               command=lambda n=g["name"]: do_open(n)
                               ).pack(side="left", padx=2)

            ctk.CTkButton(bf, text="🗑", fg_color="#7f1d1d", text_color=RED_T,
                           height=26, corner_radius=6, width=32,
                           command=lambda n=g["name"]: do_remove(n)
                           ).pack(side="left", padx=2)

    def do_open(name):
        result = open_game(name)
        self.log(result)
        self.after(1000, refresh_list)

    def do_close(name):
        result = close_game(name)
        self.log(result)
        self.after(500, refresh_list)

    def do_remove(name):
        remove_game(name)
        refresh_list()
        self.log(f"🗑  Juego eliminado: {name}")

    refresh_list()

    info_card = mk(tab)
    info_card.pack(fill="x", padx=14, pady=(0, 12))
    lb(info_card, "💡  Comandos disponibles", sz=11, bold=True, col=PURP).pack(anchor="w", padx=12, pady=(8, 4))
    cmds_text = [
        "Por voz (PTT):  \"Abre Minecraft\"  /  \"Cierra Minecraft\"",
        "Por Twitch:  !abre Minecraft  /  !cierra Minecraft",
        "Los juegos deben estar agregados en la lista de arriba.",
    ]
    for t in cmds_text:
        lb(info_card, t, sz=10, col=MUT).pack(anchor="w", padx=14, pady=1)

    return tab
