"""Voice Commands Tab — wake word 'Karin' + voice control."""
import customtkinter as ctk
from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, GRN, GRN_T, RED, RED_T_LIGHT as RED_T, TXT, TXT_DIM as MUT
from src.ui.widgets import mk, lb
from src.audio.voice_commands import VoiceCommandEngine, build_command_handler
from src.core.config import load_config, save_config

COMMAND_LIST = [
    ("🎬  Escenas", ['cambia escena [nombre]', 'pon escena [nombre]']),
    ("📹  Grabación", ['inicia grabación', 'para la grabación']),
    ("📡  Stream", ['inicia stream', 'termina stream']),
    ("🎮  Juegos", ['abre [juego]', 'cierra [juego]']),
    ("🔊  Audio", ['silencio', 'volumen a 50']),
    ("⏰  Otros", ['qué hora es']),
]


def build_tab_voice_commands(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(
        parent, fg_color=BG, corner_radius=0,
        scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD,
    )

    if not hasattr(app, "_voice_engine"):
        handler = build_command_handler(app)
        app._voice_engine = VoiceCommandEngine(app=app, on_command=handler)

    engine = app._voice_engine
    cfg = load_config()
    current_ww = cfg.get("VOICE_WAKE_WORD", "")

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🎤  Comandos de Voz", sz=13, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Configurá una palabra de activación y controlá la app con la voz",
       sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    toggle_card = mk(tab)
    toggle_card.pack(fill="x", padx=14, pady=(0, 6))

    def toggle():
        word = ww_entry.get().strip()
        if not word:
            app.log("❌  Configurá una palabra de activación primero")
            return
        if engine._running:
            engine.stop()
            toggle_btn.configure(text="🎤  Iniciar comandos de voz", fg_color=GRN)
            status_lb.configure(text="❌  Apagado", text_color=RED_T)
            app.log("⏹  Comandos de voz desactivados")
        else:
            engine.start()
            toggle_btn.configure(text="⏹  Detener comandos de voz", fg_color=RED)
            status_lb.configure(text="✅  Escuchando...", text_color=GRN_T)
            app.log(f"🎤  Comandos de voz activados — decí '{word.capitalize()}' + comando")

    toggle_btn = ctk.CTkButton(toggle_card, text="🎤  Iniciar comandos de voz", fg_color=GRN,
                                text_color="#fff", font=("Segoe UI", 12, "bold"),
                                height=40, corner_radius=10, command=toggle)
    toggle_btn.pack(fill="x", padx=14, pady=(8, 2))

    status_lb = lb(toggle_card, "❌  Apagado", sz=10, col=RED_T, bold=True)
    status_lb.pack(anchor="w", padx=18, pady=(0, 8))

    # ── Wake word config ──
    ww_card = mk(tab)
    ww_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(ww_card, "🔊  Palabra de activación", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    wwf = ctk.CTkFrame(ww_card, fg_color="transparent")
    wwf.pack(fill="x", padx=14, pady=(0, 10))
    wwf.grid_columnconfigure(1, weight=1)

    lb(wwf, "Decí esto antes del comando:", sz=10, col=MUT).grid(row=0, column=0, sticky="w", pady=3)
    ww_entry = ctk.CTkEntry(wwf, font=("Consolas", 12), fg_color=CARD, text_color=TXT, border_color=BORD,
                             placeholder_text="ej: bot, asistente, computadora")
    if current_ww:
        ww_entry.insert(0, current_ww)
    ww_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)

    def save_ww():
        word = ww_entry.get().strip().lower()
        if not word:
            app.log("❌  Ingresa una palabra")
            return
        c = load_config()
        c["VOICE_WAKE_WORD"] = word
        save_config(c)
        engine.reload_wake_word()
        rebuild_cmds(word.capitalize())
        app.log(f"✅  Wake word cambiada a: {word}")

    ctk.CTkButton(wwf, text="💾  Guardar", fg_color=GRN, text_color=GRN_T,
                   height=28, corner_radius=8, command=save_ww
                   ).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))

    # ── Comandos disponibles ──
    cmds_card = mk(tab)
    cmds_card.pack(fill="x", padx=14, pady=(0, 6))
    cmds_header = lb(cmds_card, "📋  Comandos disponibles", sz=11, bold=True, col=PURP)
    cmds_header.pack(anchor="w", padx=14, pady=(8, 4))

    cmd_labels = []

    def rebuild_cmds(wake_label):
        for w in cmd_labels:
            w.destroy()
        cmd_labels.clear()
        if not wake_label:
            lbl = lb(cmds_card, "Configurá una palabra de activación arriba para ver los comandos disponibles.", sz=10, col=MUT)
            lbl.pack(anchor="w", padx=18, pady=4)
            cmd_labels.append(lbl)
            return
        for category, cmds in COMMAND_LIST:
            lb(cmds_card, category, sz=10, bold=True, col=MUT).pack(anchor="w", padx=18, pady=(4, 0))
            for text in cmds:
                lbl = lb(cmds_card, f'  "{wake_label}, {text}"', sz=10, col=TXT)
                lbl.pack(anchor="w", padx=28, pady=1)
                cmd_labels.append(lbl)
            if category != COMMAND_LIST[-1][0]:
                sep = ctk.CTkFrame(cmds_card, height=1, fg_color="#2a2a3e")
                sep.pack(fill="x", padx=18, pady=4)
                cmd_labels.append(sep)

    rebuild_cmds(current_ww.capitalize() if current_ww else "")

    # ── Info ──
    info_card = mk(tab)
    info_card.pack(fill="x", padx=14, pady=(0, 12))
    lb(info_card, "ℹ️  Requisitos", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))
    for line in [
        "Modelo Vosk español: vosk-model-small-es-0.42",
        "Descargalo de: https://alphacephei.com/vosk/models",
        "y extraelo en la raíz del proyecto.",
        "Si no está instalado, los comandos de voz no funcionarán.",
    ]:
        lb(info_card, line, sz=10, col=MUT).pack(anchor="w", padx=14, pady=0)

    return tab
