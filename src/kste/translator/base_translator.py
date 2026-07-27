from abc import ABC, abstractmethod


class ITranslator(ABC):
    @abstractmethod
    def translate(self, text, source="auto", target="es"):
        ...

    @property
    @abstractmethod
    def name(self):
        ...

    @property
    @abstractmethod
    def is_online(self):
        ...

    @property
    @abstractmethod
    def requires_key(self):
        ...

    def test(self):
        try:
            result = self.translate("hello", source="en", target="es")
            return bool(result and len(result) > 0)
        except Exception:
            return False
