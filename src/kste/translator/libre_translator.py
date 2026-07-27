from src.kste.translator.base_translator import ITranslator
from src.utils.log import warn
import requests


class LibreTranslator(ITranslator):
    def __init__(self, api_key=""):
        self._base_url = "http://localhost:5000"
        self._available = False
        self._check_connection()

    def _check_connection(self):
        try:
            resp = requests.get(f"{self._base_url}/languages", timeout=3)
            if resp.status_code == 200:
                self._available = True
        except Exception:
            pass

    @property
    def name(self):
        return "libre"

    @property
    def is_online(self):
        return self._available

    @property
    def requires_key(self):
        return False

    def translate(self, text, source="auto", target="es"):
        if not text or not text.strip():
            return ""
        if not self._available:
            raise RuntimeError("LibreTranslate server not reachable at " + self._base_url)
        payload = {
            "q": text,
            "source": source if source != "auto" else "auto",
            "target": target,
        }
        resp = requests.post(
            f"{self._base_url}/translate",
            json=payload,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("translatedText", text)

    def set_server(self, url):
        self._base_url = url.rstrip("/")
        self._available = False
        self._check_connection()

    def test(self):
        return self._available
