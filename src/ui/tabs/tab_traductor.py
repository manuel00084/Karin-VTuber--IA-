"""Traductor Tab — extracted from main.py."""
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T, RED, RED_T_LIGHT as RED_T, BLU, BLU_T,
    AMB, AMB_T, TXT, TXT_DIM as MUT, LOGBG,
)
from src.ui.widgets import mk, lb, cb


def build_tab_traductor(parent, app, frame=None):
    """Build the Traductor tab (formerly _tab_traductor)."""
    self = app
    from src.core.config import load_config
    self.config = load_config()
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    # ── Configuración de OCR ──
    ocr_card = mk(tab, accent=True)
    ocr_card.pack(fill="x", padx=14, pady=(12, 6))
    lb(ocr_card, "❓❓  OCR", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(ocr_card, "Motor de reconocimiento de texto en pantalla", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    ocr_grid = ctk.CTkFrame(ocr_card, fg_color="transparent")
    ocr_grid.pack(fill="x", padx=14, pady=(0, 10))
    ocr_grid.grid_columnconfigure(1, weight=1)
    ocr_grid.grid_columnconfigure(3, weight=1)

    lb(ocr_grid, "Motor:", sz=11, col=TXT).grid(row=0, column=0, sticky="w", pady=3)
    self.translator_ocr_engine = cb(ocr_grid, ["RapidOCR", "Windows OCR", "Tesseract"])
    self.translator_ocr_engine.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)
    self.translator_ocr_engine.set(self.config.get("TRANSLATOR_OCR", "RapidOCR"))

    lb(ocr_grid, "Intervalo (seg):", sz=11, col=TXT).grid(row=0, column=2, sticky="w", pady=3)
    self.translator_interval = ctk.CTkEntry(ocr_grid, font=("Consolas", 11), width=80,
                                            fg_color=CARD, text_color=TXT, border_color=BORD)
    self.translator_interval.grid(row=0, column=3, sticky="w", padx=(8, 0), pady=3)
    self.translator_interval.insert(0, str(self.config.get("TRANSLATOR_INTERVAL", 3)))

    # ── Traducción ──
    trans_card = mk(tab, accent=True)
    trans_card.pack(fill="x", padx=14, pady=(6, 6))
    lb(trans_card, "\U0001f310  Traducción", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(trans_card, "Proveedor y configuración de idiomas", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    trans_grid = ctk.CTkFrame(trans_card, fg_color="transparent")
    trans_grid.pack(fill="x", padx=14, pady=(0, 10))
    trans_grid.grid_columnconfigure(1, weight=1)
    trans_grid.grid_columnconfigure(3, weight=1)

    lb(trans_grid, "Proveedor:", sz=11, col=TXT).grid(row=0, column=0, sticky="w", pady=3)
    self.translator_provider = cb(trans_grid, ["Google Web (gratuito)", "Google Gemini", "DeepL", "Dummy (debug)"])
    self.translator_provider.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)
    self.translator_provider.set(self.config.get("TRANSLATOR_PROVIDER", "Google Web (gratuito)"))

    lb(trans_grid, "Idioma origen:", sz=11, col=TXT).grid(row=0, column=2, sticky="w", pady=3)
    self.translator_src_lang = cb(trans_grid, ["auto", "en", "ja", "ko", "zh", "es", "fr", "de", "it", "pt", "ru"])
    self.translator_src_lang.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=3)
    self.translator_src_lang.set(self.config.get("TRANSLATOR_SRC_LANG", "auto"))

    lb(trans_grid, "Idioma destino:", sz=11, col=TXT).grid(row=1, column=0, sticky="w", pady=3)
    self.translator_tgt_lang = cb(trans_grid, ["es", "en", "ja", "ko", "zh", "fr", "de", "it", "pt", "ru"])
    self.translator_tgt_lang.grid(row=1, column=1, sticky="ew", padx=(8, 12), pady=3)
    self.translator_tgt_lang.set(self.config.get("TRANSLATOR_TGT_LANG", "es"))

    lb(trans_grid, "Voz TTS:", sz=11, col=TXT).grid(row=1, column=2, sticky="w", pady=3)
    self.translator_voice = cb(trans_grid, self.voices_all)
    self.translator_voice.grid(row=1, column=3, sticky="ew", padx=(8, 0), pady=3)
    self.translator_voice.set(self.config.get("TRANSLATOR_VOICE", "es-MX-DaliaNeural"))

    # ── Preprocesamiento de imagen ──
    prep_card = mk(tab, accent=True)
    prep_card.pack(fill="x", padx=14, pady=(6, 6))
    lb(prep_card, "❓❓  Preprocesamiento de imagen", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(prep_card, "Filtros para mejorar la detección de texto en el juego", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    prep_grid = ctk.CTkFrame(prep_card, fg_color="transparent")
    prep_grid.pack(fill="x", padx=14, pady=(0, 10))
    prep_grid.grid_columnconfigure(1, weight=1)
    prep_grid.grid_columnconfigure(3, weight=1)

    lb(prep_grid, "Zoom:", sz=11, col=TXT).grid(row=0, column=0, sticky="w", pady=3)
    self.translator_zoom = cb(prep_grid, ["1.0x", "1.5x", "2.0x", "3.0x", "4.0x"])
    self.translator_zoom.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)
    self.translator_zoom.set(self.config.get("TRANSLATOR_ZOOM", "1.0x"))

    lb(prep_grid, "Umbral (threshold):", sz=11, col=TXT).grid(row=0, column=2, sticky="w", pady=3)
    self.translator_threshold = cb(prep_grid, ["0 (off)", "50", "100", "127", "150", "200"])
    self.translator_threshold.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=3)
    self.translator_threshold.set(self.config.get("TRANSLATOR_THRESHOLD", "0 (off)"))

    lb(prep_grid, "Erosión:", sz=11, col=TXT).grid(row=1, column=0, sticky="w", pady=3)
    self.translator_erode = ctk.CTkSwitch(prep_grid, text="", fg_color=CARD2, progress_color=BORD,
                                          button_color=PURP)
    self.translator_erode.grid(row=1, column=1, sticky="w", padx=(8, 12), pady=3)
    if self.config.get("TRANSLATOR_ERODE", "0") == "1":
        self.translator_erode.select()

    # ── Overlay ──
    overlay_card = mk(tab, accent=True)
    overlay_card.pack(fill="x", padx=14, pady=(6, 6))
    lb(overlay_card, "❓❓  Overlay de traducción", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(overlay_card, "Ventana flotante que muestra la traducción sobre el juego", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    overlay_grid = ctk.CTkFrame(overlay_card, fg_color="transparent")
    overlay_grid.pack(fill="x", padx=14, pady=(0, 10))
    overlay_grid.grid_columnconfigure(1, weight=1)
    overlay_grid.grid_columnconfigure(3, weight=1)

    lb(overlay_grid, "Mostrar overlay:", sz=11, col=TXT).grid(row=0, column=0, sticky="w", pady=3)
    self.translator_show_overlay = ctk.CTkSwitch(overlay_grid, text="", fg_color=CARD2, progress_color=BORD,
                                                  button_color=PURP)
    self.translator_show_overlay.grid(row=0, column=1, sticky="w", padx=(8, 12), pady=3)
    if self.config.get("TRANSLATOR_SHOW_OVERLAY", "0") == "1":
        self.translator_show_overlay.select()

    lb(overlay_grid, "Hablar traducción:", sz=11, col=TXT).grid(row=0, column=2, sticky="w", pady=3)
    self.translator_speak = ctk.CTkSwitch(overlay_grid, text="", fg_color=CARD2, progress_color=BORD,
                                          button_color=PURP)
    self.translator_speak.grid(row=0, column=3, sticky="w", padx=(8, 0), pady=3)
    if self.config.get("TRANSLATOR_SPEAK", "0") == "1":
        self.translator_speak.select()

    lb(overlay_grid, "Opacidad:", sz=11, col=TXT).grid(row=1, column=0, sticky="w", pady=3)
    self.translator_opacity = cb(overlay_grid, ["0.3", "0.5", "0.7", "0.8", "0.9", "1.0"])
    self.translator_opacity.grid(row=1, column=1, sticky="ew", padx=(8, 12), pady=3)
    self.translator_opacity.set(self.config.get("TRANSLATOR_OPACITY", "0.8"))

    lb(overlay_grid, "Tamaño fuente:", sz=11, col=TXT).grid(row=1, column=2, sticky="w", pady=3)
    self.translator_font_size = cb(overlay_grid, ["12", "14", "16", "18", "20", "24", "28", "32"])
    self.translator_font_size.grid(row=1, column=3, sticky="ew", padx=(8, 0), pady=3)
    self.translator_font_size.set(self.config.get("TRANSLATOR_FONT_SIZE", "16"))

    # ── Botones de control ──
    ctrl_card = mk(tab)
    ctrl_card.pack(fill="x", padx=14, pady=(6, 6))
    ctrl_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
    ctrl_row.pack(fill="x", padx=14, pady=10)
    ctrl_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

    self.translator_btn = ctk.CTkButton(ctrl_row, text="❓  Iniciar", fg_color=GRN, text_color=GRN_T,
        font=("Segoe UI", 12, "bold"), corner_radius=10, height=36,
        command=self._iniciar_traductor)
    self.translator_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

    ctk.CTkButton(ctrl_row, text="❓  Detener", fg_color=RED, text_color=RED_T,
        font=("Segoe UI", 12, "bold"), corner_radius=10, height=36,
        command=self._detener_traductor).grid(row=0, column=1, padx=(4, 4), sticky="ew")

    ctk.CTkButton(ctrl_row, text="\U0001f9ea  Test OCR", fg_color=BLU, text_color=BLU_T,
        font=("Segoe UI", 11), corner_radius=10, height=36,
        command=self._test_traductor_ocr).grid(row=0, column=2, padx=(4, 4), sticky="ew")

    ctk.CTkButton(ctrl_row, text="❓❓  Test Overlay", fg_color=AMB, text_color=AMB_T,
        font=("Segoe UI", 11), corner_radius=10, height=36,
        command=self._test_traductor_overlay).grid(row=0, column=3, padx=(4, 4), sticky="ew")

    ctk.CTkButton(ctrl_row, text="❓❓  Guardar", fg_color=PURP, text_color="#f3e8ff",
        font=("Segoe UI", 11), corner_radius=10, height=36,
        command=self._guardar_traductor).grid(row=0, column=4, padx=(4, 0), sticky="ew")

    # ── Log ──
    log_card = mk(tab)
    log_card.pack(fill="both", expand=True, padx=14, pady=(6, 12))
    lb(log_card, "\U0001f4cb  Log del Traductor", sz=10, bold=True, col=MUT).pack(anchor="w", padx=10, pady=(6, 2))
    self.traductor_log = ctk.CTkTextbox(log_card, fg_color=LOGBG, text_color=TXT,
                                        font=("Consolas", 10), height=200)
    self.traductor_log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

    return tab
