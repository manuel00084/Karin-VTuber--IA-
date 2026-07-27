import requests, re
from .base import BaseProvider

class GoogleWebProvider(BaseProvider):
    def __init__(self, api_key=None):
        super().__init__(api_key)

    def translate(self, text, source="auto", target="es"):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text,
            }
            r = requests.get(url, params=params, timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                parts = r.json()[0]
                result = "".join(p[0] for p in parts if p[0])
                return result if result else None
            return None
        except Exception:
            return None

    @property
    def name(self):
        return "Google Web (gratuito)"

    @property
    def requires_key(self):
        return False
