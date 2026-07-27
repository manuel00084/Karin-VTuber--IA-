import requests
from .base import BaseProvider

class DeepLProvider(BaseProvider):
    FREE_URL = "https://api-free.deepl.com/v2/translate"
    PRO_URL = "https://api.deepl.com/v2/translate"

    def translate(self, text, source="auto", target="es"):
        if not self.api_key:
            return None
        url = self.PRO_URL if self.api_key.startswith("fx_") or self.api_key.startswith("dpl_") else self.FREE_URL
        try:
            params = {
                "auth_key": self.api_key,
                "text": text,
                "source_lang": source.upper() if source != "auto" else None,
                "target_lang": target.upper(),
            }
            if params["source_lang"] is None:
                del params["source_lang"]
            r = requests.post(url, data=params, timeout=15)
            if r.status_code == 200:
                return r.json()["translations"][0]["text"]
            return None
        except Exception:
            return None

    @property
    def name(self):
        return "DeepL"
