from .base import BaseProvider

class DummyProvider(BaseProvider):
    def __init__(self, api_key=None):
        super().__init__(api_key)

    def translate(self, text, source="auto", target="es"):
        return f"[{target}] {text}"

    @property
    def name(self):
        return "Dummy (debug)"

    @property
    def requires_key(self):
        return False
