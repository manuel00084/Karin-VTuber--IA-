"""
plugins/api.py — API pública que los plugins pueden consumir.
Cada plugin recibe una instancia de AppAPI en su `on_load()`.
"""


class AppAPI:
    """Interfaz que la aplicación expone a los plugins."""

    def __init__(self, app=None, game_watcher=None):
        self._app = app
        self._switches = {}
        self._game_watcher = game_watcher

    def _gw(self):
        """Resolve game_watcher — prefers stored ref, falls back to app."""
        return self._game_watcher or (self._app.game_watcher if self._app else None)

    # ── Logging ──────────────────────────────────────────────
    def log(self, msg):
        """Escribe un mensaje en el log de la aplicación."""
        if self._app and hasattr(self._app, "log"):
            self._app.log(msg)
        else:
            print(f"[Plugin] {msg}")

    # ── Audio / TTS ──────────────────────────────────────────
    def speak(self, texto, voz=None):
        """Habla un texto usando el TTS configurado."""
        from src.audio import speak as _speak
        _speak(texto, voz or getattr(self._app, "voice", None))

    # ── Captura de pantalla ──────────────────────────────────
    def get_frame(self):
        """Devuelve el último frame capturado (np.ndarray) o None."""
        gw = self._gw()
        if gw and hasattr(gw, "_ultimo_frame"):
            return gw._ultimo_frame
        return None

    def get_screen_size(self):
        """Devuelve (ancho, alto) de la captura actual o (0,0)."""
        gw = self._gw()
        if gw and hasattr(gw, "_screen_size"):
            return gw._screen_size
        return (0, 0)

    # ── OCR ──────────────────────────────────────────────────
    def get_ocr_text(self):
        """Devuelve el último texto detectado por OCR."""
        gw = self._gw()
        if gw and hasattr(gw, "_ultimo_ocr"):
            return gw._ultimo_ocr
        return ""

    # ── Información del juego ────────────────────────────────
    def get_game_info(self):
        """Devuelve un dict con info del juego actual."""
        gw = self._gw()
        if gw:
            return {
                "juego": getattr(gw, "juego_actual", ""),
                "estado": getattr(gw, "_estado_escena", ""),
                "dimension": getattr(gw, "_game_dimension", ""),
                "ultimo_evento": getattr(gw, "_ultimo_evento", ""),
            }
        return {}

    # ── Configuración persistente ────────────────────────────
    def get_config(self, key, default=None):
        """Lee un valor de la configuración global."""
        from src.core.config import load_config
        cfg = load_config()
        return cfg.get(key, default)

    def set_config(self, key, value):
        """Escribe un valor en la configuración global."""
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg[key] = value
        save_config(cfg)

    # ── Switches configurables desde UI ──────────────────────
    def add_switch(self, plugin_name, key, label, default=False):
        """Registra un switch on/off que aparecerá en la pestaña Plugins."""
        full_key = f"plugin.{plugin_name}.{key}"
        self._switches[full_key] = {"label": label, "default": default}
        # Persistir valor por defecto si no existe
        current = self.get_config(full_key, None)
        if current is None:
            self.set_config(full_key, default)
        return full_key

    def get_switch(self, key):
        """Lee el valor actual de un switch registrado."""
        return self.get_config(key, False)

    # ── Comandos de Twitch ───────────────────────────────────
    def register_command(self, comando, callback):
        """Registra un comando !comando que ejecutará callback(usuario, args)."""
        from src.bot.twitch_bot import _registrar_comando_plugin
        _registrar_comando_plugin(comando, callback)
        self.log(f"Comando !{comando} registrado por plugin")

    # ── UI: agregar pestaña propia ──────────────────────────
    def add_ui_tab(self, nombre, frame):
        """Agrega una pestaña en la interfaz (debe llamarse desde on_ui_tab)."""
        if self._app and hasattr(self._app, "_add_plugin_tab"):
            self._app._add_plugin_tab(nombre, frame)

    # ── Vector Memory (memoria persistente) ─────────────────
    def memory_search(self, query, n=5):
        """Busca en la memoria vectorial."""
        from src.ia.vector_memory import search_memory
        return search_memory(query, n_results=n)

    def memory_add(self, text, user="plugin", role="system"):
        """Agrega un texto a la memoria vectorial."""
        from src.ia.vector_memory import add_to_memory
        add_to_memory(text, user=user, role=role)

    # ── CLIP Scene Analysis ─────────────────────────────────
    def analyze_scene(self, image=None):
        """Analiza una escena con CLIP. Si image es None, usa el último frame."""
        from src.vision_clip import CLIPSceneAnalyzer
        img = image if image is not None else self.get_frame()
        if img is None:
            return None
        try:
            clip = CLIPSceneAnalyzer(model_name="mobileclip_s2")
            return clip.escena_detectada(img)
        except Exception:
            return None

    # ── FPS / rendimiento ────────────────────────────────────
    def get_fps(self):
        """Devuelve los FPS actuales del loop de captura."""
        gw = self._gw()
        if gw and hasattr(gw, "_fps"):
            return gw._fps
        return 0
