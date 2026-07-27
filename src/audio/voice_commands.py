"""Voice commands — wake word 'Karin' + voice control for the app."""
import threading, time, queue, re
import sounddevice as sd
import numpy as np
from src.utils.log import error, info


class VoiceCommandEngine:

    def __init__(self, app=None, on_command=None):
        self._running = False
        self._thread = None
        self._app = app
        self._on_command = on_command or self._default_handler
        self._vosk = None
        self._model = None
        self._recognizer = None
        self._audio_queue = queue.Queue()
        self._stream = None
        self._device = None
        self._enabled = False
        self._last_partial = ""
        self._wake_detected = False
        self._command_buffer = ""
        self._silence_frames = 0
        self._wake_words = self._load_wake_words()

    def _load_wake_words(self):
        from src.core.config import load_config
        cfg = load_config()
        ww = cfg.get("VOICE_WAKE_WORD", "").strip().lower()
        if not ww:
            return []
        base = ww
        variants = [base]
        return variants

    def set_app(self, app):
        self._app = app

    def set_device(self, device):
        self._device = device

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, val):
        self._enabled = val
        if val and not self._running:
            self.start()
        elif not val and self._running:
            self.stop()

    def start(self):
        if self._running:
            return
        self._try_load_vosk()
        if not self._vosk:
            self._log("❌  Vosk no disponible. Instala: pip install vosk")
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="voice-cmd")
        self._thread.start()
        self._log("🎤  Comandos de voz activados (decí 'Karin' + comando)")

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _try_load_vosk(self):
        try:
            import vosk
            self._vosk = vosk
            import os
            from src import PROJECT_ROOT
            model_path = os.path.join(PROJECT_ROOT, "vosk-model-small-es-0.42")
            if os.path.isdir(model_path):
                self._model = vosk.Model(model_path)
                self._recognizer = vosk.KaldiRecognizer(self._model, 16000)
                return True
            else:
                self._log(f"⚠  Modelo Vosk no encontrado en: {model_path}")
                return False
        except ImportError:
            return False

    def _log(self, msg):
        if self._app:
            try:
                self._app.log(msg)
            except Exception:
                pass
        else:
            info(msg)

    def _callback(self, indata, frames, time_info, status):
        if status:
            error(f"Voice cmd stream error: {status}")
        if self._running:
            self._audio_queue.put(bytes(indata))

    def _loop(self):
        try:
            self._stream = sd.RawInputStream(
                samplerate=16000, channels=1, dtype="int16",
                device=self._device, blocksize=8000,
                callback=self._callback,
            )
            self._stream.start()

            while self._running:
                try:
                    data = self._audio_queue.get(timeout=0.5)
                    if not self._recognizer:
                        continue
                    if self._recognizer.AcceptWaveform(data):
                        result = self._recognizer.Result()
                        self._process_result(result)
                    else:
                        partial = self._recognizer.PartialResult()
                        self._process_partial(partial)
                except queue.Empty:
                    continue
                except Exception as e:
                    error(f"Voice cmd error: {e}")
        except Exception as e:
            self._log(f"❌  Error en audio: {e}")
        finally:
            self._running = False

    def _process_partial(self, partial):
        try:
            import json
            text = json.loads(partial).get("partial", "").lower().strip()
            if not text:
                return
            self._last_partial = text

            # Detect wake word
            if not self._wake_words:
                return
            if not self._wake_detected:
                for ww in self._wake_words:
                    if re.search(r'\b' + re.escape(ww) + r'\b', text) and len(text) < 30:
                        self._wake_detected = True
                        self._command_buffer = ""
                        self._silence_frames = 0
                        if self._app:
                            try:
                                self._app.log(f"🎤  Te escucho...")
                            except Exception:
                                pass
                        break
        except Exception:
            pass

    def _process_result(self, result):
        if not self._wake_words:
            return
        try:
            import json
            data = json.loads(result)
            text = data.get("text", "").lower().strip()
            if not text:
                # Silence — check if we were listening for a command
                if self._wake_detected:
                    self._silence_frames += 1
                    if self._silence_frames > 3 and self._command_buffer:
                        self._execute_command(self._command_buffer)
                        self._reset()
                return

            if self._wake_detected:
                # Remove wake word from the text
                cmd_text = text
                for ww in self._wake_words:
                    cmd_text = cmd_text.replace(ww, "").strip()
                if cmd_text:
                    self._command_buffer = cmd_text
                    self._execute_command(cmd_text)
                    self._reset()
                else:
                    self._command_buffer = text
                    self._silence_frames = 0
        except Exception:
            pass

    def _execute_command(self, text):
        if not text:
            return
        self._log(f"🎤  Comando: {text}")
        if self._on_command:
            self._on_command(text)

    def _reset(self):
        self._wake_detected = False
        self._command_buffer = ""
        self._silence_frames = 0

    def reload_wake_word(self):
        self._wake_words = self._load_wake_words()
        if self._wake_words:
            self._log(f"🔊  Wake word cambiada a: {self._wake_words[0]}")
        else:
            self._log("🔊  Wake word desactivada (campo vacío)")

    def _default_handler(self, text):
        self._log(f"📢  (sin handler) '{text}'")


def build_command_handler(app):
    """Build a command handler that routes voice commands to app actions."""

    def handler(text):
        text = text.lower().strip()
        try:
            # OBS scene switch
            m = re.search(r"(?:cambia|pon|ve a|ir a)\s+escena\s+(.+)", text)
            if m:
                scene = m.group(1).strip()
                obs = getattr(app, "obs_controller", None)
                if obs and hasattr(obs, "switch_scene"):
                    obs.switch_scene(scene)
                    app.log(f"🎬  Escena cambiada a: {scene}")
                    _speak(app, f"Cambiando a escena {scene}")
                else:
                    _speak(app, "OBS no está conectado")
                return

            # OBS recording
            if re.search(r"(?:inicia|empieza|comienza)\s+(?:a\s+)?grabar", text) or \
               re.search(r"graba(?:ción)?\s*(?:on|ahora|ya)?", text):
                obs = getattr(app, "obs_controller", None)
                if obs and hasattr(obs, "toggle_recording"):
                    obs.toggle_recording()
                    _speak(app, "Grabación iniciada")
                return

            if re.search(r"(?:para|detén|frena)\s+(?:la\s+)?grabación", text) or \
               text in ("para grabar", "detener grabación"):
                obs = getattr(app, "obs_controller", None)
                if obs and hasattr(obs, "toggle_recording"):
                    obs.toggle_recording()
                    _speak(app, "Grabación detenida")
                return

            # Stream
            if re.search(r"(?:inicia|empieza|comienza)\s+(?:el\s+)?stream", text) or \
               "hacer stream" in text:
                obs = getattr(app, "obs_controller", None)
                if obs and hasattr(obs, "toggle_streaming"):
                    obs.toggle_streaming()
                    _speak(app, "Stream iniciado")
                return

            if re.search(r"(?:termina|detén|frena)\s+(?:el\s+)?stream", text) or \
               "terminar stream" in text:
                obs = getattr(app, "obs_controller", None)
                if obs and hasattr(obs, "toggle_streaming"):
                    obs.toggle_streaming()
                    _speak(app, "Stream terminado")
                return

            # Volume
            m = re.search(r"volumen\s+(?:a\s+)?(\d+)", text)
            if m:
                vol = min(100, max(0, int(m.group(1)))) / 100
                try:
                    from src.core.config import load_config, save_config
                    cfg = load_config()
                    cfg["VOLUME"] = str(vol)
                    save_config(cfg)
                except Exception:
                    pass
                _speak(app, f"Volumen a {int(vol*100)} porciento")
                return

            # Game launcher
            m = re.search(r"(?:abre|abrir|inicia|lanza)\s+(.+)", text)
            if m:
                game = m.group(1).strip()
                from src.utils.game_launcher import handle_command
                result = handle_command(f"abrir {game}")
                app.log(f"🎮  {result}")
                _speak(app, result)
                return

            m = re.search(r"(?:cierra|cerrar|mata)\s+(.+)", text)
            if m:
                game = m.group(1).strip()
                from src.utils.game_launcher import handle_command
                result = handle_command(f"cerrar {game}")
                app.log(f"🎮  {result}")
                _speak(app, result)
                return

            # Time
            if any(w in text for w in ("hora es", "hora actual", "qué hora")):
                from datetime import datetime
                now = datetime.now().strftime("%I:%M %p")
                _speak(app, f"Son las {now}")
                return

            # Mute
            if text in ("silencio", "mute", "silencio total"):
                from src.audio import stop_audio
                stop_audio()
                _speak(app, "Audio detenido")
                return

            # Unknown command
            _speak(app, f"No entendí el comando: {text}")
            app.log(f"🤔  Comando no reconocido: {text}")

        except Exception as e:
            app.log(f"❌  Error en comando de voz: {e}")

    return handler


def _speak(app, text):
    """Speak a response via TTS."""
    try:
        from src.audio import speak
        from src.core.config import load_config
        cfg = load_config()
        voice = cfg.get("VOICE_IA", "es-MX-DaliaNeural")
        _, dev = app.get_devices() if hasattr(app, "get_devices") else (None, None)
        speak(text, voice, dev, volume=1.0)
    except Exception:
        pass
