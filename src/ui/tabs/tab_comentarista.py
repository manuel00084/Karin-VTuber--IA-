"""Comentarista Tab — AI chat for Twitch with automatic game commentator."""
import customtkinter as ctk
import threading, webbrowser, requests, json, traceback

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T, RED, RED_T_LIGHT as RED_T, BLU, BLU_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, cb


def build_tab_comentarista(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    from src.core.config import load_config as _lc
    config = _lc()

    ia_card = mk(tab, accent=True)
    ia_card.pack(fill="x", padx=14, pady=(12, 6))
    lb(ia_card, "🤖  IA para Chat de Twitch", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(ia_card, "Los viewers escriben el comando en el chat y la IA responde con voz", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    ia_grid = ctk.CTkFrame(ia_card, fg_color="transparent")
    ia_grid.pack(fill="x", padx=14, pady=(4, 10))
    ia_grid.grid_columnconfigure(1, weight=1)

    lb(ia_grid, "Comando:", sz=11, col=MUT).grid(row=0, column=0, sticky="w")
    self.ia_cmd_entry = ctk.CTkEntry(ia_grid, placeholder_text="!IA",
                                        font=("Consolas", 12, "bold"),
                                        fg_color=CARD, text_color=TXT, border_color=BORD, width=100)
    self.ia_cmd_entry.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=3)
    ia_cmd_val = config.get("BOT_IA_COMMAND", "!IA")
    self.ia_cmd_entry.insert(0, ia_cmd_val)

    lb(ia_grid, "IA para Comentarista:", sz=11, col=MUT).grid(row=1, column=0, sticky="w")
    self.comentador_ia_provider = cb(ia_grid, ["Groq", "Cerebras", "Google Studio IA", "Local AI"])
    self.comentador_ia_provider.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=3)
    ia_provider_val = config.get("COMENTADOR_IA_PROVIDER", "Groq")
    self.comentador_ia_provider.set(ia_provider_val)

    lb(ia_grid, "Voz TTS:", sz=11, col=MUT).grid(row=2, column=0, sticky="w", pady=(6, 0))
    voz_row = ctk.CTkFrame(ia_grid, fg_color="transparent")
    voz_row.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
    voz_row.grid_columnconfigure(0, weight=1)
    self.ia_voice_menu = cb(voz_row, self.voices_all)
    self.ia_voice_menu.grid(row=0, column=0, sticky="ew")
    self.ia_voice_menu.set(config.get("BOT_IA_VOICE", "es-MX-DaliaNeural"))

    def test_ia_voice():
        voz = self.ia_voice_menu.get()
        from src.core.config import load_config
        cfg = load_config()
        ia_dev = int(cfg.get("IA_DEVICE", 2))
        from src.audio import speak
        vol = float(config.get("VOLUME", "2.0"))
        speak("Hola, soy tu asistente de voz. Esta es una prueba.", voz, ia_dev, volume=vol)

    ctk.CTkButton(voz_row, text="🔊 Test", fg_color=CARD2, text_color=TXT,
                  hover_color=PURP, height=28, corner_radius=6,
                  command=test_ia_voice).grid(row=0, column=1, padx=(6, 0))

    def guardar_ia_command():
        cmd = self.ia_cmd_entry.get().strip()
        voz = self.ia_voice_menu.get()
        provider = self.comentador_ia_provider.get()
        if not cmd:
            self.log("❌  Ingresa un comando válido")
            return
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["BOT_IA_COMMAND"] = cmd
        cfg["BOT_IA_VOICE"] = voz
        cfg["COMENTADOR_IA_PROVIDER"] = provider
        save_config(cfg)
        self.log(f"✅  Comando IA guardado: {cmd} → voz: {voz} | Proveedor: {provider}")

    ctk.CTkButton(ia_grid, text="💾 Guardar comando IA", fg_color=GRN, text_color=GRN_T,
                   height=30, corner_radius=8, hover_color="#10b981",
                   command=guardar_ia_command).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(10, 0))

    ctk.CTkFrame(tab, height=6, fg_color="transparent").pack(fill="x", padx=14, pady=(6, 0))

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(8, 6))
    lb(c, "🎮  Asistente IA", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))

    opts = mk(c)
    opts.pack(fill="x", padx=14, pady=(0, 10))

    grid = ctk.CTkFrame(opts, fg_color="transparent")
    grid.pack(fill="x", padx=14, pady=(10, 4))
    grid.grid_columnconfigure(1, weight=1)

    lb(grid, "🎮 Juego:", sz=11, col=MUT).grid(row=0, column=0, sticky="w", pady=3)
    game_row = ctk.CTkFrame(grid, fg_color="transparent")
    game_row.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)
    game_row.grid_columnconfigure(0, weight=1)
    juego_inicial = config.get("COMENTARISTA_JUEGO", "")
    self.juego_entry = ctk.CTkEntry(game_row, placeholder_text="ej: Minecraft",
                                     font=("Segoe UI", 12, "bold"),
                                     fg_color=CARD, text_color=TXT, border_color=BORD)
    self.juego_entry.grid(row=0, column=0, sticky="ew")
    if juego_inicial:
        self.juego_entry.insert(0, juego_inicial)

        def detectar_juego_twitch():
            from src.core.config import load_config
            cfg_d = load_config()
            tok = cfg_d.get("TWITCH_TOKEN", "")
            chan = cfg_d.get("CHANNEL", "")
            if not tok or not chan:
                log_comentarista("⚠  No hay sesión de Twitch activa")
                return
            log_comentarista("🔍  Detectando juego desde Twitch...")
            from src.core.oauth_server import fetch_twitch_game
            def _fetch():
                juego = fetch_twitch_game(tok, chan)
                if juego:
                    self.juego_entry.delete(0, "end")
                    self.juego_entry.insert(0, juego)
                    log_comentarista(f"✅  Juego detectado: {juego}")
                else:
                    log_comentarista("❌  No se pudo detectar el juego")
            threading.Thread(target=_fetch, daemon=True).start()

    detect_btn = ctk.CTkButton(game_row, text="🎮", fg_color=CARD2, text_color=TXT,
                                hover_color=PURP, width=32, height=28, corner_radius=6,
                                command=detectar_juego_twitch)
    detect_btn.grid(row=0, column=1, padx=(6, 0))

    lb(grid, "⏱ Intervalo (seg):", sz=11, col=MUT).grid(row=1, column=0, sticky="w", pady=3)
    irow = ctk.CTkFrame(grid, fg_color="transparent")
    irow.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=3)
    self.comentarista_intervalo = ctk.CTkEntry(irow, placeholder_text="30",
                                                   fg_color=CARD, text_color=TXT, border_color=BORD,
                                                   font=("Segoe UI", 11), width=80)
    self.comentarista_intervalo.pack(side="left")
    self.comentarista_intervalo.insert(0, str(config.get("COMENTARISTA_INTERVALO", 30)))

    lb(grid, "🔥 Cooldown (seg):", sz=11, col=MUT).grid(row=2, column=0, sticky="w", pady=3)
    cdown_row = ctk.CTkFrame(grid, fg_color="transparent")
    cdown_row.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=3)
    self.comentarista_cooldown = ctk.CTkEntry(cdown_row, placeholder_text="30",
                                               fg_color=CARD, text_color=TXT, border_color=BORD,
                                               font=("Segoe UI", 11), width=80)
    self.comentarista_cooldown.pack(side="left")
    self.comentarista_cooldown.insert(0, str(config.get("COMENTARISTA_COOLDOWN", 30)))

    sw_card = mk(c)
    sw_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(sw_card, "🔧  Módulos activos", sz=11, bold=True, col=PURP).pack(anchor="w", padx=12, pady=(8, 4))

    def _obtener_key_por_modo(modo, cfg):
        if "Google Vision" in modo:
            key = cfg.get("GOOGLE_STUDIO_API_KEY", "")
            return key, "google_studio"
        if "Groq Vision" in modo:
            key = cfg.get("GROQ_API_KEY", "")
            return key, "groq"
        ia_provider = self.comentador_ia_provider.get().lower().replace(" ", "_")
        mapa = {"google_studio_ia": "google_studio", "groq": "groq", "cerebras": "cerebras", "local_ai": "local"}
        ia_provider = mapa.get(ia_provider, "groq")
        cfg_key = {"google_studio": "GOOGLE_STUDIO_API_KEY", "cerebras": "CEREBRAS_API_KEY", "local": "LOCAL_AI_API_KEY"}.get(ia_provider, "GROQ_API_KEY")
        key = cfg.get(cfg_key, "")
        return key, ia_provider

    def reiniciar_comentarista():
        if self.game_watcher is None:
            return
        try:
            partes = []
            if hasattr(self, 'sw_ocr') and self.sw_ocr.get():
                partes.append("OCR")
            if hasattr(self, 'sw_karin_vision') and self.sw_karin_vision.get():
                partes.append("CLIP Vision")
            if hasattr(self, 'sw_groq_vision') and self.sw_groq_vision.get():
                partes.append("Groq Vision")
            if hasattr(self, 'sw_google_vision') and self.sw_google_vision.get():
                partes.append("Google Vision")
            if hasattr(self, 'sw_karin_animadora') and self.sw_karin_animadora.get():
                partes.append("Karin Animadora")
            modo = " + ".join(partes) if partes else "OCR"
            self.log(f"🔄  Reiniciando comentarista: {modo}")
            old = self.game_watcher
            old.detener()
            juego = self.juego_entry.get().strip()
            voz = self.ia_voice_menu.get()
            try:
                cooldown = int(self.comentarista_cooldown.get().strip() or 30)
            except ValueError:
                cooldown = 30
            from src.core.config import load_config
            cfg = load_config()
            ia_key, ia_provider = _obtener_key_por_modo(modo, cfg)
            if not ia_key:
                self.log("❌  No hay API Key para reiniciar")
                self.game_watcher = None
                return
            from src.utils.game_watcher import GameWatcher
            self.game_watcher = GameWatcher(
                speak_fn=lambda *a, **kw: None,
                stop_audio_fn=lambda: None,
                get_devices_fn=lambda: self.get_devices(),
                log_fn=log_comentarista
            )
            from src.audio import speak, stop_audio
            self.game_watcher = GameWatcher(
                speak_fn=speak,
                stop_audio_fn=stop_audio,
                get_devices_fn=lambda: self.get_devices(),
                log_fn=log_comentarista
            )
            self.game_watcher.iniciar(voz=voz, juego=juego, modo=modo, ia_key=ia_key, ia_provider=ia_provider, cooldown=cooldown)
        except Exception as ex:
            self.log(f"⚠ Error al reiniciar comentarista: {ex}")
            import traceback
            self.log(traceback.format_exc())
            self.game_watcher = None

    def _crear_switch(parent, texto, attr_switch, attr_indicador, default=True, badge=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=2)
        row.grid_columnconfigure(1, weight=1)
        var = ctk.BooleanVar(value=config.get(attr_switch.upper(), "1") == "1")
        sw = ctk.CTkSwitch(row, text=texto, variable=var, onvalue=True, offvalue=False,
                            fg_color=CARD2, progress_color=BORD, button_color=PURP,
                            font=("Segoe UI", 11))
        sw.grid(row=0, column=0, sticky="w")
        if badge:
            lb(row, badge, sz=8, col="#f59e0b").grid(row=0, column=1, sticky="w", padx=(4, 0))
        ind = lb(row, "●", sz=14, col=GRN_T if var.get() else RED_T)
        ind.grid(row=0, column=2, sticky="e", padx=(0, 4))
        def _on_toggle(*_a):
            try:
                ind.configure(text_color=GRN_T if var.get() else RED_T)
                from src.core.config import load_config, save_config
                cfg = load_config()
                cfg[attr_switch.upper()] = "1" if var.get() else "0"
                save_config(cfg)
                reiniciar_comentarista()
            except Exception as ex:
                self.log(f"⚠ Error al cambiar {attr_switch}: {ex}")
                self.log(traceback.format_exc())
        var.trace_add("write", _on_toggle)
        setattr(self, attr_switch, var)
        setattr(self, attr_indicador, ind)

    sw_inner = ctk.CTkFrame(sw_card, fg_color="transparent")
    sw_inner.pack(fill="x", padx=0, pady=(0, 6))
    sw_inner.grid_columnconfigure((0, 1), weight=1)

    col1 = ctk.CTkFrame(sw_inner, fg_color="transparent")
    col1.grid(row=0, column=0, sticky="ew", padx=(0, 4))
    col2 = ctk.CTkFrame(sw_inner, fg_color="transparent")
    col2.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    _crear_switch(col1, "📖 OCR", "sw_ocr", "ind_ocr")
    _crear_switch(col1, "👁️ CLIP Vision", "sw_karin_vision", "ind_karin_vision", badge="MobileCLIP-S2")
    _crear_switch(col2, "🎭 Karin Animadora", "sw_karin_animadora", "ind_karin_animadora")
    _crear_switch(col2, "🟢 Groq Vision", "sw_groq_vision", "ind_groq_vision")
    _crear_switch(col2, "🔵 Google Vision", "sw_google_vision", "ind_google_vision")

    learn_card = mk(c)
    learn_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(learn_card, "🧠  Aprendizaje y Memoria", sz=11, bold=True, col=PURP).pack(anchor="w", padx=12, pady=(8, 4))

    learn_inner = ctk.CTkFrame(learn_card, fg_color="transparent")
    learn_inner.pack(fill="x", padx=12, pady=(0, 6))
    learn_inner.grid_columnconfigure((0, 1, 2), weight=1)

    var_vm = ctk.BooleanVar(value=config.get("SW_VECTOR_MEMORY", "1") == "1")
    self.sw_vector_memory = ctk.CTkSwitch(learn_inner, text="💾 Memoria Vectorial", variable=var_vm,
                                           onvalue=True, offvalue=False,
                                           fg_color=CARD2, progress_color=BORD, button_color=PURP,
                                           font=("Segoe UI", 11))
    self.sw_vector_memory.grid(row=0, column=0, sticky="w", pady=2)

    var_cl = ctk.BooleanVar(value=config.get("SW_CHAT_LEARNING", "1") == "1")
    self.sw_chat_learning = ctk.CTkSwitch(learn_inner, text="📈 Aprendizaje del Chat", variable=var_cl,
                                           onvalue=True, offvalue=False,
                                           fg_color=CARD2, progress_color=BORD, button_color=PURP,
                                           font=("Segoe UI", 11))
    self.sw_chat_learning.grid(row=0, column=1, sticky="w", pady=2)

    learn_btns = ctk.CTkFrame(learn_card, fg_color="transparent")
    learn_btns.pack(fill="x", padx=12, pady=(0, 8))
    learn_btns.grid_columnconfigure((0, 1, 2), weight=1)

    ctk.CTkButton(learn_btns, text="📊 Stats", fg_color=CARD2, text_color=TXT,
                   font=("Segoe UI", 10), corner_radius=8, height=28,
                   command=self._mostrar_learning_stats).grid(row=0, column=0, padx=(0, 3), sticky="ew")
    ctk.CTkButton(learn_btns, text="🗑 Borrar Aprendizaje", fg_color="#7f1d1d", text_color=RED_T,
                   font=("Segoe UI", 10), corner_radius=8, height=28,
                   command=self._borrar_chat_learning).grid(row=0, column=1, padx=3, sticky="ew")
    ctk.CTkButton(learn_btns, text="🗑 Borrar Memoria Vectorial", fg_color="#7f1d1d", text_color=RED_T,
                   font=("Segoe UI", 10), corner_radius=8, height=28,
                   command=self._borrar_vector_memory).grid(row=0, column=2, padx=(3, 0), sticky="ew")

    idle_card = mk(c)
    idle_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(idle_card, "🗣  Voz Espontánea (habla cuando hay silencio)", sz=11, bold=True, col=PURP).pack(anchor="w", padx=12, pady=(8, 4))

    idle_inner = ctk.CTkFrame(idle_card, fg_color="transparent")
    idle_inner.pack(fill="x", padx=12, pady=(0, 4))
    idle_inner.grid_columnconfigure((0, 1, 2), weight=1)

    var_idle = ctk.BooleanVar(value=config.get("SW_IDLE_MODE", "1") == "1")
    self.sw_idle_mode = ctk.CTkSwitch(idle_inner, text="🗣 Activar Voz Espontánea", variable=var_idle,
                                        onvalue=True, offvalue=False,
                                        fg_color=CARD2, progress_color=BORD, button_color=PURP,
                                        font=("Segoe UI", 11))
    self.sw_idle_mode.grid(row=0, column=0, sticky="w", pady=2)

    var_idle_int = ctk.BooleanVar(value=config.get("SW_IDLE_INTERRUPT", "1") == "1")
    self.sw_idle_interrupt = ctk.CTkSwitch(idle_inner, text="⏹ Interrumpir al recibir mensaje", variable=var_idle_int,
                                             onvalue=True, offvalue=False,
                                             fg_color=CARD2, progress_color=BORD, button_color=PURP,
                                             font=("Segoe UI", 10))
    self.sw_idle_interrupt.grid(row=0, column=1, sticky="w", pady=2)

    idle_row2 = ctk.CTkFrame(idle_card, fg_color="transparent")
    idle_row2.pack(fill="x", padx=12, pady=(0, 4))
    idle_row2.grid_columnconfigure((0, 1, 2), weight=1)

    lb(idle_row2, "Silencio mínimo (s):", sz=10, col=TXT).grid(row=0, column=0, sticky="w", pady=2)
    self.idle_interval_entry = ctk.CTkEntry(idle_row2, placeholder_text="60",
                                               fg_color=CARD, text_color=TXT, border_color=BORD,
                                               font=("Segoe UI", 11), width=70)
    self.idle_interval_entry.grid(row=0, column=1, sticky="w", padx=(4, 12), pady=2)
    self.idle_interval_entry.insert(0, str(config.get("IDLE_INTERVAL", 60)))

    var_idle_ai = ctk.BooleanVar(value=config.get("SW_IDLE_AI", "0") == "1")
    self.sw_idle_ai = ctk.CTkSwitch(idle_row2, text="🤖 IA generativa", variable=var_idle_ai,
                                     onvalue=True, offvalue=False,
                                     fg_color=CARD2, progress_color=BORD, button_color=PURP,
                                     font=("Segoe UI", 10))
    self.sw_idle_ai.grid(row=0, column=2, sticky="w", padx=(8, 0), pady=2)

    def _obtener_key_por_modo_actual(modo, cfg_val):
        return _obtener_key_por_modo(modo, cfg_val)

    def iniciar_comentarista():
        partes = []
        if hasattr(self, 'sw_ocr') and self.sw_ocr.get():
            partes.append("OCR")
        if hasattr(self, 'sw_karin_vision') and self.sw_karin_vision.get():
            partes.append("CLIP Vision")
        if hasattr(self, 'sw_groq_vision') and self.sw_groq_vision.get():
            partes.append("Groq Vision")
        if hasattr(self, 'sw_google_vision') and self.sw_google_vision.get():
            partes.append("Google Vision")
        if hasattr(self, 'sw_karin_animadora') and self.sw_karin_animadora.get():
            partes.append("Karin Animadora")
        modo = " + ".join(partes) if partes else "OCR"
        juego = self.juego_entry.get().strip()
        voz = self.ia_voice_menu.get()
        try:
            cooldown = int(self.comentarista_cooldown.get().strip() or 30)
        except ValueError:
            cooldown = 30
            self.log("⚠  Cooldown inválido, usando 30 seg")

        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["COMENTARISTA_JUEGO"] = juego
        cfg["COMENTARISTA_VOICE"] = voz
        cfg["COMENTARISTA_MODO"] = modo
        cfg["COMENTARISTA_COOLDOWN"] = cooldown
        save_config(cfg)

        ia_key, ia_provider = _obtener_key_por_modo(modo, cfg)
        if not ia_key:
            self.log(f"❌  Se necesita API Key para el modo {modo}")
            return
        self.log(f" IA disponible ({ia_provider})")

        if self.game_watcher:
            self.game_watcher.detener()

        from src.utils.game_watcher import GameWatcher
        from src.audio import speak, stop_audio
        self.game_watcher = GameWatcher(
            speak_fn=speak,
            stop_audio_fn=stop_audio,
            get_devices_fn=lambda: self.get_devices(),
            log_fn=log_comentarista
        )
        self.game_watcher.iniciar(voz=voz, juego=juego, modo=modo, ia_key=ia_key, ia_provider=ia_provider, cooldown=cooldown)
        self.log(f" Comentarista iniciado ({modo})")

    def detener_comentarista():
        if self.game_watcher:
            self.game_watcher.detener()
            self.game_watcher = None
        self.log("⏹ Comentarista detenido")

    def guardar_config_comentarista():
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["COMENTARISTA_JUEGO"] = self.juego_entry.get().strip()
        cfg["COMENTARISTA_INTERVALO"] = int(self.comentarista_intervalo.get().strip() or 30)
        cfg["COMENTARISTA_MODO"] = "OCR"
        cfg["COMENTADOR_IA_PROVIDER"] = self.comentador_ia_provider.get()
        for key, attr in [("SW_OCR", "sw_ocr"), ("SW_KARIN_VISION", "sw_karin_vision"),
                          ("SW_KARIN_ANIMADORA", "sw_karin_animadora"), ("SW_VISION_IA", "sw_vision_ia")]:
            if hasattr(self, attr):
                cfg[key] = "1" if getattr(self, attr).get() else "0"
        cfg["SW_IDLE_MODE"] = "1" if self.sw_idle_mode.get() else "0"
        cfg["SW_IDLE_INTERRUPT"] = "1" if self.sw_idle_interrupt.get() else "0"
        cfg["SW_IDLE_AI"] = "1" if self.sw_idle_ai.get() else "0"
        cfg["IDLE_INTERVAL"] = int(self.idle_interval_entry.get().strip() or 60)
        cfg.pop("SUBTITULOS_INTERVALO", None)
        cfg.pop("PLAYER_MODO", None)
        cfg.pop("PLAYER_INPUT", None)
        cfg.pop("PLAYER_JUEGO", None)
        save_config(cfg)
        self.log("✅ Configuración del comentarista guardada")

    btns = ctk.CTkFrame(c, fg_color="transparent")
    btns.pack(fill="x", padx=14, pady=(0, 10))
    btns.grid_columnconfigure((0, 1, 2), weight=1)

    self.comentarista_btn = ctk.CTkButton(btns, text="▶ Iniciar", fg_color=GRN, text_color=GRN_T,
        font=("Segoe UI", 12, "bold"), corner_radius=10, height=36,
        command=iniciar_comentarista)
    self.comentarista_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

    ctk.CTkButton(btns, text="⏹ Detener", fg_color=RED, text_color=RED_T,
        font=("Segoe UI", 12, "bold"), corner_radius=10, height=36,
        command=detener_comentarista).grid(row=0, column=1, padx=(4, 4), sticky="ew")

    ctk.CTkButton(btns, text="💾 Guardar", fg_color=BLU, text_color=BLU_T,
        font=("Segoe UI", 11), corner_radius=10, height=36,
        command=guardar_config_comentarista).grid(row=0, column=2, padx=(4, 0), sticky="ew")

    # Log
    log_card = mk(tab)
    log_card.pack(fill="both", expand=True, padx=14, pady=(8, 12))
    lb(log_card, "📋  Log del Comentarista", sz=10, bold=True, col=MUT).pack(anchor="w", padx=10, pady=(6, 2))
    self.comentarista_log = ctk.CTkTextbox(log_card, fg_color="#080812", text_color=TXT,
                                            font=("Consolas", 10), height=150)
    self.comentarista_log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

    def log_comentarista(msg):
        if hasattr(self, 'comentarista_log'):
            self.comentarista_log.insert("end", f"{msg}\n")
            self.comentarista_log.see("end")

    return tab
