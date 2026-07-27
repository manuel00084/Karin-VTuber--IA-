from src.kste.translator.base_translator import ITranslator
import requests
import json
import time


class GoogleTranslator(ITranslator):
    _ENDPOINT = "https://translate.googleapis.com/translate_a/single"

    def __init__(self, api_key=""):
        self._last_request = 0

    @property
    def name(self):
        return "google"

    @property
    def is_online(self):
        return True

    @property
    def requires_key(self):
        return False

    def translate(self, text, source="auto", target="es"):
        if not text or not text.strip():
            return ""
        elapsed = time.time() - self._last_request
        if elapsed < 0.15:
            time.sleep(0.15 - elapsed)
        params = {
            "client": "gtx",
            "sl": source,
            "tl": target,
            "dt": "t",
            "q": text,
        }
        resp = requests.get(self._ENDPOINT, params=params, timeout=10)
        self._last_request = time.time()
        resp.raise_for_status()
        data = resp.json()
        if data and isinstance(data, list) and data[0]:
            return "".join(part[0] for part in data[0] if part[0])
        return text
