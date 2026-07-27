import time
import threading
from src.utils.log import info, warn, error
from src.kste.config.kste_config import KSTEConfig, load_kste_config, save_kste_config
from src.kste.capture.capture_manager import CaptureManager
from src.kste.ocr.ocr_manager import OCRManager
from src.kste.parser.message_parser import MessageParser, ChatChannel
from src.kste.translator.translator_factory import create as create_translator, available as available_translators
from src.kste.cache.translation_cache import TranslationCache
from src.kste.language.language_detector import LanguageDetector
from src.kste.profiles.player_profile import PlayerProfileManager
from src.kste.context.context_engine import ContextEngine
from src.kste.dictionary.game_dictionary import GameDictionary
from src.kste.filter.spam_filter import SpamFilter
from src.kste.memory.conversation_memory import ConversationMemory
from src.kste.overlay.kste_overlay import KSTEOverlay
from src.kste.sender.reply_system import ReplySystem
from src.kste.sender.quick_reply import QuickReplyManager


class KSTEEngine:
    def __init__(self, config=None):
        self.config = config or load_kste_config()

        self.capture = CaptureManager(self.config)
        self.ocr = OCRManager(self.config)
        self.parser = MessageParser()
        self.translator = create_translator(
            self.config.translator_name,
            self.config.translator_api_key
        )
        self.cache = TranslationCache(self.config)
        self.profiles = PlayerProfileManager()
        self.language_detector = LanguageDetector(self.profiles)
        self.dictionary = GameDictionary()
        self.context = ContextEngine(self.dictionary)
        self.spam_filter = SpamFilter(self.config)
        self.memory = ConversationMemory(self.config)
        self.overlay = KSTEOverlay(self.config)
        self.sender = ReplySystem(self.translator, self.config)
        self.quick_reply = QuickReplyManager()

        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._status = "stopped"
        self._stats = {"processed": 0, "translated": 0, "filtered": 0, "cached": 0}

    @property
    def status(self):
        return self._status

    @property
    def stats(self):
        return dict(self._stats)

    def start(self):
        if self._running:
            warn("KSTE already running")
            return
        if not self.capture.has_region():
            warn("KSTE: no capture region set")
            return
        self._running = True
        self._status = "running"
        self._thread = threading.Thread(target=self._loop, daemon=True, name="KSTE")
        self._thread.start()
        info("KSTE engine started")

    def stop(self):
        self._running = False
        self._status = "stopped"
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        info("KSTE engine stopped")

    def set_translator(self, name, api_key=""):
        try:
            self.translator = create_translator(name, api_key)
            self.sender.translator = self.translator
            self.config.translator_name = name
            self.config.translator_api_key = api_key
            save_kste_config(self.config)
            info(f"KSTE translator changed to: {name}")
        except Exception as e:
            warn(f"KSTE set_translator error: {e}")

    def set_capture_region(self, x, y, w, h):
        self.capture.set_region(x, y, w, h)

    def calibrate_capture(self):
        return self.capture.calibrate()

    def send_reply(self, text_es, target_player):
        return self.sender.send_reply(text_es, target_player, self.profiles)

    def search_history(self, query):
        return self.memory.search(query)

    def get_quick_replies(self, category):
        return self.quick_reply.get_replies(category)

    def get_quick_reply_text(self, category, index, target_lang="en"):
        return self.quick_reply.get_reply_text(category, index, target_lang)

    def toggle_overlay(self):
        self.overlay.toggle()

    def save_all(self):
        self.cache.save()
        self.profiles.save()
        save_kste_config(self.config)

    def _loop(self):
        info("KSTE loop started")
        while self._running:
            try:
                self._pipeline_step()
            except Exception as e:
                error(f"KSTE pipeline error: {e}")
            time.sleep(self.config.capture_interval)
        info("KSTE loop ended")

    def _pipeline_step(self):
        image = self.capture.capture()
        if image is None:
            return

        ocr_results = self.ocr.read(image)
        if not ocr_results:
            return

        messages = self.parser.parse(ocr_results)

        for msg in messages:
            if self.spam_filter.should_filter(msg):
                self._stats["filtered"] += 1
                continue

            self._stats["processed"] += 1

            msg.idioma = self.language_detector.detect(msg.texto, msg.jugador)

            profile = self.profiles.get_or_create(msg.jugador)
            msg = self.context.resolve(msg, profile)

            msg.texto, msg.protegido = self.dictionary.lookup(msg.texto, msg.idioma)

            cached = self.cache.get(msg.texto, msg.idioma, self.config.target_lang)
            if cached:
                msg.traduccion = cached
                self._stats["cached"] += 1
            elif msg.idioma != self.config.target_lang:
                try:
                    msg.traduccion = self.translator.translate(
                        msg.texto, source=msg.idioma, target=self.config.target_lang
                    )
                    self.cache.set(msg.texto, msg.idioma, self.config.target_lang, msg.traduccion)
                    self._stats["translated"] += 1
                except Exception as e:
                    warn(f"KSTE translate error: {e}")
                    msg.traduccion = msg.texto
            else:
                msg.traduccion = msg.texto

            self.profiles.update(
                msg.jugador,
                mensajes_totales=profile.mensajes_totales + 1
            )

            self.memory.save(msg, msg.traduccion)

            self.overlay.add_message(
                msg.jugador, msg.texto, msg.traduccion,
                msg.idioma, msg.canal.value
            )

    def _on_closing(self):
        self.stop()
        self.save_all()
        self.overlay.destroy()
        self.memory.cleanup()
        info("KSTE engine closed")
