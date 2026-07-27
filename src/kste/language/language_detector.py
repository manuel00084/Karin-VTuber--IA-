import re
from src.utils.game_ocr_post import detectar_idioma


_KEYWORDS = {
    "es": {"hola", "gracias", "por favor", "ayuda", "vamos", "bien", "mal",
           "necesito", "quiero", "puedes", "dame", "aqui", "alli", "bueno",
           "malo", "grande", "pequeno", "rapido", "lento", "fuerte", "debil"},
    "en": {"hello", "thanks", "please", "help", "let's go", "good", "bad",
           "need", "want", "can you", "give me", "here", "there", "big",
           "small", "fast", "slow", "strong", "weak", "yes", "no"},
    "ja": {"こんにちは", "ありがとう", "お願い", "助けて", "行く", "良い", "悪い",
           "大きい", "小さい", "速い", "強い", "弱い"},
    "ko": {"안녕", "감사", "부탁", "도와", "가자", "좋", "나쁜",
           "크", "작", "빠른", "강한", "약한"},
    "pt": {"olá", "obrigado", "por favor", "ajuda", "vamos", "bom", "mau",
           "preciso", "quero", "pode", "aqui", "la", "grande", "pequeno"},
    "zh": {"你好", "谢谢", "请", "帮助", "走", "好", "坏",
           "大", "小", "快", "慢", "强", "弱"},
}


class LanguageDetector:
    def __init__(self, profile_manager):
        self._profiles = profile_manager
        self._langdetect = None
        try:
            from langdetect import detect as _detect
            self._langdetect = _detect
        except ImportError:
            pass

    def detect(self, text, player_name=None):
        if not text or len(text.strip()) < 2:
            return "unknown"
        if player_name:
            profile = self._profiles.get(player_name)
            if profile and profile.idioma_detectado != "unknown":
                return profile.idioma_detectado
        lang = self._detect_unicode(text)
        if lang != "unknown":
            return lang
        lang = self._detect_langdetect(text)
        if lang:
            return lang
        lang = self._detect_keywords(text)
        return lang

    def _detect_unicode(self, text):
        return detectar_idioma(text)

    def _detect_langdetect(self, text):
        if not self._langdetect:
            return None
        try:
            result = self._langdetect(text)
            if result and len(result) == 2:
                return result
        except Exception:
            pass
        return None

    def _detect_keywords(self, text):
        text_lower = text.lower()
        scores = {}
        for lang, words in _KEYWORDS.items():
            score = sum(1 for w in words if w in text_lower)
            if score > 0:
                scores[lang] = score
        if scores:
            return max(scores, key=scores.get)
        return "unknown"
