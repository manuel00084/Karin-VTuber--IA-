"""Perfil Streamer Tab — Player / Streamer profile."""
import customtkinter as ctk
import os
from tkinter import filedialog

from src import PROJECT_ROOT
from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, cb


def build_tab_perfil_streamer(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    from src.core.config import load_config as _lc
    pcfg = _lc()

    pf2 = mk(tab, accent=True)
    pf2.pack(fill="x", padx=14, pady=(12, 6))
    lb(pf2, "🎮  Perfil del Streamer / Player", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(pf2, "Datos del compañero — la IA usará esta información para interactuar contigo", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    pg = ctk.CTkFrame(pf2, fg_color="transparent")
    pg.pack(fill="x", padx=14, pady=(0, 10))
    pg.grid_columnconfigure(1, weight=1)
    pg.grid_columnconfigure(3, weight=1)

    field_defs = [
        ("Nombre:", 0, 0, "_player_nombre", "PLAYER_NOMBRE"),
        ("Apellido:", 0, 2, "_player_apellido", "PLAYER_APELLIDO"),
        ("Edad:", 1, 0, "_player_edad", "PLAYER_EDAD"),
        ("Género:", 1, 2, "_player_genero", "PLAYER_GENERO"),
        ("Cumpleaños:", 2, 0, "_player_cumple", "PLAYER_CUMPLE"),
        ("Signo Zodiacal:", 2, 2, "_player_signo", "PLAYER_SIGNO"),
        ("Altura:", 3, 0, "_player_altura", "PLAYER_ALTURA"),
        ("Trabajo:", 3, 2, "_player_trabajo", "PLAYER_TRABAJO"),
        ("Relación:", 6, 0, "_player_relacion", "PLAYER_RELACION"),
    ]
    for label, row, col, attr, cfg_key in field_defs:
        lb(pg, label, sz=11, col=TXT, width=65 if col == 0 else 80).grid(row=row, column=col, padx=(0, 4), pady=3, sticky="w")
        setattr(self, attr, ctk.StringVar(value=pcfg.get(cfg_key, "")))
        if cfg_key == "PLAYER_RELACION":
            opciones = ["", "SIMP", "Compañeros", "Amig@", "Novi@", "Amante",
                        "Espos@", "Waifu", "Sirvienta/Mayordomo", "Esclava/o Sexual", "Fan tóxico"]
            c = cb(pg, opciones, variable=getattr(self, attr), width=180)
            c.grid(row=row, column=col + 1, columnspan=3, padx=(0, 4), pady=3, sticky="w")
        else:
            ctk.CTkEntry(pg, textvariable=getattr(self, attr), font=("Consolas", 11),
                         fg_color=CARD, text_color=TXT, border_color=BORD).grid(
                row=row, column=col + 1, padx=(0, 12) if col == 0 else (0, 4), pady=3, sticky="ew")

    lb(pg, "Gustos:", sz=11, col=TXT, width=65).grid(row=4, column=0, padx=(0, 4), pady=3, sticky="w")
    self._player_gustos = ctk.StringVar(value=pcfg.get("PLAYER_GUSTOS", ""))
    ctk.CTkEntry(pg, textvariable=self._player_gustos, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=4, column=1, columnspan=3, padx=(0, 4), pady=3, sticky="ew")

    lb(pg, "Frases típicas:", sz=11, col=TXT, width=65).grid(row=5, column=0, padx=(0, 4), pady=3, sticky="w")
    self._player_frases = ctk.StringVar(value=pcfg.get("PLAYER_FRASES", ""))
    ctk.CTkEntry(pg, textvariable=self._player_frases, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=5, column=1, columnspan=3, padx=(0, 4), pady=3, sticky="ew")

    _campos_player = [
        ("PLAYER_NOMBRE", self._player_nombre), ("PLAYER_APELLIDO", self._player_apellido),
        ("PLAYER_EDAD", self._player_edad), ("PLAYER_GENERO", self._player_genero),
        ("PLAYER_CUMPLE", self._player_cumple), ("PLAYER_SIGNO", self._player_signo),
        ("PLAYER_ALTURA", self._player_altura), ("PLAYER_TRABAJO", self._player_trabajo),
        ("PLAYER_GUSTOS", self._player_gustos), ("PLAYER_FRASES", self._player_frases),
        ("PLAYER_RELACION", self._player_relacion),
    ]

    def _guardar_txt_player():
        path = filedialog.asksaveasfilename(
            initialdir=os.path.join(PROJECT_ROOT, "Perfil"),
            defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for k, v in _campos_player:
                    f.write(f"{k}={v.get()}\n")
        except Exception as e:
            self.log(f"Error guardando Perfil Streamer: {e}", "error")

    def _cargar_txt_player():
        path = filedialog.askopenfilename(
            initialdir=os.path.join(PROJECT_ROOT, "Perfil"),
            defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    for ck, cv in _campos_player:
                        if ck == k:
                            cv.set(v)
                            break
        except Exception as e:
            self.log(f"Error cargando Perfil Streamer: {e}", "error")

    btn_txt_row = ctk.CTkFrame(pf2, fg_color="transparent")
    btn_txt_row.pack(fill="x", padx=14, pady=(6, 2))
    ctk.CTkButton(btn_txt_row, text="📂 Cargar Perfil .txt",
                  fg_color=CARD2, text_color=TXT,
                  hover_color=PURP, height=28, corner_radius=8,
                  command=_cargar_txt_player).pack(side="left", padx=(0, 6))
    ctk.CTkButton(btn_txt_row, text="💾 Guardar Perfil .txt",
                  fg_color=GRN, text_color=GRN_T,
                  height=28, corner_radius=8,
                  command=_guardar_txt_player).pack(side="left")

    btn_row2 = ctk.CTkFrame(pf2, fg_color="transparent")
    btn_row2.pack(fill="x", padx=14, pady=(4, 12))
    ctk.CTkButton(btn_row2, text="💾 Guardar Perfil del Streamer",
                  fg_color=GRN, text_color=GRN_T,
                  height=28, corner_radius=8,
                  command=self._guardar_config_panel).pack(side="left")

    return tab
