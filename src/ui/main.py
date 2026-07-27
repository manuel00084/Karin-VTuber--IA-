import customtkinter as ctk
import threading, os, traceback, webbrowser, requests, time, json
try:
    import keyboard
    KEYBOARD_OK = True
except ImportError:
    KEYBOARD_OK = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "0.9.1-beta"
APP_NAME = "Karin VTuber -IA-"

from src.core.config import load_config
from src.audio import audio_worker, speak, stop_audio, get_output_devices
from src.ia import ask_ai
from src.bot.twitch_bot import start_chat
from src.core.oauth_server import TwitchOAuth, validate_token
from src.utils.ptt import PTTManager
from src.translator.engine import TranslationEngine
from src.alerts.engine import AlertEngine

from src.utils import PIL_OK
from src import PROJECT_ROOT
from PIL import Image

# Sistema de plugins
from plugins import PluginManager
from plugins.api import AppAPI

from src.ui.tabs.tab_panel import build_tab_panel
from src.ui.tabs.tab_audio import build_tab_audio
from src.ui.tabs.tab_chat_ia import build_tab_chat_ia
from src.ui.tabs.tab_chat_bot import build_tab_chat_bot
from src.ui.tabs.tab_plugins import build_tab_plugins
from src.ui.tabs.tab_obs import build_tab_obs
from src.ui.tabs.tab_creditos import build_tab_creditos
from src.ui.tabs.tab_avatar import build_tab_avatar
from src.ui.tabs.tab_kste import build_tab_kste
from src.ui.theme import BG, SIDE, CARD_BG_HEX as CARD, CARD2, BORD, PURP, GRN, GRN_T, RED, RED_T_LIGHT as RED_T, BLU, BLU_T, AMB, AMB_T, TXT, MUT, LOGBG
from src.ui.widgets import lb, mk

config = load_config()



# ════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)
        threading.Thread(target=audio_worker, daemon=True).start()
        
        # Prompts
        self.prompt_folder = os.path.join(PROJECT_ROOT, "prompts")
        os.makedirs(self.prompt_folder, exist_ok=True)
        self.prompt_files = [f for f in os.listdir(self.prompt_folder) if f.endswith(".txt")]
        if not self.prompt_files:
            p = os.path.join(self.prompt_folder, "default.txt")
            with open(p, "w", encoding="utf-8") as f:
                f.write("Eres una VTuber divertida.")
            self.prompt_files = ["default.txt"]
        
        # Cargar la personalidad guardada o usar la primera por defecto
        selected_prompt_file = config.get("SELECTED_PROMPT", self.prompt_files[0])
        # Verificar que el archivo guardado existe, si no usar el primero
        if selected_prompt_file not in self.prompt_files:
            selected_prompt_file = self.prompt_files[0]
        self._selected_prompt_file = selected_prompt_file
        self.current_prompt = ""
        
        self.devices   = get_output_devices()
        self.dev_names = [n for n, _ in self.devices] or ["Default"]
        
        # Restaurar dispositivos seleccionados desde config
        try:
            sp_idx = int(config.get("SPEAKER_DEVICE", 0))
        except (ValueError, TypeError):
            sp_idx = 0
        try:
            ia_idx = int(config.get("IA_DEVICE", 0))
        except (ValueError, TypeError):
            ia_idx = 0
        if sp_idx < len(self.dev_names):
            self._sp_default = self.dev_names[sp_idx]
        else:
            self._sp_default = self.dev_names[0] if self.dev_names else "Default"
        if ia_idx < len(self.dev_names):
            self._ia_default = self.dev_names[ia_idx]
        else:
            self._ia_default = self.dev_names[0] if self.dev_names else "Default"
        try:
            mn_idx = int(config.get("MONITOR_DEVICE", 0))
        except (ValueError, TypeError):
            mn_idx = 0
        if mn_idx < len(self.dev_names):
            self._mn_default = self.dev_names[mn_idx]
        else:
            self._mn_default = "(Ninguno)"
        self.game_watcher = None
        self.lector_subtitulos = None
        self.hotkey_reader = None
        self._lectura_auto_activa = False
        
        # Traductor
        self.translator_engine = TranslationEngine(log_fn=self._log_traductor)
        self.alert_engine = AlertEngine(log_fn=self.log)

        # OBS
        self.obs_controller = None

        # KarinMocap
        self._mocap_controller = None

        # Streamer
        self._streamer_vmm = None


        
        # Todas las voces disponibles
        self.voices_all = ["es-ES-ElviraNeural", "es-ES-AlvaroNeural",
                           "es-MX-DaliaNeural", "es-MX-LiaNeural", "es-MX-DarioNeural",
                           "es-AR-EmiliaNeural", "es-AR-TonoNeural"]
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Plugin manager (descubrimiento temprano para _tab_plugins; carga diferida)
        self._plugin_manager = PluginManager()
        self._plugin_api = AppAPI(app=self, game_watcher=self.game_watcher)
        self._plugin_manager.discover()

        self._tabs = {}
        self._nav_btns = {}
        self._nav_indicators = {}

        self._build_sidebar()

        # Cargar plugins ANTES de _build_content para que los hooks
        # (ej. ui_tab) estén registrados cuando _tab_plugins los emita
        try:
            if self._plugin_manager.plugins:
                cargados = self._plugin_manager.load_all(self._plugin_api)
                self._plugin_manager.emit("app_ready")
            else:
                print("[Plugins] No se encontraron plugins")
        except Exception as e:
            print(f"[Plugins] Error: {e}")

        self._build_content()

        # Inicializar pitch y EQ monitor desde config
        from src.audio.audio import set_pitch, set_monitor_device, set_eq_gain
        pitch_val = int(config.get("MONITOR_PITCH", "0"))
        set_pitch(pitch_val)
        for i in range(5):
            g = int(config.get(f"MONITOR_EQ_{i}", "0"))
            set_eq_gain(i, g)
        mn_name = getattr(self, "_mn_default", "(Ninguno)")
        if mn_name not in ("(Ninguno)", ""):
            mid = next((i for n, i in self.devices if n == mn_name), None)
            set_monitor_device(mid)

        # PTT
        saved_ptt_key = config.get("PTT_KEY", "F9")
        if PTTManager:
            try:
                saved_vol = float(config.get("VOLUME", "2.0"))
                self.ptt_obj = PTTManager(
                    app=self, ask_ai_fn=ask_ai, speak=speak,
                    stop_audio=stop_audio, config=config,
                    get_devices=self.get_devices,
                    current_prompt=lambda: self.current_prompt,
                    key=saved_ptt_key.lower(), voice="es-MX-DaliaNeural",
                    volume=saved_vol)
                self.log(f"⌨  PTT listo — mantén CTRL+{saved_ptt_key} para hablar")
            except Exception as e:
                self.log(f"⚠  PTT error: {e}")
        else:
            self.log("⚠  PTT no disponible — pip install keyboard")

        if not PIL_OK:
            self.log("Comentarista: pip install pillow")

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Auto-conectar OBS
        obs_host = config.get("OBS_HOST", "")
        obs_port = config.get("OBS_PORT", "")
        if obs_host and obs_port:
            try:
                from src.obs_controller import OBSController
                self.obs_controller = OBSController(log_fn=self.log)
                self.obs_controller.config(obs_host, int(obs_port), config.get("OBS_PASSWORD", ""))
                self.obs_controller.connect()
            except Exception as e:
                self.log(f"[OBS] Auto-conexion fallida: {e}")

        # Auto-cargar perfil por defecto
        default_profile = config.get("DEFAULT_PROFILE", "")
        if default_profile:
            try:
                from src.core.secrets_manager import load_profile
                if load_profile(default_profile):
                    self.log(f"💾  Perfil '{default_profile}' cargado automáticamente")
            except Exception as e:
                self.log(f"⚠  Error cargando perfil por defecto: {e}")

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0, width=220)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        for r in range(9):
            sb.grid_rowconfigure(r, weight=1 if r == 3 else 0)
        
        hdr = ctk.CTkFrame(sb, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(16, 4))
        
        # Agregar logo
        try:
            logo_path = os.path.join(PROJECT_ROOT, "assets", "logo", "avatar.png")
            self._logo_img = ctk.CTkImage(light_image=Image.open(logo_path), size=(80, 80))
            ctk.CTkLabel(hdr, image=self._logo_img, text="").pack(anchor="center", pady=(0, 8))
        except Exception as e:
            print(f"Error cargando logo: {e}")
        
        lb(hdr, "Karin VTuber", sz=15, bold=True, col=PURP).pack(anchor="center")
        
        ctk.CTkFrame(sb, height=1, fg_color=BORD).grid(row=1, column=0, sticky="ew", padx=8)
        
        self._nav_btns = {}
        self._nav_indicators = {}
        self._nav_container = ctk.CTkFrame(sb, fg_color="transparent")
        self._nav_container.grid(row=3, column=0, sticky="nsew", padx=6, pady=4)
        sb.grid_rowconfigure(3, weight=1)

        buttons = [
            ("📊  Panel",        "panel"),
            ("🎧  Audio",        "audio"),
            ("🤖  Chat Bot",     "chat_bot"),
            ("⚙  Core IA",      "chat_ia"),
            ("🎨  Avatar",       "avatar"),
            ("🌐  KSTE",        "kste"),
            ("🧩  Plugins",      "plugins"),
            ("📺  OBS",           "obs"),
            ("❓  Ayuda",        "creditos"),
        ]

        for i, (txt, key) in enumerate(buttons):
            row = ctk.CTkFrame(self._nav_container, fg_color="transparent", height=36)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            
            indicator = ctk.CTkFrame(row, fg_color="transparent", width=3, corner_radius=0)
            indicator.pack(side="left", fill="y")
            self._nav_indicators[key] = indicator
            
            b = ctk.CTkButton(row, text=txt, anchor="w", fg_color="transparent",
                              text_color=MUT, hover_color=CARD2, font=("Segoe UI", 12),
                              corner_radius=0, height=36, border_width=0,
                              command=lambda k=key: self._tab(k))
            b.pack(side="left", fill="x", expand=True, padx=(4, 0))
            self._nav_btns[key] = b
        
        ctk.CTkFrame(sb, height=1, fg_color="#2a2a3e").grid(row=9, column=0, sticky="ew", padx=12, pady=6)
        
        self.twitch_btn = ctk.CTkButton(
            sb, text="🔴  Twitch", fg_color="#9146FF", text_color="#fff",
            hover_color="#772CE8", font=("Segoe UI", 11, "bold"), corner_radius=10,
            height=34, command=self.connect_twitch)
        self.twitch_btn.grid(row=10, column=0, padx=8, pady=(4, 8), sticky="ew")
    
    def _tab(self, key):
        if hasattr(self, '_tab_built'):
            self._guardar_config_panel()
        if key == "audio":
            self._refresh_audio_devices()
        elif key == "panel":
            self._refresh_prompts()
        elif key == "plugins":
            if key in self._tab_built:
                self._tabs[key].destroy()
                del self._tabs[key]
                self._tab_built.discard(key)
                self._plugin_manager.discover()
        for k, b in self._nav_btns.items():
            is_active = (k == key)
            b.configure(fg_color=CARD2 if is_active else "transparent",
                        text_color=TXT if is_active else MUT)
            ind = self._nav_indicators.get(k)
            if ind:
                ind.configure(fg_color=BORD if is_active else "transparent")
        # Lazy-load tab on first access
        if key not in self._tab_built:
            builder = self._tab_builders.get(key)
            if builder:
                area = self._tab_placeholder.master
                frame = builder(area)
                self._tabs[key] = frame
                self._tab_built.add(key)
        for k, f in self._tabs.items():
            if k == key:
                f.grid(row=0, column=0, sticky="nsew")
            else:
                f.grid_remove()
    
    # ════════════════════════════════════════════════════════════════════════
    #  CONTENIDO
    # ════════════════════════════════════════════════════════════════════════
    def _build_content(self):
        wrap = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        wrap.grid(row=0, column=1, sticky="nsew")
        wrap.grid_rowconfigure(0, weight=0)
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        
        # Topbar
        top = ctk.CTkFrame(wrap, fg_color=SIDE, corner_radius=0, height=48)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)
        top.grid_columnconfigure(1, weight=1)
        
        # Accent bottom line
        ctk.CTkFrame(top, fg_color=BORD, height=2, corner_radius=0).grid(row=1, column=0, columnspan=3, sticky="ew")
        
        inner_top = ctk.CTkFrame(top, fg_color="transparent")
        inner_top.grid(row=0, column=0, sticky="ew", padx=14)
        inner_top.grid_columnconfigure(1, weight=1)
        lb(inner_top, "Panel de control", sz=14, bold=True).grid(row=0, column=0, sticky="w")
        lb(inner_top, f"v{APP_VERSION}", sz=10, col=MUT).grid(row=0, column=2, sticky="e", padx=(10, 0))
        

        
        # Área tabs
        area = ctk.CTkFrame(wrap, fg_color=BG, corner_radius=0)
        area.grid(row=1, column=0, sticky="nsew")
        area.grid_rowconfigure(0, weight=1)
        area.grid_columnconfigure(0, weight=1)
        
        self._tabs = {}
        self._tab_builders = {
            "panel":        self._tab_panel,
            "audio":        self._tab_audio,
            "chat_bot":     self._tab_chat_bot,
            "chat_ia":      self._tab_chat_ia,
            "avatar":       self._tab_avatar,
            "kste":         self._tab_kste,
            "plugins":      self._tab_plugins,
            "obs":          self._tab_obs,
            "creditos":     self._tab_creditos,
        }
        self._tab_built = set()
        self._tab_placeholder = ctk.CTkLabel(area, text="", fg_color="transparent")
        self._tab_placeholder.grid(row=0, column=0, sticky="nsew")
        self._tab("panel")
        self._nav_btns["panel"].configure(fg_color=CARD2, text_color=TXT)
        self._nav_indicators["panel"].configure(fg_color=BORD)
    
    def _add_plugin_tab(self, nombre, frame):
        key = f"_plugin_{nombre.lower().replace(' ', '_')}"
        self._tab_builders[key] = lambda p, n=nombre, f=frame: f
        self._nav_container.update()
        row = ctk.CTkFrame(self._nav_container, fg_color="transparent", height=36)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        indicator = ctk.CTkFrame(row, fg_color="transparent", width=3, corner_radius=0)
        indicator.pack(side="left", fill="y")
        self._nav_indicators[key] = indicator
        b = ctk.CTkButton(row, text=f"🧩  {nombre}", anchor="w", fg_color="transparent",
                          text_color=MUT, hover_color=CARD2, font=("Segoe UI", 12),
                          corner_radius=0, height=36, border_width=0,
                          command=lambda k=key: self._tab(k))
        b.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self._nav_btns[key] = b

    def _refresh_audio_devices(self):
        try:
            from src.audio import get_output_devices
            self.devices = get_output_devices()
            self.dev_names = [n for n, _ in self.devices] or ["Default"]
            for attr in ("sp2", "ia2", "mn2"):
                cb = getattr(self, attr, None)
                if cb:
                    vals = ["(Ninguno)"] + self.dev_names if attr == "mn2" else self.dev_names
                    current = cb.get()
                    cb.configure(values=vals)
                    if current in vals:
                        cb.set(current)
                    else:
                        cb.set(vals[0])
        except Exception as e:
            self.log(f"Error refrescando dispositivos: {e}")

    def _refresh_prompts(self):
        try:
            folder = self.prompt_folder
            if os.path.isdir(folder):
                self.prompt_files = sorted([f for f in os.listdir(folder) if f.endswith(".txt")])
            if hasattr(self, "mode_select") and self.prompt_files:
                current = self.mode_select.get()
                self.mode_select.configure(values=self.prompt_files)
                if current in self.prompt_files:
                    self.mode_select.set(current)
                else:
                    self.mode_select.set(self.prompt_files[0])
        except Exception as e:
            self.log(f"Error refrescando prompts: {e}")

    # ════════════════════════════════════════════════════════════════════════
    #  TAB PANEL
    # ════════════════════════════════════════════════════════════════════════
    def _tab_panel(self, parent):
        return build_tab_panel(parent, self)
    
    # ════════════════════════════════════════════════════════════════════════
    #  TAB AUDIO
    # ════════════════════════════════════════════════════════════════════════
    def _tab_audio(self, parent):
        return build_tab_audio(parent, self)
    

    
    #  TAB CHAT BOT (Bot Speaker + Alertas)
    # ════════════════════════════════════════════════════════════════════════
    def _tab_chat_bot(self, parent):
        return build_tab_chat_bot(parent, self)

    #  TAB CHAT IA (Perfil IA + PTT + Comentarista + Traductor + API Key)
    # ════════════════════════════════════════════════════════════════════════
    def _tab_chat_ia(self, parent):
        return build_tab_chat_ia(parent, self)

    #  TAB AVATAR (Smart Avatar + Wallpaper Creator)
    # ════════════════════════════════════════════════════════════════════════
    def _tab_avatar(self, parent):
        return build_tab_avatar(parent, self)

    #  TAB KSTE (Smart Translator Engine)
    def _tab_kste(self, parent):
        return build_tab_kste(parent, self)

    # ── Pestaña Plugins ─────────────────────────────────────
    def _tab_plugins(self, parent):
        return build_tab_plugins(parent, self)




    
# ════════════════════════════════════════════════════════════════════════
    #  TAB OBS
    # ════════════════════════════════════════════════════════════════════════
    def _tab_obs(self, parent):
        return build_tab_obs(parent, self)

    def _log_traductor(self, msg):
        def _update():
            if hasattr(self, 'traductor_log'):
                self.traductor_log.insert("end", f"{msg}\n")
                self.traductor_log.see("end")
        try:
            self.after(0, _update)
        except Exception:
            pass

    def _sync_translator_config(self):
        eng = self.translator_engine
        eng.ocr_engine = self.translator_ocr_engine.get().lower().replace(" ", "_")
        prov_map = {
            "Google Web (gratuito)": "google_web",
            "Google Gemini": "google_gemini",
            "DeepL": "deepl",
            "Dummy (debug)": "dummy",
        }
        eng.translation_provider_name = prov_map.get(self.translator_provider.get(), "google_web")
        eng.translation_api_key = config.get("GOOGLE_STUDIO_API_KEY", "")
        eng.source_lang = self.translator_src_lang.get()
        eng.target_lang = self.translator_tgt_lang.get()
        try:
            eng.interval = float(self.translator_interval.get().strip() or 3)
        except ValueError:
            eng.interval = 3.0
        zoom_map = {"1.0x": 1.0, "1.5x": 1.5, "2.0x": 2.0, "3.0x": 3.0, "4.0x": 4.0}
        eng.preprocessor.zoom = zoom_map.get(self.translator_zoom.get(), 1.0)
        thresh = self.translator_threshold.get()
        eng.preprocessor.threshold = int(thresh.replace(" (off)", "")) if thresh != "0 (off)" else 0
        eng.preprocessor.erode = bool(self.translator_erode.get())
        eng.show_overlay = bool(self.translator_show_overlay.get())
        eng.speak_translation = bool(self.translator_speak.get())
        eng.voice = self.translator_voice.get()
        try:
            eng.tts_device = int(config.get("IA_DEVICE", 2))
        except ValueError:
            eng.tts_device = 2
        try:
            eng.overlay.set_opacity(float(self.translator_opacity.get()))
        except ValueError:
            pass
        try:
            eng.overlay.set_font_size(int(self.translator_font_size.get()))
        except ValueError:
            pass

    def _iniciar_traductor(self):
        self._sync_translator_config()
        if self.translator_engine._running:
            self._log_traductor("⚠  El traductor ya está en ejecución")
            return
        self.translator_engine.start()
        self.translator_btn.configure(text="🟢  Ejecutando...", fg_color=GRN, text_color=GRN_T)

    def _detener_traductor(self):
        self.translator_engine.stop()
        self.translator_btn.configure(text="▶  Iniciar", fg_color=GRN, text_color=GRN_T)
        self._log_traductor("⏹  Traductor detenido")

    def _test_traductor_ocr(self):
        import threading
        def run():
            self._log_traductor("🔍  Probando OCR...")
            self._sync_translator_config()
            result = self.translator_engine.test_ocr()
            self._log_traductor(f"  Resultado: {result[:120] if result else 'Nada'}")

            if result and len(result) > 3:
                self._log_traductor("🌐  Probando traducción...")
                trans = self.translator_engine.test_translation(result)
                self._log_traductor(f"  Traducción: {trans[:120] if trans else 'Error'}")
        threading.Thread(target=run, daemon=True).start()

    def _test_traductor_overlay(self):
        """Prueba la ventana overlay independientemente del OCR."""
        eng = self.translator_engine
        self._log_traductor("🖥  Probando overlay...")
        if eng.overlay._window and eng.overlay._window.winfo_exists():
            eng.overlay.destroy()
            self._log_traductor("  Overlay anterior destruido")

        eng.show_overlay = True
        eng.overlay.show()
        eng.overlay.update_text(
            "🔴 PRUEBA DE OVERLAY\n"
            "─\n"
            "¿Puedes ver esta ventana?\n"
            "Si la ves, el overlay funciona.\n"
            "Arrástrala: haz clic y mantén presionado."
        )
        eng.overlay.set_position(300, 200)
        self._log_traductor("  Overlay creado en (300, 200)")
        self._log_traductor("  Si NO ves la ventana, revisa:")
        self._log_traductor("    - ¿Está el juego en pantalla completa exclusiva?")
        self._log_traductor("    - Prueba con el juego en modo ventana/borderless")
        self._log_traductor("    - Busca una ventana negra con borde morado")

    def _guardar_traductor(self):
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["TRANSLATOR_OCR"] = self.translator_ocr_engine.get()
        cfg["TRANSLATOR_PROVIDER"] = self.translator_provider.get()
        cfg["TRANSLATOR_SRC_LANG"] = self.translator_src_lang.get()
        cfg["TRANSLATOR_TGT_LANG"] = self.translator_tgt_lang.get()
        cfg["TRANSLATOR_INTERVAL"] = self.translator_interval.get().strip() or "3"
        cfg["TRANSLATOR_ZOOM"] = self.translator_zoom.get()
        cfg["TRANSLATOR_THRESHOLD"] = self.translator_threshold.get()
        cfg["TRANSLATOR_ERODE"] = "1" if self.translator_erode.get() else "0"
        cfg["TRANSLATOR_SHOW_OVERLAY"] = "1" if self.translator_show_overlay.get() else "0"
        cfg["TRANSLATOR_SPEAK"] = "1" if self.translator_speak.get() else "0"
        cfg["TRANSLATOR_VOICE"] = self.translator_voice.get()
        cfg["TRANSLATOR_OPACITY"] = self.translator_opacity.get()
        cfg["TRANSLATOR_FONT_SIZE"] = self.translator_font_size.get()
        save_config(cfg)
        for k, v in cfg.items():
            config[k] = v
        self._log_traductor("✅  Configuración del traductor guardada")

    # ════════════════════════════════════════════════════════════════════════

    
    def _crear_nuevo_prompt(self):
        # Pedir nombre para el nuevo prompt
        dialog = ctk.CTkInputDialog(title="Nueva Personalidad", 
                                    text="Ingresa el nombre para la nueva personalidad:")
        nombre = dialog.get_input()
        if nombre:
            nombre = nombre.strip()
            if not nombre.endswith(".txt"):
                nombre += ".txt"
            
            if nombre in self.prompt_files:
                self.log(f"Ya existe una personalidad con ese nombre")
                return
            
            try:
                ruta = os.path.join(self.prompt_folder, nombre)
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write("Eres una VTuber divertida y amigable.")
                
                self.prompt_files = [f for f in os.listdir(self.prompt_folder) if f.endswith(".txt")]
                self.prompt_files.sort()
                
                self.mode_select.configure(values=self.prompt_files)
                self.mode_select.set(nombre)
                
                from src.core.config import load_config, save_config
                cfg = load_config()
                cfg["SELECTED_PROMPT"] = nombre
                save_config(cfg)
                config["SELECTED_PROMPT"] = nombre
                
                with open(ruta, encoding="utf-8") as f:
                    self.current_prompt = f.read()
                
                self.log(f"Nueva personalidad '{nombre}' creada")
            except Exception as e:
                self.log(f"Error al crear personalidad: {e}")
    
    def ptt_click(self):
        def run():
            try:
                from src.audio.stt import listen
                stop_audio(); self.log("🎤  Escuchando...")
                text = listen()
                if not text: self.log("❌  No se entendió"); return
                self.log(f"🗣  Tú: {text}")
                api_key = config.get("CEREBRAS_API_KEY", "") or config.get("GROQ_API_KEY", "")
                if not api_key:
                    self.log("❌  Falta CEREBRAS_API_KEY o GROQ_API_KEY"); return
                provider = "cerebras" if config.get("CEREBRAS_API_KEY") else "groq"
                r = ask_ai(text, api_key, self.current_prompt, provider)
                self.log(f"🤖  IA: {r}")
                _, d = self.get_devices()
                try:
                    vol = float(config.get("VOLUME", "1.0"))
                except (ValueError, TypeError):
                    vol = 1.0
                speak(r, "es-MX-DaliaNeural", d, volume=vol)
            except Exception as e:
                self.log(f"❌  PTT: {e}")
        threading.Thread(target=run, daemon=True).start()

    def connect_twitch(self):
        """
        Si ya hay TWITCH_TOKEN en config -> arranca el chat directo.
        Si NO hay token -> abre el navegador para autorizar (OAuth) y al
        recibir el callback recarga la config y arranca el chat.
        """
        def _start_chat_with_current_config():
            from src.core.config import load_config
            cfg = load_config()
            
            tok = cfg.get("TWITCH_TOKEN", "")
            nick = cfg.get("NICK", "")
            chan = cfg.get("CHANNEL", "")
            
            if not tok or not nick or not chan:
                self.log(f"❌ Faltan datos tras OAuth: TOKEN={'✓' if tok else '✗'} NICK={'✓' if nick else '✗'} CHANNEL={'✓' if chan else '✗'}")
                return
            sd, idev = self.get_devices()
            slots = []
            for i, pv, cv in getattr(self, '_audio_slots', []):
                p, c = pv.get(), cv.get()
                if p and c:
                    slots.append((p, c.strip().lower()))

            self.log(f"🔵 Iniciando bot: nick={nick}, canal={chan}, slots_audio={len(slots)}")
            start_chat(self, tok, nick, chan,
                       cfg.get("GROQ_API_KEY", ""), sd, idev, self,
                       ia_command=cfg.get("BOT_IA_COMMAND", "!IA"),
                       ia_voice=cfg.get("BOT_IA_VOICE", "es-MX-DaliaNeural"),
                       audio_slots=slots)
            self.after(0, lambda: (
                self.twitch_btn.configure(text="🟢  Conectado",
                                          fg_color=GRN, text_color=GRN_T),
            ))
        
        def _on_oauth_success(token, nick, channel):
            self.log(f"✅  OAuth OK — usuario: {nick}")
            try:
                from src.core.config import load_config
                fresh = load_config()
                config.update(fresh)
            except Exception as e:
                self.log(f"⚠  No se pudo recargar config: {e}")
            _start_chat_with_current_config()
        
        def _on_oauth_error(msg):
            self.log(f"❌  OAuth: {msg}")
            self.after(0, lambda: self.twitch_btn.configure(
                text="🔴  Twitch", fg_color="#9146FF", text_color="#fff"))
        
        def run():
            tok = config.get("TWITCH_TOKEN", "")
            if tok:
                self.log("🔍  Validando token de Twitch...")
                if not validate_token(tok):
                    self.log("⚠  Token expirado o inválido. Abriendo OAuth...")
                    self.after(0, lambda: self.twitch_btn.configure(
                        text="🟡  Autorizando...",
                        fg_color=AMB, text_color="#fff"))
                    from src.core.oauth_server import clear_token
                    clear_token()
                    tok = None
                else:
                    self.log("🔵  Conectando Twitch con token guardado...")
                    _start_chat_with_current_config()
                    return

            if TwitchOAuth is None:
                self.log("❌  oauth_server no disponible (revisa secrets_manager.py)")
                return
            self.log("🌐  Abriendo navegador para autorizar en Twitch...")
            self.after(0, lambda: self.twitch_btn.configure(
                text="🟡  Esperando autorización...",
                fg_color=AMB, text_color="#fff"))
            try:
                TwitchOAuth(on_success=_on_oauth_success,
                            on_error=_on_oauth_error).start()
            except Exception as e:
                self.log(f"❌  No se pudo iniciar OAuth: {e}")
                self.log(traceback.format_exc())
        
        threading.Thread(target=run, daemon=True).start()
    
    def _guardar_config_panel(self):
        from src.core.config import load_config, save_config
        cfg = load_config()
        
        if hasattr(self, 'mode_select'):
            cfg["SELECTED_PROMPT"] = self.mode_select.get()
        
        if hasattr(self, 'sp2'):
            idx = self.sp2.get()
            try:
                cfg["SPEAKER_DEVICE"] = str(self.dev_names.index(idx)) if idx in self.dev_names else "0"
            except Exception:
                cfg["SPEAKER_DEVICE"] = "0"
        if hasattr(self, 'ia2'):
            idx = self.ia2.get()
            try:
                cfg["IA_DEVICE"] = str(self.dev_names.index(idx) if idx in self.dev_names else 0)
            except Exception:
                cfg["IA_DEVICE"] = "0"
        if hasattr(self, 'mn2'):
            idx = self.mn2.get()
            if idx in ("(Ninguno)", ""):
                cfg.pop("MONITOR_DEVICE", None)
            else:
                try:
                    cfg["MONITOR_DEVICE"] = str(self.dev_names.index(idx) if idx in self.dev_names else 0)
                except Exception:
                    cfg["MONITOR_DEVICE"] = "0"
        
        if hasattr(self, 'ptt_key_entry'):
            ptt_key = self.ptt_key_entry.get().strip().upper()
            if not ptt_key:
                ptt_key = "F9"
            cfg["PTT_KEY"] = ptt_key
            config["PTT_KEY"] = ptt_key

        cfg["MOCAP_FACE_CAM"] = config.get("MOCAP_FACE_CAM", "0")
        cfg["MOCAP_FACE_CONF"] = config.get("MOCAP_FACE_CONF", "0.5")
        cfg["MOCAP_AUDIO_SENS"] = config.get("MOCAP_AUDIO_SENS", "0.3")

        for key, attr in [("IA_NOMBRE", "_ia_nombre"), ("IA_APELLIDO", "_ia_apellido"),
                          ("IA_EDAD", "_ia_edad"), ("IA_GENERO", "_ia_genero"),
                          ("IA_CUMPLE", "_ia_cumple"), ("IA_SIGNO", "_ia_signo"),
                          ("IA_ALTURA", "_ia_altura"), ("IA_TRABAJO", "_ia_trabajo"),
                          ("IA_GUSTOS", "_ia_gustos"), ("IA_FRASES", "_ia_frases"),
                          ("PLAYER_NOMBRE", "_player_nombre"), ("PLAYER_APELLIDO", "_player_apellido"),
                          ("PLAYER_EDAD", "_player_edad"), ("PLAYER_GENERO", "_player_genero"),
                          ("PLAYER_CUMPLE", "_player_cumple"), ("PLAYER_SIGNO", "_player_signo"),
                          ("PLAYER_ALTURA", "_player_altura"), ("PLAYER_TRABAJO", "_player_trabajo"),
                           ("PLAYER_GUSTOS", "_player_gustos"), ("PLAYER_FRASES", "_player_frases"),
                           ("PLAYER_RELACION", "_player_relacion")]:
            if hasattr(self, attr):
                cfg[key] = getattr(self, attr).get()
                config[key] = getattr(self, attr).get()
        
        save_config(cfg)
        self._build_prompt(self._selected_prompt_file)
        self.log(f"Configuracion guardada ({ptt_key if hasattr(self, 'ptt_key_entry') else 'F9'})")
    
    def _borrar_memoria(self):
        try:
            from src.ia.memory import clear_memory
            clear_memory()
            self.log("🗑  Memoria borrada correctamente")
        except Exception as e:
            self.log(f"❌  Error al borrar memoria: {e}")

    def _borrar_vector_memory(self):
        try:
            from src.ia.vector_memory import clear_vector_memory
            clear_vector_memory()
            self.log("🗑  Memoria vectorial borrada correctamente")
        except Exception as e:
            self.log(f"❌  Error: {e}")

    def _borrar_chat_learning(self):
        try:
            from src.ia.chat_learning import get_chat_learning
            get_chat_learning().clear()
            self.log("🗑  Datos de aprendizaje borrados correctamente")
        except Exception as e:
            self.log(f"❌  Error: {e}")

    def _mostrar_learning_stats(self):
        try:
            from src.ia.chat_learning import get_learning_stats, get_learning_summary
            from src.ia.vector_memory import memory_stats
            stats = get_learning_stats()
            total = stats["total_positive"] + stats["total_negative"]
            ratio = (stats["total_positive"] / max(total, 1)) * 100
            vstats = memory_stats()
            self.log(f"📊  Aprendizaje: {stats['total_positive']}👍 / {stats['total_negative']}👎 ({ratio:.0f}% positivo) de {total} reacciones")
            self.log(f"💾  Memoria vectorial: {vstats['count']} entradas (modo: {vstats['mode']})")
            self.log(f"📝  {get_learning_summary()}")
        except Exception as e:
            self.log(f"❌  Error al obtener estadísticas: {e}")
    
    def change_mode(self, filename):
        from src.core.config import load_config, save_config
        cfg = load_config()
        cfg["SELECTED_PROMPT"] = filename
        save_config(cfg)
        config["SELECTED_PROMPT"] = filename
        self._build_prompt(filename)
        self.log(f"Personalidad cambiada a: {filename}")

    def _build_prompt(self, filename=None):
        if filename is None:
            filename = self._selected_prompt_file

        def _seccion(attr_prefix, titulo):
            partes = []
            campos = [("Nom", f"_{attr_prefix}_nombre"), ("Ape", f"_{attr_prefix}_apellido"),
                      ("Edad", f"_{attr_prefix}_edad"), ("Gen", f"_{attr_prefix}_genero"),
                      ("Cumple", f"_{attr_prefix}_cumple"), ("Signo", f"_{attr_prefix}_signo"),
                      ("Alt", f"_{attr_prefix}_altura"), ("Trab", f"_{attr_prefix}_trabajo"),
                      ("Gustos", f"_{attr_prefix}_gustos"), ("Frase", f"_{attr_prefix}_frases")]
            if attr_prefix == "player":
                campos.append(("Rel", "_player_relacion"))
            for k, attr in campos:
                if hasattr(self, attr):
                    v = getattr(self, attr).get()
                    if v.strip():
                        partes.append(f"{k}:{v.strip()}")
            if partes:
                return f"[{titulo}] " + ", ".join(partes)
            return None

        secciones = [s for s in [_seccion("ia", "IA"), _seccion("player", "Player")] if s]
        try:
            with open(os.path.join(self.prompt_folder, filename), encoding="utf-8") as f:
                personalidad = f.read()
        except FileNotFoundError:
            personalidad = "Eres una VTuber divertida."
        if secciones:
            self.current_prompt = "\n".join(secciones) + f"\n[Yo]\n{personalidad}"
        else:
            self.current_prompt = personalidad
    
    def get_devices(self):
        if not hasattr(self, 'sp2') or not hasattr(self, 'ia2') or not hasattr(self, 'mn2'):
            return 2, 2
        sn = self.sp2.get()
        an = self.ia2.get()
        mn = self.mn2.get()
        sid = next((i for n, i in self.devices if n == sn), 2)
        iid = next((i for n, i in self.devices if n == an), 2)
        if mn in ("(Ninguno)", ""):
            return sid, iid
        mid = next((i for n, i in self.devices if n == mn), None)
        return sid, ([iid, mid] if mid and mid != iid else iid)
    
    def log(self, text):
        def _update():
            if hasattr(self, "log_box") and self.log_box.winfo_exists():
                self.log_box.insert("end", text + "\n")
                self.log_box.see("end")
            else:
                print(text)
        try:
            self.after(0, _update)
        except Exception:
            print(text)
    
    def _on_closing(self):
        self.log("Apagando Karin VTuber...")
        if self.obs_controller:
            self.obs_controller.disconnect()
        if self.translator_engine:
            self.translator_engine.stop()
        try:
            from src.audio import stop_audio
            stop_audio()
        except Exception as e:
            self.log(f"Error deteniendo audio: {e}")
        try:
            if self._plugin_manager:
                self._plugin_manager.unload_all()
        except Exception as e:
            self.log(f"Error descargando plugins: {e}")
        try:
            if hasattr(self, 'kste_engine'):
                self.kste_engine._on_closing()
        except Exception as e:
            self.log(f"Error cerrando KSTE: {e}")
        self.destroy()

    # ════════════════════════════════════════════════════════════════════════
    #  AYUDA
    # ════════════════════════════════════════════════════════════════════════
    def _tab_creditos(self, parent):
        return build_tab_creditos(parent, self)


# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print("\n========== ERROR AL INICIAR ==========")
        traceback.print_exc()
        print("======================================")
        input("\nPresiona ENTER para cerrar...")