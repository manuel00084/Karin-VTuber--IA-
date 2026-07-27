"""Perfil IA Tab — IA profile form and personality selector."""
import customtkinter as ctk
import os
from tkinter import filedialog

from src import PROJECT_ROOT
from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T, RED, RED_T_LIGHT as RED_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, cb, bt


def build_tab_perfil_ia(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    from src.core.config import load_config as _lc
    config = _lc()

    pf = mk(tab, accent=True)
    pf.pack(fill="x", padx=14, pady=(12, 6))
    lb(pf, "🤖  Perfil de la IA", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(pf, "Prompt principal — los datos del perfil se anteponen a la personalidad", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    pf_grid = ctk.CTkFrame(pf, fg_color="transparent")
    pf_grid.pack(fill="x", padx=14)
    pf_grid.grid_columnconfigure(1, weight=1)
    pf_grid.grid_columnconfigure(3, weight=1)

    self._ia_nombre = ctk.StringVar(value=config.get("IA_NOMBRE", ""))
    lb(pf_grid, "Nombre:", sz=11, col=TXT, width=65).grid(row=0, column=0, padx=(0, 4), pady=3, sticky="w")
    ctk.CTkEntry(pf_grid, textvariable=self._ia_nombre, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=0, column=1, padx=(0, 12), pady=3, sticky="ew")
    lb(pf_grid, "Apellido:", sz=11, col=TXT, width=65).grid(row=0, column=2, padx=(0, 4), pady=3, sticky="w")
    self._ia_apellido = ctk.StringVar(value=config.get("IA_APELLIDO", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_apellido, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=0, column=3, padx=(0, 4), pady=3, sticky="ew")

    lb(pf_grid, "Edad:", sz=11, col=TXT, width=65).grid(row=1, column=0, padx=(0, 4), pady=3, sticky="w")
    self._ia_edad = ctk.StringVar(value=config.get("IA_EDAD", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_edad, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=1, column=1, padx=(0, 12), pady=3, sticky="ew")
    lb(pf_grid, "Género:", sz=11, col=TXT, width=65).grid(row=1, column=2, padx=(0, 4), pady=3, sticky="w")
    self._ia_genero = ctk.StringVar(value=config.get("IA_GENERO", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_genero, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=1, column=3, padx=(0, 4), pady=3, sticky="ew")

    lb(pf_grid, "Cumpleaños:", sz=11, col=TXT, width=80).grid(row=2, column=0, padx=(0, 4), pady=3, sticky="w")
    self._ia_cumple = ctk.StringVar(value=config.get("IA_CUMPLE", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_cumple, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=2, column=1, padx=(0, 12), pady=3, sticky="ew")
    lb(pf_grid, "Signo Zodiacal:", sz=11, col=TXT, width=100).grid(row=2, column=2, padx=(0, 4), pady=3, sticky="w")
    self._ia_signo = ctk.StringVar(value=config.get("IA_SIGNO", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_signo, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=2, column=3, padx=(0, 4), pady=3, sticky="ew")

    lb(pf_grid, "Altura:", sz=11, col=TXT, width=65).grid(row=3, column=0, padx=(0, 4), pady=3, sticky="w")
    self._ia_altura = ctk.StringVar(value=config.get("IA_ALTURA", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_altura, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=3, column=1, padx=(0, 12), pady=3, sticky="ew")
    lb(pf_grid, "Trabajo:", sz=11, col=TXT, width=65).grid(row=3, column=2, padx=(0, 4), pady=3, sticky="w")
    self._ia_trabajo = ctk.StringVar(value=config.get("IA_TRABAJO", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_trabajo, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=3, column=3, padx=(0, 4), pady=3, sticky="ew")

    lb(pf_grid, "Gustos:", sz=11, col=TXT, width=65).grid(row=4, column=0, padx=(0, 4), pady=3, sticky="w")
    self._ia_gustos = ctk.StringVar(value=config.get("IA_GUSTOS", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_gustos, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=4, column=1, columnspan=3, padx=(0, 4), pady=3, sticky="ew")

    lb(pf_grid, "Frases típicas:", sz=11, col=TXT, width=65).grid(row=5, column=0, padx=(0, 4), pady=3, sticky="w")
    self._ia_frases = ctk.StringVar(value=config.get("IA_FRASES", ""))
    ctk.CTkEntry(pf_grid, textvariable=self._ia_frases, font=("Consolas", 11),
                 fg_color=CARD, text_color=TXT, border_color=BORD).grid(row=5, column=1, columnspan=3, padx=(0, 4), pady=3, sticky="ew")

    _campos_ia = [
        ("IA_NOMBRE", self._ia_nombre), ("IA_APELLIDO", self._ia_apellido),
        ("IA_EDAD", self._ia_edad), ("IA_GENERO", self._ia_genero),
        ("IA_CUMPLE", self._ia_cumple), ("IA_SIGNO", self._ia_signo),
        ("IA_ALTURA", self._ia_altura), ("IA_TRABAJO", self._ia_trabajo),
        ("IA_GUSTOS", self._ia_gustos), ("IA_FRASES", self._ia_frases),
    ]

    def _guardar_txt_ia():
        path = filedialog.asksaveasfilename(
            initialdir=os.path.join(PROJECT_ROOT, "Perfil"),
            defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for k, v in _campos_ia:
                    f.write(f"{k}={v.get()}\n")
        except Exception as e:
            self.log(f"Error guardando Perfil IA: {e}", "error")

    def _cargar_txt_ia():
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
                    for ck, cv in _campos_ia:
                        if ck == k:
                            cv.set(v)
                            break
        except Exception as e:
            self.log(f"Error cargando Perfil IA: {e}", "error")

    btn_txt_row = ctk.CTkFrame(pf, fg_color="transparent")
    btn_txt_row.pack(fill="x", padx=14, pady=(6, 2))
    ctk.CTkButton(btn_txt_row, text="📂 Cargar Perfil .txt",
                  fg_color=CARD2, text_color=TXT,
                  hover_color=PURP, height=28, corner_radius=8,
                  command=_cargar_txt_ia).pack(side="left", padx=(0, 6))
    ctk.CTkButton(btn_txt_row, text="💾 Guardar Perfil .txt",
                  fg_color=GRN, text_color=GRN_T,
                  height=28, corner_radius=8,
                  command=_guardar_txt_ia).pack(side="left")

    sep = ctk.CTkFrame(pf, height=1, fg_color="#2a2a3e")
    sep.pack(fill="x", padx=14, pady=(10, 6))
    lb_row = ctk.CTkFrame(pf, fg_color="transparent")
    lb_row.pack(fill="x", padx=14)
    lb(lb_row, "🧠  Personalidad", sz=11, bold=True, col=PURP).pack(side="left")
    lb(lb_row, "Prompt activo", sz=10, col=MUT).pack(side="left", padx=(12, 0))
    self.mode_select = cb(pf, self.prompt_files, command=self.change_mode)
    self.mode_select.pack(fill="x", padx=14, pady=(4, 0))
    initial_prompt = config.get("SELECTED_PROMPT", self.prompt_files[0])
    if initial_prompt not in self.prompt_files:
        initial_prompt = self.prompt_files[0]
    self.mode_select.set(initial_prompt)

    btn_row = ctk.CTkFrame(pf, fg_color="transparent")
    btn_row.pack(fill="x", padx=14, pady=(6, 10))
    ctk.CTkButton(btn_row, text="+ Nueva Personalidad",
                  fg_color=CARD2, text_color=TXT,
                  hover_color=PURP, height=28, corner_radius=8,
                  command=self._crear_nuevo_prompt).pack(side="left", padx=(0, 6))
    ctk.CTkButton(btn_row, text="💾 Guardar Perfil",
                  fg_color=GRN, text_color=GRN_T,
                  height=28, corner_radius=8,
                  command=self._guardar_config_panel).pack(side="left")

    return tab
