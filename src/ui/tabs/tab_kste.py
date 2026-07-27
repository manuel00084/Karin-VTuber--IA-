"""KSTE Tab — Karin Smart Translator Engine configuration."""
import customtkinter as ctk
from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T, RED, RED_T_LIGHT as RED_T, BLU, BLU_T,
    AMB, AMB_T, TXT, TXT_DIM as MUT, LOGBG,
)
from src.ui.widgets import mk, lb, cb


def build_tab_kste(parent, app):
    self = app
    tab = ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                  scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    if not hasattr(self, 'kste_engine'):
        from src.kste.engine import KSTEEngine
        self.kste_engine = KSTEEngine()
    kste = self.kste_engine

    # ── Capture Region ──
    cap_card = mk(tab, accent=True)
    cap_card.pack(fill="x", padx=14, pady=(12, 6))
    lb(cap_card, "KSTE - Captura de Chat", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(cap_card, "Selecciona el area del chat del juego", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    cap_row = ctk.CTkFrame(cap_card, fg_color="transparent")
    cap_row.pack(fill="x", padx=14, pady=(0, 10))
    cap_row.grid_columnconfigure(1, weight=1)

    self.kste_region_label = lb(cap_row, "Region: No configurada", sz=11, col=TXT)
    self.kste_region_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=3)

    _update_region_label(kste, self.kste_region_label)

    cap_btns = ctk.CTkFrame(cap_card, fg_color="transparent")
    cap_btns.pack(fill="x", padx=14, pady=(0, 10))

    ctk.CTkButton(cap_btns, text="Capturar Area", fg_color=BLU, text_color=BLU_T,
        font=("Segoe UI", 11, "bold"), corner_radius=10, height=32,
        command=lambda: _calibrate(kste, self.kste_region_label)).pack(side="left", padx=(0, 8))

    ctk.CTkButton(cap_btns, text="Limpiar", fg_color=RED, text_color=RED_T,
        font=("Segoe UI", 11), corner_radius=10, height=32,
        command=lambda: _clear_region(kste, self.kste_region_label)).pack(side="left")

    # ── Translation Engine ──
    tr_card = mk(tab, accent=True)
    tr_card.pack(fill="x", padx=14, pady=(6, 6))
    lb(tr_card, "KSTE - Motor de Traduccion", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(tr_card, "Selecciona el motor de traduccion (sin IA, solo reglas)", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    tr_grid = ctk.CTkFrame(tr_card, fg_color="transparent")
    tr_grid.pack(fill="x", padx=14, pady=(0, 10))
    tr_grid.grid_columnconfigure(1, weight=1)

    lb(tr_grid, "Motor:", sz=11, col=TXT).grid(row=0, column=0, sticky="w", pady=3)
    self.kste_translator_cb = cb(tr_grid, ["google", "deepl", "argos", "libre", "nllb"])
    self.kste_translator_cb.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)
    self.kste_translator_cb.set(kste.config.translator_name)

    lb(tr_grid, "API Key:", sz=11, col=TXT).grid(row=1, column=0, sticky="w", pady=3)
    self.kste_api_key = ctk.CTkEntry(tr_grid, font=("Consolas", 11),
        fg_color=CARD, text_color=TXT, border_color=BORD, show="*")
    self.kste_api_key.grid(row=1, column=1, sticky="ew", padx=(8, 12), pady=3)
    self.kste_api_key.insert(0, kste.config.translator_api_key)

    lb(tr_grid, "Intervalo (seg):", sz=11, col=TXT).grid(row=2, column=0, sticky="w", pady=3)
    self.kste_interval = ctk.CTkEntry(tr_grid, font=("Consolas", 11), width=80,
        fg_color=CARD, text_color=TXT, border_color=BORD)
    self.kste_interval.grid(row=2, column=1, sticky="w", padx=(8, 12), pady=3)
    self.kste_interval.insert(0, str(kste.config.capture_interval))

    # ── Overlay ──
    ov_card = mk(tab, accent=True)
    ov_card.pack(fill="x", padx=14, pady=(6, 6))
    lb(ov_card, "KSTE - Overlay", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))

    ov_grid = ctk.CTkFrame(ov_card, fg_color="transparent")
    ov_grid.pack(fill="x", padx=14, pady=(0, 10))
    ov_grid.grid_columnconfigure(1, weight=1)
    ov_grid.grid_columnconfigure(3, weight=1)

    lb(ov_grid, "Opacidad:", sz=11, col=TXT).grid(row=0, column=0, sticky="w", pady=3)
    self.kste_opacity = cb(ov_grid, ["0.3", "0.5", "0.7", "0.8", "0.85", "0.9", "1.0"])
    self.kste_opacity.grid(row=0, column=1, sticky="ew", padx=(8, 12), pady=3)
    self.kste_opacity.set(str(kste.config.overlay_opacity))

    lb(ov_grid, "Fuente:", sz=11, col=TXT).grid(row=0, column=2, sticky="w", pady=3)
    self.kste_font_size = cb(ov_grid, ["10", "12", "14", "16", "18", "20"])
    self.kste_font_size.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=3)
    self.kste_font_size.set(str(kste.config.overlay_font_size))

    # ── Filters ──
    fl_card = mk(tab, accent=True)
    fl_card.pack(fill="x", padx=14, pady=(6, 6))
    lb(fl_card, "KSTE - Filtros", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))

    fl_row = ctk.CTkFrame(fl_card, fg_color="transparent")
    fl_row.pack(fill="x", padx=14, pady=(0, 10))

    self.kste_spam_filter = ctk.CTkSwitch(fl_row, text="Filtro de spam",
        font=("Segoe UI", 11), fg_color=CARD2, progress_color=BORD, button_color=PURP)
    self.kste_spam_filter.pack(side="left", padx=(0, 20))
    if kste.config.spam_filter_enabled:
        self.kste_spam_filter.select()

    lb(fl_row, "Min longitud:", sz=11, col=TXT).pack(side="left", padx=(0, 4))
    self.kste_min_len = ctk.CTkEntry(fl_row, font=("Consolas", 11), width=50,
        fg_color=CARD, text_color=TXT, border_color=BORD)
    self.kste_min_len.pack(side="left")
    self.kste_min_len.insert(0, str(kste.config.min_message_length))

    # ── Controls ──
    ctrl_card = mk(tab)
    ctrl_card.pack(fill="x", padx=14, pady=(6, 6))
    ctrl_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
    ctrl_row.pack(fill="x", padx=14, pady=10)
    ctrl_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

    self.kste_start_btn = ctk.CTkButton(ctrl_row, text="Iniciar KSTE", fg_color=GRN, text_color=GRN_T,
        font=("Segoe UI", 12, "bold"), corner_radius=10, height=36,
        command=lambda: _start_kste(kste))
    self.kste_start_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

    ctk.CTkButton(ctrl_row, text="Detener KSTE", fg_color=RED, text_color=RED_T,
        font=("Segoe UI", 12, "bold"), corner_radius=10, height=36,
        command=lambda: _stop_kste(kste)).grid(row=0, column=1, padx=(4, 4), sticky="ew")

    ctk.CTkButton(ctrl_row, text="Overlay", fg_color=BLU, text_color=BLU_T,
        font=("Segoe UI", 11), corner_radius=10, height=36,
        command=lambda: kste.toggle_overlay()).grid(row=0, column=2, padx=(4, 4), sticky="ew")

    ctk.CTkButton(ctrl_row, text="Guardar", fg_color=PURP, text_color="#f3e8ff",
        font=("Segoe UI", 11), corner_radius=10, height=36,
        command=lambda: _save_kste(kste, self)).grid(row=0, column=3, padx=(4, 0), sticky="ew")

    # ── Status ──
    st_card = mk(tab)
    st_card.pack(fill="x", padx=14, pady=(6, 6))
    lb(st_card, "KSTE - Estado", sz=10, bold=True, col=MUT).pack(anchor="w", padx=10, pady=(6, 2))
    self.kste_status_label = lb(st_card, f"Estado: {kste.status}", sz=11, col=TXT)
    self.kste_status_label.pack(anchor="w", padx=10)
    self.kste_stats_label = lb(st_card, "", sz=10, col=MUT)
    self.kste_stats_label.pack(anchor="w", padx=10)
    _update_stats(kste, self.kste_stats_label)

    # ── Log ──
    log_card = mk(tab)
    log_card.pack(fill="both", expand=True, padx=14, pady=(6, 12))
    lb(log_card, "Log del KSTE", sz=10, bold=True, col=MUT).pack(anchor="w", padx=10, pady=(6, 2))
    self.kste_log = ctk.CTkTextbox(log_card, fg_color=LOGBG, text_color=TXT,
                                    font=("Consolas", 10), height=200)
    self.kste_log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

    return tab


def _update_region_label(kste, label):
    region = kste.capture.get_region()
    if region:
        label.configure(text=f"Region: x={region[0]}, y={region[1]}, w={region[2]}, h={region[3]}")
    else:
        label.configure(text="Region: No configurada")


def _calibrate(kste, label):
    result = kste.calibrate_capture()
    _update_region_label(kste, label)


def _clear_region(kste, label):
    kste.capture.clear_region()
    _update_region_label(kste, label)


def _start_kste(kste):
    kste.start()


def _stop_kste(kste):
    kste.stop()


def _save_kste(kste, app_ctx):
    try:
        kste.config.translator_name = app_ctx.kste_translator_cb.get()
        kste.config.translator_api_key = app_ctx.kste_api_key.get()
        try:
            kste.config.capture_interval = float(app_ctx.kste_interval.get())
        except ValueError:
            pass
        try:
            kste.config.overlay_opacity = float(app_ctx.kste_opacity.get())
        except ValueError:
            pass
        try:
            kste.config.overlay_font_size = int(app_ctx.kste_font_size.get())
        except ValueError:
            pass
        kste.config.spam_filter_enabled = app_ctx.kste_spam_filter.get() == 1
        try:
            kste.config.min_message_length = int(app_ctx.kste_min_len.get())
        except ValueError:
            pass
        kste.set_translator(kste.config.translator_name, kste.config.translator_api_key)
        from src.kste.config.kste_config import save_kste_config
        save_kste_config(kste.config)
        if hasattr(app_ctx, 'kste_status_label'):
            app_ctx.kste_status_label.configure(text=f"Estado: {kste.status}")
        if hasattr(app_ctx, 'kste_stats_label'):
            _update_stats(kste, app_ctx.kste_stats_label)
    except Exception as e:
        pass


def _update_stats(kste, label):
    stats = kste.stats
    label.configure(
        text=f"Procesados: {stats['processed']} | Traducidos: {stats['translated']} | "
             f"Filtrados: {stats['filtered']} | Cache: {stats['cached']}"
    )
