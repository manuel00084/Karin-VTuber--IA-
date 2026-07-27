"""Chat translator — detect language, translate messages, respond in same language."""
import threading, re
from src.utils.log import error

_LANGDETECT_OK = False
try:
    from langdetect import detect
    _LANGDETECT_OK = True
except ImportError:
    pass

_PROVIDER_CACHE = {}

def _get_provider():
    name = "google_web"
    if name not in _PROVIDER_CACHE:
        try:
            from src.translator.providers import get_provider
            _PROVIDER_CACHE[name] = get_provider(name)
        except Exception:
            return None
    return _PROVIDER_CACHE[name]


def detect_language(text):
    """Detect language code from text. Returns None if uncertain."""
    if not text or len(text.strip()) < 3:
        return None
    if _LANGDETECT_OK:
        try:
            return detect(text)
        except Exception:
            pass
    return None


def translate(text, target="es", source="auto"):
    """Translate text to target language. Returns (translated, detected_source) or (None, None)."""
    if not text or not text.strip():
        return None, None
    provider = _get_provider()
    if not provider:
        return None, None
    try:
        result = provider.translate(text, source=source, target=target)
        if result and result.strip():
            return result.strip(), None
    except Exception:
        pass
    return None, None


def is_spanish(text):
    """Quick check if text is likely Spanish."""
    lang = detect_language(text)
    if lang:
        return lang == "es"
    return None


def auto_translate(text, target="es"):
    """Translate to target only if not already in that language. Returns (translated, lang_code) or None.

    Uses a two-step approach:
    1. Try langdetect if available
    2. If detection can't determine or returns non-target, translate and compare
    """
    if not text or len(text.strip()) < 2:
        return None
    text_stripped = text.strip()

    # Step 1: try language detection
    lang = detect_language(text_stripped)

    # Normalize close languages (pt, gl, ca → es for practical purposes)
    _CLOSE_TO_ES = {"pt", "gl", "ca"}
    if lang in _CLOSE_TO_ES and lang != target:
        lang = target

    if lang == target:
        return None, lang

    # Step 2: translate and compare
    translated, _ = translate(text_stripped, target=target)
    if translated:
        if translated.lower().strip() == text_stripped.lower().strip():
            return None, lang or target
        similarity = len(set(translated.lower()) & set(text_stripped.lower())) / max(len(set(translated.lower()) | set(text_stripped.lower())), 1)
        if similarity > 0.85 and abs(len(translated) - len(text_stripped)) < 5:
            return None, lang or target
        return translated, lang or "unknown"

    return None, lang


class UserLanguageCache:
    """Stores the detected language for each user to respond in kind."""

    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def set(self, user, lang):
        with self._lock:
            self._data[user.lower()] = lang

    def get(self, user):
        with self._lock:
            return self._data.get(user.lower())

    def remove(self, user):
        with self._lock:
            self._data.pop(user.lower(), None)


user_langs = UserLanguageCache()
