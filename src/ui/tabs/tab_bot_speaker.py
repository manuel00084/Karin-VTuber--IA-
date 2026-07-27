"""Bot Speaker Tab — Twitch audio commands and custom sounds."""
import customtkinter as ctk
import os

from src.ui.theme import (
    BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD,
    GRN, GRN_T,
    TXT, TXT_DIM as MUT,
)
from src.ui.widgets import mk, lb, ToolTip


def build_tab_bot_speaker(parent, app, frame=None):
    self = app
    tab = frame or ctk.CTkScrollableFrame(parent, fg_color=BG, corner_radius=0,
                                           scrollbar_button_color=PURP, scrollbar_button_hover_color=BORD)

    c = mk(tab, accent=True)
    c.pack(fill="x", padx=14, pady=(12, 6))
    lb(c, "🔧  Bot Speaker", sz=12, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lb(c, "Comandos para reproducir audio en Twitch", sz=10, col=MUT).pack(anchor="w", padx=14, pady=(0, 6))

    self.voices_male = ["es-ES-AlvaroNeural", "es-MX-DarioNeural", "es-AR-TonoNeural"]
    self.voices_female = ["es-ES-ElviraNeural", "es-MX-LiaNeural", "es-MX-DaliaNeural", "es-AR-EmiliaNeural"]

    from src.core.config import load_config as _lc
    config = _lc()
    saved_male = config.get("BOT_VOICE_MALE", "es_MX-DarioNeural")
    saved_female = config.get("BOT_VOICE_FEMALE", "es-MX-DaliaNeural")

    cmd_frame = mk(c)
    cmd_frame.pack(fill="x", padx=14, pady=(0, 10))

    row1 = ctk.CTkFrame(cmd_frame, fg_color="transparent")
    row1.pack(fill="x", padx=14, pady=(10, 4))
    row1.grid_columnconfigure(1, weight=1)
    lb(row1, "!sp comando:", sz=10, col=MUT, width=95).grid(row=0, column=0, sticky="w")
    ToolTip(row1, "Comando que los viewers usan para que Karin lea texto en voz alta con voz masculina.\nEjemplo: !sp Hola Karin")
    self.cmd_speak_entry = ctk.CTkEntry(row1, placeholder_text="!sp",
                                    font=("Consolas", 12),
                                    fg_color=CARD, text_color=TXT, border_color=BORD)
    self.cmd_speak_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
    self.cmd_speak_entry.insert(0, config.get("BOT_SPEAK_CMD", "!sp"))

    lb(row1, "Voz:", sz=10, col=MUT, width=30).grid(row=0, column=2, padx=(8, 4))
    self.voice_male_var = ctk.StringVar(value=saved_male)
    self.voice_male_menu = ctk.CTkOptionMenu(row1, values=self.voices_male,
                                          variable=self.voice_male_var,
                                          fg_color=CARD, button_color=PURP, dropdown_fg_color=CARD2,
                                          text_color=TXT, font=("Segoe UI", 11), width=140)
    self.voice_male_menu.grid(row=0, column=3, padx=(0, 0))

    ctk.CTkFrame(cmd_frame, height=1, fg_color="#2a2a3e").pack(fill="x", padx=14, pady=4)

    row2 = ctk.CTkFrame(cmd_frame, fg_color="transparent")
    row2.pack(fill="x", padx=14, pady=(4, 10))
    row2.grid_columnconfigure(1, weight=1)
    lb(row2, "!spm comando:", sz=10, col=MUT, width=95).grid(row=0, column=0, sticky="w")
    ToolTip(row2, "Comando que los viewers usan para que Karin lea texto en voz alta con voz femenina.\nEjemplo: !spm Hola Karin")
    self.cmd_speakmap_entry = ctk.CTkEntry(row2, placeholder_text="!spm",
                                          font=("Consolas", 12),
                                          fg_color=CARD, text_color=TXT, border_color=BORD)
    self.cmd_speakmap_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
    self.cmd_speakmap_entry.insert(0, config.get("BOT_SPEAKMAP_CMD", "!spm"))

    lb(row2, "Voz:", sz=10, col=MUT, width=30).grid(row=0, column=2, padx=(8, 4))
    self.voice_female_var = ctk.StringVar(value=saved_female)
    self.voice_female_menu = ctk.CTkOptionMenu(row2, values=self.voices_female,
                                                variable=self.voice_female_var,
                                                fg_color=CARD, button_color=PURP, dropdown_fg_color=CARD2,
                                                text_color=TXT, font=("Segoe UI", 11), width=140)
    self.voice_female_menu.grid(row=0, column=3)

    def guardar_bot_cmds():
        cmd = self.cmd_speak_entry.get().strip()
        cmd_map = self.cmd_speakmap_entry.get().strip()
        voice_male = self.voice_male_var.get()
        voice_female = self.voice_female_var.get()
        if not cmd:
            self.log("❌  Ingresa el comando Speak")
            return
        if not cmd_map:
            self.log("❌  Ingresa el comando SpeakMap")
            return
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["BOT_SPEAK_CMD"] = cmd
        cfg["BOT_SPEAKMAP_CMD"] = cmd_map
        cfg["BOT_VOICE_MALE"] = voice_male
        cfg["BOT_VOICE_FEMALE"] = voice_female
        save_config(cfg)
        self.log(f"✅  Guardado: {cmd} ({voice_male}), {cmd_map} ({voice_female})")

    def test_bot_speaker():
        voice_male_display = self.voice_male_var.get()
        voice_female_display = self.voice_female_var.get()
        voice_male_edge = voice_male_display.replace("_", "-")
        voice_female_edge = voice_female_display.replace("_", "-")
        _, device_id = self.get_devices()
        vol = float(config.get("VOLUME", "2.0"))
        self.log("Probando voz masculina...")
        from src.audio import speak
        speak("Hola, esta es una prueba de voz masculina", voice_male_edge, device_id, volume=vol)
        import time
        time.sleep(1)
        self.log("Probando voz femenina...")
        speak("Hola, esta es una prueba de voz femenina", voice_female_edge, device_id, volume=vol)

    btn_frame = ctk.CTkFrame(c, fg_color="transparent")
    btn_frame.pack(fill="x", padx=14, pady=(0, 10))
    btn_frame.grid_columnconfigure((0, 1), weight=1)
    ctk.CTkButton(btn_frame, text="💾 Guardar comandos", fg_color=GRN, text_color=GRN_T,
                 height=34, corner_radius=8, hover_color="#10b981",
                 command=guardar_bot_cmds).grid(row=0, column=0, padx=(0, 4), sticky="ew")
    ctk.CTkButton(btn_frame, text="🧪 Test", fg_color=PURP, text_color="#f3e8ff",
                 height=34, corner_radius=8, hover_color="#a855f7",
                 command=test_bot_speaker).grid(row=0, column=1, padx=(4, 0), sticky="ew")

    audio_card = mk(tab, accent=True)
    audio_card.pack(fill="x", padx=14, pady=(8, 6))
    lb(audio_card, "🔊  Sonidos personalizados", sz=12, bold=True).pack(anchor="w", padx=14, pady=(10, 2))
    lbl_audio = lb(audio_card, "Sube archivos MP3 y asígnales un comando para Twitch", sz=10, col=MUT)
    lbl_audio.pack(anchor="w", padx=14, pady=(0, 6))
    ToolTip(lbl_audio, "Asigna archivos de audio (MP3/WAV/OGG) a comandos de Twitch.\nCuando un viewer escribe el comando, se reproduce el sonido.")

    self._audio_slots = []
    audio_inner = ctk.CTkFrame(audio_card, fg_color="transparent")
    audio_inner.pack(fill="x", padx=14, pady=(0, 10))

    def seleccionar_audio(idx, path_var):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title=f"Seleccionar audio #{idx}",
                                          filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
        if path:
            path_var.set(path)
            self.log(f"🔊 Audio #{idx}: {path}")

    def reprobar_audio(path):
        if not path:
            self.log("⚠  No hay archivo seleccionado")
            return
        if not os.path.isfile(path):
            self.log(f"⚠  Archivo no encontrado: {path}")
            return
        from src.audio import play_file
        sp_dev, _ = self.get_devices()
        self.log(f"🔊 Reproduciendo: {os.path.basename(path)} (device {sp_dev})")
        import threading
        def _play():
            try:
                play_file(path, sp_dev)
            except Exception as e:
                self.after(0, lambda e=e: self.log(f"❌ Error reproduciendo: {e}"))
        threading.Thread(target=_play, daemon=True).start()

    def guardar_audio_slots():
        from src.core.config import load_config, save_config
        cfg = load_config()
        for i, path_var, cmd_var in self._audio_slots:
            cfg[f"AUDIO_FILE_{i}"] = path_var.get()
            cfg[f"AUDIO_CMD_{i}"] = cmd_var.get()
        save_config(cfg)
        self.log("✅  Sonidos guardados")

    for i in range(1, 6):
        row = ctk.CTkFrame(audio_inner, fg_color="transparent")
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(1, weight=1)

        lb(row, f"#{i}", sz=11, col=PURP, width=22).grid(row=0, column=0, padx=(0, 4))

        path_var = ctk.StringVar(value=config.get(f"AUDIO_FILE_{i}", ""))
        entry_path = ctk.CTkEntry(row, textvariable=path_var,
                                   font=("Consolas", 10), fg_color=CARD, text_color=MUT,
                                   border_color="#2a2a3e", state="readonly")
        entry_path.grid(row=0, column=1, sticky="ew", padx=(0, 4))

        cmd_var = ctk.StringVar(value=config.get(f"AUDIO_CMD_{i}", ""))
        entry_cmd = ctk.CTkEntry(row, textvariable=cmd_var, placeholder_text="!comando",
                                  font=("Consolas", 11, "bold"), width=120,
                                  fg_color=CARD, text_color=TXT, border_color=BORD)
        entry_cmd.grid(row=0, column=2, padx=(0, 4))

        ctk.CTkButton(row, text="📂", fg_color=CARD2, text_color=TXT, width=32, height=28,
                      corner_radius=6, command=lambda idx=i, pv=path_var: seleccionar_audio(idx, pv)).grid(row=0, column=3, padx=(0, 2))
        ctk.CTkButton(row, text="▶", fg_color=CARD2, text_color=GRN_T, width=32, height=28,
                      corner_radius=6, command=lambda pv=path_var: reprobar_audio(pv.get())).grid(row=0, column=4)

        self._audio_slots.append((i, path_var, cmd_var))

    ctk.CTkButton(audio_card, text="💾 Guardar sonidos", fg_color=GRN, text_color=GRN_T,
                  height=30, corner_radius=8, hover_color="#10b981",
                  command=guardar_audio_slots).pack(padx=14, pady=(0, 10))

    return tab
