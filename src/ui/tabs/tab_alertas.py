"""Alertas Tab — Twitch event alert overlay configuration."""
import os
import customtkinter as ctk

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T, RED, RED_T_LIGHT as RED_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb


def build_tab_alertas(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    from src.core.config import load_config
    config = load_config()

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🎯  Alertas del Stream", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Muestra notificaciones animadas en pantalla cuando alguien sigue, se suscribe o dona",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    opts = mk(c)
    opts.pack(fill="x", padx=14, pady=(0, 10))

    grid = ctk.CTkFrame(opts, fg_color="transparent")
    grid.pack(fill="x", padx=14, pady=(10, 4))
    grid.grid_columnconfigure(1, weight=1)
    grid.grid_columnconfigure(3, weight=1)

    row = 0
    lb(grid, "Duración (seg):", sz=11, col=TXT).grid(row=row, column=0, sticky="w", pady=3)
    self.alert_duration = ctk.CTkEntry(grid, font=("Consolas", 11), width=80,
                                        fg_color=CARD, text_color=TXT, border_color=BORD)
    self.alert_duration.grid(row=row, column=1, sticky="w", padx=(8, 12), pady=3)
    self.alert_duration.insert(0, str(config.get("ALERT_DURATION", 6)))

    lb(grid, "Opacidad:", sz=11, col=TXT).grid(row=row, column=2, sticky="w", pady=3)
    self.alert_opacity = ctk.CTkEntry(grid, font=("Consolas", 11), width=80,
                                       fg_color=CARD, text_color=TXT, border_color=BORD)
    self.alert_opacity.grid(row=row, column=3, sticky="w", padx=(8, 0), pady=3)
    self.alert_opacity.insert(0, str(config.get("ALERT_OPACITY", 0.9)))

    row += 1
    lb(grid, "Intervalo (seg):", sz=11, col=TXT).grid(row=row, column=0, sticky="w", pady=3)
    self.alert_interval = ctk.CTkEntry(grid, font=("Consolas", 11), width=80,
                                        fg_color=CARD, text_color=TXT, border_color=BORD)
    self.alert_interval.grid(row=row, column=1, sticky="w", padx=(8, 12), pady=3)
    self.alert_interval.insert(0, str(config.get("ALERT_INTERVAL", 15)))

    sw_card = mk(c)
    sw_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(sw_card, "🔧  Eventos activos", sz=11, bold=True, col=PURP).pack(anchor="w", padx=12, pady=(8, 4))

    def _make_switch(parent, text, cfg_key, default="1"):
        var = ctk.BooleanVar(value=config.get(cfg_key, default) == "1")
        sw = ctk.CTkSwitch(parent, text=text, variable=var, onvalue=True, offvalue=False,
                            fg_color=CARD2, progress_color=BORD, button_color=PURP,
                            font=("Segoe UI", 11))
        sw.pack(anchor="w", padx=12, pady=2)

        def _on_toggle(*_a):
            from src.core.config import load_config as _lc, save_config
            c = _lc()
            c[cfg_key] = "1" if var.get() else "0"
            save_config(c)

        var.trace_add("write", _on_toggle)
        return var

    self.sw_alert_follows = _make_switch(sw_card, "⭐  Follows", "ALERT_POLL_FOLLOWS", "1")
    self.sw_alert_subs = _make_switch(sw_card, "🌟  Suscripciones", "ALERT_POLL_SUBS", "0")
    self.sw_alert_sound = _make_switch(sw_card, "🔊  Sonido de alerta", "ALERT_SOUND", "1")

    lb(sw_card, "💡  Nota: Los follows usan la API de Twitch.", sz=9, col=MUT).pack(anchor="w", padx=12, pady=(2, 6))
    lb(sw_card, "     Suscripciones requieren scope adicional.", sz=9, col=MUT).pack(anchor="w", padx=12, pady=(0, 6))

    btns = ctk.CTkFrame(c, fg_color="transparent")
    btns.pack(fill="x", padx=14, pady=(0, 10))
    btns.grid_columnconfigure((0, 1, 2), weight=1)

    if hasattr(self, 'alert_engine'):
        def toggle_alerts():
            if self.alert_engine._running:
                self.alert_engine.stop()
                toggle_btn.configure(text="▶  Iniciar Alertas", fg_color=GRN)
            else:
                self.alert_engine.start()
                toggle_btn.configure(text="🟢  Activo", fg_color=RED)

        toggle_btn = ctk.CTkButton(btns, text="🟢  Activo" if self.alert_engine._running else "▶  Iniciar Alertas",
                                    fg_color=RED if self.alert_engine._running else GRN,
                                    text_color=GRN_T, font=("Segoe UI", 12, "bold"),
                                    corner_radius=10, height=36, command=toggle_alerts)
        toggle_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkButton(btns, text="🧪  Probar Follow", fg_color=CARD2, text_color=TXT,
                       font=("Segoe UI", 11), corner_radius=10, height=36,
                       command=lambda: self.alert_engine.test_alert("follow", "NuevoViewer")
                       ).grid(row=0, column=1, padx=(4, 4), sticky="ew")

        ctk.CTkButton(btns, text="🧪  Probar Sub", fg_color=CARD2, text_color=TXT,
                       font=("Segoe UI", 11), corner_radius=10, height=36,
                       command=lambda: self.alert_engine.test_alert("sub", "Suscriptor")
                       ).grid(row=0, column=2, padx=(4, 0), sticky="ew")

    # ── Sonidos personalizados ──
    sound_card = mk(tab)
    sound_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(sound_card, "🔊  Sonidos personalizados", sz=11, bold=True, col=PURP).pack(anchor="w", padx=12, pady=(8, 4))

    sound_events = [
        ("follow", "⭐  Follow"),
        ("sub", "🌟  Sub / Resub"),
        ("bit", "💎  Bits"),
        ("raid", "⚔️  Raid"),
        ("donation", "❤️  Donación"),
    ]

    sound_entries = {}
    sound_frame = ctk.CTkFrame(sound_card, fg_color="transparent")
    sound_frame.pack(fill="x", padx=12, pady=(0, 10))
    sound_frame.grid_columnconfigure(1, weight=1)

    for idx, (ev_key, ev_label) in enumerate(sound_events):
        cfg_key = f"ALERT_SOUND_{ev_key.upper()}"
        lb(sound_frame, ev_label, sz=10, col=MUT).grid(row=idx, column=0, sticky="w", pady=2)

        entry = ctk.CTkEntry(sound_frame, font=("Consolas", 10), fg_color=CARD,
                              text_color=TXT, border_color=BORD)
        current = config.get(cfg_key, "")
        if current:
            entry.insert(0, current)
        entry.grid(row=idx, column=1, sticky="ew", padx=(8, 4), pady=2)
        sound_entries[ev_key] = entry

        def browse_sound(ev=ev_key, ent=entry):
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                title=f"Seleccionar sonido para {ev}",
                filetypes=[("Archivos de audio", "*.wav *.mp3 *.ogg"), ("Todos", "*.*")]
            )
            if path:
                ent.delete(0, "end")
                ent.insert(0, path)

        ctk.CTkButton(sound_frame, text="📁", fg_color=CARD2, text_color=TXT,
                       height=24, corner_radius=6, width=32,
                       command=browse_sound
                       ).grid(row=idx, column=2, padx=(0, 0), pady=2)

        def test_sound(ev=ev_key):
            path = sound_entries[ev].get().strip()
            if path and os.path.exists(path):
                try:
                    import winsound
                    winsound.PlaySound(path, winsound.SND_ASYNC)
                    self.log(f"🔊  Probando sonido: {os.path.basename(path)}")
                except Exception as e:
                    self.log(f"❌  Error al reproducir: {e}")
            else:
                self.log("❌  Archivo no encontrado")

        ctk.CTkButton(sound_frame, text="▶", fg_color="#1e3a5f", text_color="#93c5fd",
                       height=24, corner_radius=6, width=28,
                       command=test_sound
                       ).grid(row=idx, column=3, padx=(2, 0), pady=2)

    def guardar_alertas():
        from src.core.config import load_config as _lc, save_config
        c = _lc()
        try:
            c["ALERT_DURATION"] = str(int(self.alert_duration.get().strip() or 6))
        except ValueError:
            c["ALERT_DURATION"] = "6"
        try:
            c["ALERT_OPACITY"] = str(float(self.alert_opacity.get().strip() or 0.9))
        except ValueError:
            c["ALERT_OPACITY"] = "0.9"
        try:
            c["ALERT_INTERVAL"] = str(int(self.alert_interval.get().strip() or 15))
        except ValueError:
            c["ALERT_INTERVAL"] = "15"
        # Guardar rutas de sonido
        for ev_key, entry in sound_entries.items():
            cfg_key = f"ALERT_SOUND_{ev_key.upper()}"
            val = entry.get().strip()
            if val:
                c[cfg_key] = val
            else:
                c.pop(cfg_key, None)
        save_config(c)
        if hasattr(self, 'alert_engine'):
            self.alert_engine._load_config()
        self.log("✅  Configuración de alertas guardada")

    guardar_row = ctk.CTkFrame(tab, fg_color="transparent")
    guardar_row.pack(fill="x", padx=14, pady=(0, 12))
    ctk.CTkButton(guardar_row, text="💾  Guardar Configuración", fg_color=GRN, text_color=GRN_T,
                   font=("Segoe UI", 11), corner_radius=10, height=34,
                   command=guardar_alertas).pack(side="left")

    log_card = mk(tab)
    log_card.pack(fill="both", expand=True, padx=14, pady=(0, 12))
    lb(log_card, "📋  Log de Alertas", sz=10, bold=True, col=MUT).pack(anchor="w", padx=10, pady=(6, 2))
    self.alertas_log = ctk.CTkTextbox(log_card, fg_color="#080812", text_color=TXT,
                                       font=("Consolas", 10), height=120)
    self.alertas_log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

    def log_alertas(msg):
        if hasattr(self, 'alertas_log'):
            self.alertas_log.insert("end", f"{msg}\n")
            self.alertas_log.see("end")

    if not hasattr(self, '_alertas_log_fn'):
        self._alertas_log_fn = log_alertas

    return tab
