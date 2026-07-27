class BaseProvider:
    def __init__(self, api_key=None):
        self.api_key = api_key or ""

    def translate(self, text, source="auto", target="es"):
        raise NotImplementedError

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def requires_key(self):
        return True

    def test(self):
        try:
            self.translate("Hello", source="en", target="es")
            return True
        except Exception:
            return False
