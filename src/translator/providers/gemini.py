import requests, json, time
from .base import BaseProvider

class GeminiProvider(BaseProvider):
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.models = ["gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-2.5-flash"]

    def translate(self, text, source="auto", target="es"):
        if not self.api_key:
            return None
        prompt = (
            f"Translate the following text from {source} to {target}. "
            f"Respond with ONLY the translated text, nothing else.\n\n{text}"
        )
        for model in self.models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 200, "temperature": 0.1}
                }
                r = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=15)
                if r.status_code == 200:
                    resp = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    for ch in ["*", "#", "`", "_"]:
                        resp = resp.replace(ch, "")
                    return resp if resp else None
                if r.status_code in (400, 404):
                    continue
                if r.status_code == 429:
                    time.sleep(2)
                    continue
            except Exception:
                continue
        return None

    @property
    def name(self):
        return "Google Gemini"
