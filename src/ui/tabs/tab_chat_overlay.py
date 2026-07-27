import customtkinter as ctk

from src.ui.theme import BG, CARD_BG_HEX as CARD, CARD2, PURP, BORD, TXT
from src.ui.widgets import mk, lb


_overlay_instance = None


def build_tab_chat_overlay(parent, app, frame):
    self = app

    card = mk(frame)
    card.pack(fill="x", padx=14, pady=(12, 6))
    lb(card, "🌐  Chat Overlay", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))
    lb(card, "Ventana flotante transparente para ver el chat de Twitch, escribir y usar voz.",
       sz=9, col="#999").pack(anchor="w", padx=14, pady=(0, 6))

    btn_var = ctk.StringVar(value="Mostrar Overlay")

    def toggle_overlay():
        global _overlay_instance
        if _overlay_instance and _overlay_instance._visible:
            _overlay_instance.hide()
            btn_var.set("Mostrar Overlay")
        else:
            try:
                from src.chat_overlay.overlay import ChatOverlay
                if _overlay_instance is None:
                    _overlay_instance = ChatOverlay()
                _overlay_instance.show()
                btn_var.set("Ocultar Overlay")
                self.log("🌐  Chat Overlay mostrado")
            except Exception as e:
                self.log(f"❌  Error al crear overlay: {e}")

    toggle_btn = ctk.CTkButton(
        card, textvariable=btn_var,
        command=toggle_overlay,
        fg_color=PURP, hover_color=BORD,
        text_color="#fff", font=("Segoe UI", 12, "bold"),
        corner_radius=10, height=36,
    )
    toggle_btn.pack(anchor="w", padx=14, pady=(0, 8))

    def destroy_overlay():
        global _overlay_instance
        if _overlay_instance:
            _overlay_instance.destroy()
            _overlay_instance = None

    frame.bind("<Destroy>", lambda e: destroy_overlay())

    info_card = mk(frame)
    info_card.pack(fill="x", padx=14, pady=(0, 6))
    lb(info_card, "📖  Cómo usar", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    tips = [
        "✏️  Escribí un mensaje y presioná Enter o click en ➤ para enviar",
        "🎤  Click en 🎤 para activar/desactivar el micrófono (STT)",
        "🌐  Los mensajes se traducen automáticamente al español",
        "↕  Arrastrá el overlay desde la barra superior",
        "❌  Click en ✕ para cerrar el overlay",
    ]
    for tip in tips:
        lb(info_card, tip, sz=9, col="#aaa").pack(anchor="w", padx=14, pady=1)

    status_card = mk(frame)
    status_card.pack(fill="x", padx=14, pady=(6, 12))
    lb(status_card, "🔌  Estado", sz=11, bold=True, col=PURP).pack(anchor="w", padx=14, pady=(8, 4))

    status_label = ctk.CTkLabel(status_card, text="Verificando...", font=("Segoe UI", 10), text_color=TXT)
    status_label.pack(anchor="w", padx=14, pady=(0, 8))

    try:
        from src.bot.twitch_bot import _bot_instance
        if _bot_instance:
            status_label.configure(text="✅  Bot de Twitch conectado", text_color="#2ecc71")
        else:
            status_label.configure(text="⏳  Bot de Twitch no conectado (conectá en Panel primero)", text_color="#e74c3c")
    except Exception:
        status_label.configure(text="❌  No se pudo verificar el estado del bot", text_color="#e74c3c")
