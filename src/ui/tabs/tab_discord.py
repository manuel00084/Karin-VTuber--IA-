import customtkinter as ctk
import threading

from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, TXT, TXT_MUTED as MUT
from src.ui.widgets import mk, lb


def build_tab_discord(parent, app, frame):
    self = app

    # ── Connection card ──
    conn_card = mk(frame)
    conn_card.pack(fill="x", padx=14, pady=(12, 6))
    lb(conn_card, "🔊  Conexión Discord", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    lb(conn_card, "Token del bot Discord", sz=9, col=MUT).pack(anchor="w", padx=14, pady=(2, 0))
    token_entry = ctk.CTkEntry(
        conn_card, font=("Segoe UI", 10), show="*",
        fg_color=CARD, text_color=TXT, border_width=0, height=28,
        placeholder_text="DISCORD_BOT_TOKEN",
    )
    token_entry.pack(fill="x", padx=14, pady=(2, 6))

    lb(conn_card, "ID del canal de texto", sz=9, col=MUT).pack(anchor="w", padx=14, pady=(2, 0))
    txt_ch_entry = ctk.CTkEntry(
        conn_card, font=("Segoe UI", 10),
        fg_color=CARD, text_color=TXT, border_width=0, height=28,
        placeholder_text="123456789012345678",
    )
    txt_ch_entry.pack(fill="x", padx=14, pady=(2, 6))

    lb(conn_card, "ID del canal de voz (opcional)", sz=9, col=MUT).pack(anchor="w", padx=14, pady=(2, 0))
    voice_ch_entry = ctk.CTkEntry(
        conn_card, font=("Segoe UI", 10),
        fg_color=CARD, text_color=TXT, border_width=0, height=28,
        placeholder_text="123456789012345678 (vacío = solo texto)",
    )
    voice_ch_entry.pack(fill="x", padx=14, pady=(2, 6))

    def load_config():
        from src.core.config import load_config
        cfg = load_config()
        token_entry.delete(0, "end")
        token_entry.insert(0, cfg.get("DISCORD_BOT_TOKEN", ""))
        txt_ch_entry.delete(0, "end")
        txt_ch_entry.insert(0, cfg.get("DISCORD_TEXT_CHANNEL", ""))
        voice_ch_entry.delete(0, "end")
        voice_ch_entry.insert(0, cfg.get("DISCORD_VOICE_CHANNEL", ""))

    def save_config():
        from src.core.config import save_config, load_config
        cfg = load_config()
        cfg["DISCORD_BOT_TOKEN"] = token_entry.get().strip()
        cfg["DISCORD_TEXT_CHANNEL"] = txt_ch_entry.get().strip()
        cfg["DISCORD_VOICE_CHANNEL"] = voice_ch_entry.get().strip()
        save_config(cfg)
        self.log("✅  Configuración de Discord guardada")

    load_config()

    btn_frame = ctk.CTkFrame(conn_card, fg_color="transparent")
    btn_frame.pack(fill="x", padx=14, pady=(4, 8))

    status_var = ctk.StringVar(value="🔴  Desconectado")

    def toggle_bot():
        from src.discord_bot import start_bot, stop_bot, is_running
        if is_running():
            stop_bot()
            status_var.set("🔴  Desconectado")
            toggle_btn.configure(text="Conectar Discord")
            self.log("🔴 Discord desconectado")
        else:
            token = token_entry.get().strip()
            if not token:
                self.log("⚠  Ingresá el token del bot Discord")
                return
            text_cid = txt_ch_entry.get().strip()
            if not text_cid:
                self.log("⚠  Ingresá el ID del canal de texto")
                return
            voice_cid = voice_ch_entry.get().strip()
            try:
                text_cid_int = int(text_cid)
                voice_cid_int = int(voice_cid) if voice_cid else None
            except ValueError:
                self.log("⚠  Los IDs deben ser números")
                return

            def on_ready():
                status_var.set("🟢  Conectado")
                toggle_btn.configure(text="Desconectar Discord")

            def handle_msg(author, content):
                from src.core.config import load_config
                cfg = load_config()
                api_key = cfg.get("CEREBRAS_API_KEY", "")
                if not api_key:
                    return None
                from src.ia.cache import cached_ask_ai
                prompt = getattr(self, "current_prompt", "Sos Karin, una VTuber amigable.")
                resp = cached_ask_ai(author, content, api_key, prompt, "cerebras")
                return resp

            save_config()
            start_bot(token, text_cid_int, voice_cid_int or None,
                      log_fn=self.log, message_handler=handle_msg,
                      ready_callback=on_ready)
            status_var.set("🟡  Conectando...")

    toggle_btn = ctk.CTkButton(
        btn_frame, text="Conectar Discord",
        command=toggle_bot,
        fg_color="#5865F2", hover_color="#4752C4",
        text_color="#fff", font=("Segoe UI", 11, "bold"),
        corner_radius=10, height=32,
    )
    toggle_btn.pack(side="left", padx=(0, 6))

    status_lb = ctk.CTkLabel(btn_frame, textvariable=status_var,
                              font=("Segoe UI", 10), text_color=TXT)
    status_lb.pack(side="left")

    def guardar():
        save_config()
    ctk.CTkButton(
        btn_frame, text="💾", width=28, height=28,
        command=guardar,
        fg_color=CARD2, hover_color=PURP,
        text_color="#fff", font=("Segoe UI", 11),
        corner_radius=4, border_width=0,
    ).pack(side="right", padx=2)

    # ── Info card ──
    info_card = mk(frame)
    info_card.pack(fill="x", padx=14, pady=(6, 12))
    lb(info_card, "📖  Cómo obtener el token", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    steps = [
        "1️⃣  Andá a https://discord.com/developers/applications",
        "2️⃣  Click 'New Application' → poné nombre → Create",
        "3️⃣  Bot → Add Bot → Reset Token → copiá el token",
        "4️⃣  Activá Message Content Intent en Bot → Privileged Gateway Intents",
        "5️⃣  OAuth2 → URL Generator → Bot + Send Messages/Connect/Speak",
        "6️⃣  Abrí la URL generada, seleccioná el servidor",
        "7️⃣  Copiá el ID del canal (activá modo desarrollador → click derecho canal → Copy ID)",
    ]
    for step in steps:
        lb(info_card, step, sz=9, col=MUT).pack(anchor="w", padx=14, pady=1)
