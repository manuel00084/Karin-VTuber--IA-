from src.kste.translator.base_translator import ITranslator
import requests


class DeepLTranslator(ITranslator):
    _FREE = "https://api-free.deepl.com/v2/translate"
    _PRO = "https://api.deepl.com/v2/translate"

    def __init__(self, api_key=""):
        self.api_key = api_key or ""
        self._endpoint = self._FREE if self.api_key.startswith("fx") else self._PRO

    @property
    def name(self):
        return "deepl"

    @property
    def is_online(self):
        return True

    @property
    def requires_key(self):
        return True

    def translate(self, text, source="auto", target="es"):
        if not text or not text.strip():
            return ""
        if not self.api_key:
            raise ValueError("DeepL requires API key")
        deepl_target = target.upper() if target != "auto" else "ES"
        deepl_source = source.upper() if source != "auto" else None
        payload = {"text": [text], "target_lang": deepl_target}
        if deepl_source:
            payload["source_lang"] = deepl_source
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(self._endpoint, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("translations"):
            return data["translations"][0]["text"]
        return text

    def test(self):
        return bool(self.api_key)
