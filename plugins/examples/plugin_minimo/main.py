"""
plugin_minimo — Plugin de ejemplo que demuestra:
  - Registro de hooks (on_frame, on_commentary)
  - Agregar pestaña propia en la UI
  - Leer/escribir configuración
  - Agregar switch configurable
"""

import customtkinter as ctk

api = None


def on_load(_api):
    """Inicialización del plugin. Recibe la instancia de AppAPI."""
    global api
    api = _api

    api.log("[Plugin Mínimo] ¡Cargado exitosamente!")

    # Registrar un switch configurable en la pestaña Plugins
    api.add_switch("plugin_minimo", "saludar", "Saludar al iniciar partida", True)

    api.log("[Plugin Mínimo] Usa !hola en el chat de Twitch para probar")
    return True


def on_unload():
    """Limpieza al descargar el plugin."""
    api.log("[Plugin Mínimo] Descargado.")


# ── Hooks ────────────────────────────────────────────────────

def on_frame(frame, fps):
    """Se ejecuta en cada frame capturado (no bloquear)."""
    # Ejemplo: solo log cada 300 frames (~5s a 60fps)
    if frame is not None and hasattr(on_frame, "_count"):
        on_frame._count += 1
        if on_frame._count % 300 == 0:
            h, w = frame.shape[:2]
            api.log(f"[Plugin Mínimo] Frame {on_frame._count}: {w}x{h} @ {fps:.1f} FPS")
    elif frame is not None:
        on_frame._count = 1


def on_commentary(texto_ia):
    """Se ejecuta cuando la IA genera un comentario."""
    estado = api.get_game_info().get("estado", "")
    if "combate" in estado and "jefe" in texto_ia.lower():
        api.log("[Plugin Mínimo] ¡Detectado combate contra jefe en comentario!")


def on_ui_tab(parent_frame):
    """Agrega una pestaña personalizada en la UI."""
    frame = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")

    ctk.CTkLabel(
        frame, text="Plugin Mínimo",
        font=("Segoe UI", 20, "bold"),
        text_color="#c084fc"
    ).pack(anchor="w", padx=20, pady=(20, 10))

    ctk.CTkLabel(
        frame, text="Este plugin demuestra cómo agregar una pestaña propia.",
        font=("Segoe UI", 12),
        text_color="#94a3b8"
    ).pack(anchor="w", padx=20, pady=(0, 20))

    # Mostrar estado
    info = api.get_game_info()
    estado_texto = (
        f"Juego: {info.get('juego', 'N/A')}\n"
        f"Estado: {info.get('estado', 'N/A')}\n"
        f"Dimensión: {info.get('dimension', 'N/A')}"
    )
    ctk.CTkLabel(
        frame, text=estado_texto,
        font=("Segoe UI", 12),
        text_color="#e2e8f0",
        justify="left"
    ).pack(anchor="w", padx=20, pady=10)

    # Switch de ejemplo
    switch_valor = api.get_switch("plugin.plugin_minimo.saludar")
    switch = ctk.CTkSwitch(
        frame, text="Saludar al iniciar partida",
        font=("Segoe UI", 12),
        switch_width=40, switch_height=20
    )
    switch.select() if switch_valor else switch.deselect()
    switch.pack(anchor="w", padx=20, pady=10)

    def _toggle_switch():
        api.set_config("plugin.plugin_minimo.saludar", bool(switch.get()))

    switch.configure(command=_toggle_switch)

    ctk.CTkLabel(
        frame, text="ℹ️ Los switches también aparecen en la pestaña Plugins.",
        font=("Segoe UI", 11),
        text_color="#64748b"
    ).pack(anchor="w", padx=20, pady=(20, 5))

    # Botón de prueba
    def _test_speak():
        juego = api.get_game_info().get("juego", "mundo")
        api.speak(f"¡Hola! Este es el Plugin Mínimo hablando desde {juego}.")

    ctk.CTkButton(
        frame, text="🔊 Probar TTS",
        font=("Segoe UI", 12),
        fg_color="#7c3aed",
        hover_color="#6d28d9",
        command=_test_speak
    ).pack(anchor="w", padx=20, pady=10)

    return frame
