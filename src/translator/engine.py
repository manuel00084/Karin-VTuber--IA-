import threading, time, gc
import numpy as np
import cv2
from PIL import Image

from .providers import get_provider
from .memory import TranslationMemory
from .overlay import TranslationOverlay
from .preprocessor import ImagePreprocessor

class TranslationEngine:
    def __init__(self, log_fn=print):
        self.log = log_fn
        self._running = False
        self._thread = None

        self.ocr_engine = "rapidocr"
        self.translation_provider_name = "google_web"
        self.translation_api_key = ""
        self.source_lang = "auto"
        self.target_lang = "es"

        self.interval = 3.0
        self.region = None
        self._last_ocr_text = ""
        self._last_translation = ""
        self._last_hash = ""

        self.memory = TranslationMemory()
        self.overlay = TranslationOverlay()
        self.preprocessor = ImagePreprocessor()

        self.show_overlay = False
        self.speak_translation = False
        self.voice = "es-MX-DaliaNeural"
        self.tts_device = 2

        self._provider_instance = None

    def _get_provider(self):
        return get_provider(self.translation_provider_name, self.translation_api_key)

    def _do_ocr(self, img):
        try:
            from src.utils.game_ocr_lite import ocr_read_text
            preprocessed = self.preprocessor.process(np.array(img.convert("RGB")))
            if preprocessed is None:
                return ""
            preprocessed_bgr = cv2.cvtColor(preprocessed, cv2.COLOR_RGB2BGR)
            results = ocr_read_text(preprocessed_bgr, conf_min=0.3)
            texts = [r["text"] for r in results if len(r["text"].strip()) > 2]
            return " ".join(texts) if texts else ""
        except Exception as e:
            self.log(f" OCR error: {e}")
            return ""

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        if self.show_overlay:
            self.overlay.show()
        self.log(" Traductor iniciado")

    def stop(self):
        self._running = False
        self.overlay.destroy()
        self.log(" Traductor detenido")

    def _loop(self):
        while self._running:
            try:
                img = self._capture()
                if img is None:
                    time.sleep(0.5)
                    continue

                text = self._do_ocr(img)
                if text and text != self._last_ocr_text:
                    self.log(f" OCR: {text[:100]}")
                    self._last_ocr_text = text

                    cached = self.memory.get(text, self.source_lang, self.target_lang)
                    if cached:
                        translation = cached
                        self.log(f"  Traduccion (cache): {translation[:100]}")
                    else:
                        provider = self._get_provider()
                        translation = provider.translate(text, self.source_lang, self.target_lang)
                        if translation:
                            self.memory.set(text, self.source_lang, self.target_lang, translation)
                            self.log(f"  Traduccion: {translation[:100]}")

                    if translation:
                        self._last_translation = translation
                        if self.show_overlay:
                            self.overlay.update_text(f"{text}\n─\n{translation}")
                        if self.speak_translation:
                            self._speak(translation)

                time.sleep(self.interval)
                gc.collect()
            except Exception as e:
                self.log(f" Error en loop: {e}")
                time.sleep(1)

    def _capture(self):
        try:
            from src.utils.win_capture import capturar_pantalla
            return capturar_pantalla(region=self.region)
        except Exception as e:
            self.log(f" Error captura: {e}")
            return None

    def _speak(self, text):
        try:
            from src.audio import speak
            speak(text, self.voice, self.tts_device, volume=2.0)
        except Exception as e:
            self.log(f" Error TTS: {e}")

    def test_ocr(self):
        img = self._capture()
        if img is None:
            return "Sin captura"
        text = self._do_ocr(img)
        return text or "Sin texto detectado"

    def test_translation(self, text=None):
        if text is None:
            text = self._last_ocr_text or "Hello, this is a test"
        provider = self._get_provider()
        result = provider.translate(text, self.source_lang, self.target_lang)
        return result or "Error en traduccion"
